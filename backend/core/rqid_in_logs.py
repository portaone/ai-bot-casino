import os
import logging
import contextvars
from typing import Optional

# Add context variable for request ID
current_request_id = contextvars.ContextVar('current_request_id', default="STARTUP")


class AddRequestID(logging.Filter):
    """Logging filter that adds request_id to log records"""
    def filter(self, record):
        record.request_id = get_request_id()
        return True


def setup_logging(debug: bool = False):
    """Configure logging with request ID support"""
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Reduce noise from third-party libraries
    logging.getLogger("google.auth").setLevel(logging.INFO)
    logging.getLogger("google.cloud").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Create log format based on environment
    log_format = ""
    if not os.environ.get("PORT"):
        # Add timestamps when running locally
        log_format += "[%(asctime)s] "
    log_format += "%(levelname)s [Req-ID: %(request_id)s]: %(message)s"

    # Configure handler with formatter and filter
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(AddRequestID())

    # Get root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)

    root_logger.addHandler(handler)


def set_request_id(request_id: Optional[str]):
    """Set the current request ID in context"""
    if request_id:
        current_request_id.set(request_id)


def get_request_id() -> str:
    """Get the current request ID from context"""
    return current_request_id.get()


def clear_request_id():
    """Clear the current request ID from context"""
    current_request_id.set("STARTUP")


def log_formatted_json(label: str, text):
    """Take JSON (as byte-string) and pretty-print it to the log"""
    if len(text) == 0:
        logging.info(f"{label}: Empty")
        return
    logging.info(f"{label}: {text}")
    return


debug = True if os.getenv("DEBUG", "False").lower() == "true" else False

# Initialize logging when module is imported
setup_logging(debug)
