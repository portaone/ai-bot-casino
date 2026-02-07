#!/bin/sh
# Runtime configuration injection for containerized React app
# This allows environment variables to be set at container runtime
# instead of build time, making the image more portable

# Inject runtime environment variables into config.js
cat > /usr/share/nginx/html/config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_URL: "${VITE_API_URL:-}",
  VITE_WS_URL: "${VITE_WS_URL:-}",
  VITE_RECAPTCHA_SITE_KEY: "${VITE_RECAPTCHA_SITE_KEY:-}"
};
EOF

echo "Runtime configuration injected:"
cat /usr/share/nginx/html/config.js

# Execute the CMD (nginx)
exec "$@"
