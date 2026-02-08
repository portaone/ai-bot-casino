gcloud run deploy aibotcasino-api `
    --image=europe-west1-docker.pkg.dev/portaone-ai/aibotcasino/backend:latest `
    --region=europe-west1 `
    --env-vars-file="C:\prog\agent-casino\tools\backend-env.yaml" `
    --set-secrets="AUTH_JWT_SECRET=aibotcasino-jwt-secret:latest,EMAIL_MAILERSEND_API_KEY=aibotcasino-mailersend-api-key:latest" `
    --quiet
