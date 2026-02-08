// Runtime config injected by docker-entrypoint.sh (Cloud Run / Docker)
// Falls back to Vite build-time env vars for local dev
const runtime = (window as unknown as Record<string, unknown>).__RUNTIME_CONFIG__ as
  | Record<string, string>
  | undefined;

const apiUrl = runtime?.VITE_API_URL || import.meta.env.VITE_API_URL || '';
const wsDefault = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;

export const config = {
  apiUrl,
  wsUrl: runtime?.VITE_WS_URL || import.meta.env.VITE_WS_URL || (apiUrl ? apiUrl.replace(/^http/, 'ws') : wsDefault),
  recaptchaSiteKey: runtime?.VITE_RECAPTCHA_SITE_KEY || import.meta.env.VITE_RECAPTCHA_SITE_KEY || '',
};
