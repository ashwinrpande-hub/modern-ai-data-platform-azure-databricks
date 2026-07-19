# acme Data Marketplace (stretch) — independent module
Frontend: static SPA (no build step) -> Azure Static Web Apps (free tier)
Backend: FastAPI -> Azure Container Apps / App Service (free tier) — proxies Databricks
Vector Search for AI metadata search and UC information_schema for the catalog.
Deploy: `az staticwebapp create ...` for frontend; `az containerapp up --source backend/` for API.

