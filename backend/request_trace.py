import logging
import uuid
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from settings import settings
from core.rqid_in_logs import set_request_id
from core.exceptions import CasinoError


def extract_request_id(request: Request):
    """Extract request ID from request headers"""
    for id in [
        request.headers.get('X-Request-ID', None),
        request.headers.get('X-Cloud-Trace-Context', None),
    ]:
        if id is not None:
            return id
    return 'ABC-' + str(uuid.uuid4())[:8]


def format_app_traceback(exc: Exception) -> str:
    """Format traceback filtering out framework internal frames."""
    tb_lines = []
    tb = exc.__traceback__

    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        if any(path in filename for path in ['core', 'routers', 'modules', 'backend']):
            if 'site-packages' not in filename:
                lineno = tb.tb_lineno
                name = frame.f_code.co_name
                tb_lines.append(f'  File "{filename}", line {lineno}, in {name}')
        tb = tb.tb_next

    if tb_lines:
        return "Application traceback:\n" + "\n".join(tb_lines)
    return ""


def log_formatted_json(label: str, text):
    if len(text) == 0:
        logging.info(f"{label}: Empty")
        return
    logging.info(f"{label}: {text}")


def log_info(req_body, res_body):
    log_formatted_json("Request body", req_body)
    log_formatted_json("Reply body", res_body)


def log_with_label(label: str, data):
    log_formatted_json(label, data)


class RouteWithLogging(APIRoute):
    """Custom route class that logs request and response bodies"""
    HEADER_LIST = [element.strip().lower() for element in settings.log_headers]
    LOG_ALL_HEADERS = settings.log_headers_full
    SENSITIVE_HEADERS = ['authorization', 'x-api-key']
    FULLY_LOG_SENSITIVE_HEADERS = settings.log_headers_sensitive

    def add_headers_to_log(self, request: Request):
        def obfuscate_string(s: str) -> str:
            if s is None or len(s) <= 13:
                return s
            return s[:10] + '***' + s[-3:]

        headers = []
        for header in (request.headers.keys() if self.LOG_ALL_HEADERS else self.HEADER_LIST):
            value = request.headers.get(header)
            if header in self.SENSITIVE_HEADERS and not self.FULLY_LOG_SENSITIVE_HEADERS:
                value = obfuscate_string(value)
            headers.append(f"{header}: '{value}'")
        return "Headers: " + ", ".join(headers)

    def get_ip(self, request: Request):
        client_ip = None
        gcp_ip = request.headers.get("x-forwarded-for")
        if gcp_ip:
            client_ip = gcp_ip.split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host
        return client_ip

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request_id = extract_request_id(request)
            set_request_id(request_id)

            req_body = await request.body()
            content_type = request.headers.get('content-type', '').lower()
            if 'multipart/form-data' in content_type or 'application/octet-stream' in content_type:
                req_body = "<binary data>"
            else:
                try:
                    req_body = req_body.decode("utf-8").replace("\n", " ")
                except UnicodeDecodeError:
                    req_body = "<binary data>"

            if len(req_body) == 0:
                req_body = "<empty>"
            log_with_label(
                f"{request.method} request to {request.url.path} " +
                self.add_headers_to_log(request) +
                f" client IP: {self.get_ip(request)}",
                f"body: {req_body}"
            )
            try:
                response = await original_route_handler(request)
            except RequestValidationError as validation_exc:
                err_response = JSONResponse(
                    status_code=422,
                    content={"error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Input data validation error",
                        "details": {"errors": validation_exc.errors(), "path": request.url.path}
                    }}
                )
                logging.error(f"Validation exception {validation_exc.errors()}")
                return err_response
            except HTTPException as http_exc:
                _STATUS_TO_CODE = {
                    400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN",
                    404: "NOT_FOUND", 409: "CONFLICT", 422: "VALIDATION_ERROR",
                    429: "RATE_LIMIT_EXCEEDED", 502: "BAD_GATEWAY",
                }
                detail = http_exc.detail if hasattr(http_exc, 'detail') else "Unknown error"
                if isinstance(detail, dict) and "code" in detail:
                    code = detail["code"]
                    message = detail.get("message", str(detail))
                    details = detail.get("details", {})
                else:
                    code = _STATUS_TO_CODE.get(http_exc.status_code, "SERVER_ERROR")
                    message = str(detail)
                    details = {}
                err_response = JSONResponse(
                    status_code=http_exc.status_code,
                    content={"error": {"code": code, "message": message, "details": details}}
                )
                logging.error(f"HTTP exception {http_exc.status_code} {http_exc.detail}")
                err_response.background = BackgroundTask(
                    log_with_label,
                    "Reply", err_response.body.decode("utf-8").replace("\n", " ")
                )
                return err_response
            except CasinoError as casino_exc:
                logging.error(f"Casino error: {casino_exc.code} - {casino_exc.message}")
                status_map = {
                    "BETTING_CLOSED": 400,
                    "INSUFFICIENT_BALANCE": 400,
                    "TABLE_FULL": 400,
                    "BOT_NOT_SEATED": 400,
                    "RATE_LIMIT_EXCEEDED": 429,
                    "REFILL_COOLDOWN": 429,
                }
                status_code = status_map.get(casino_exc.code, 400)
                return JSONResponse(status_code=status_code, content=casino_exc.to_dict())
            except Exception as e:
                app_tb = format_app_traceback(e)
                if app_tb:
                    logging.error(f"Application error: {e}\n{app_tb}")
                else:
                    logging.error(f"Application error: {e}")
                details = {"trace": format_app_traceback(e)} if settings.debug else {}
                return JSONResponse(
                    status_code=500,
                    content={"error": {"code": "INTERNAL_ERROR", "message": str(e), "details": details}}
                )

            if isinstance(response, StreamingResponse):
                res_body = b""
                async for item in response.body_iterator:
                    res_body += item
                task = BackgroundTask(log_info, req_body, b"<streaming content>")
                return Response(
                    content=res_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                    background=task,
                )
            else:
                res_body = response.body
                response.background = BackgroundTask(
                    log_with_label,
                    "Reply", res_body.decode("utf-8").replace("\n", " ")
                )
                return response

        return custom_route_handler
