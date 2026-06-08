# BOM Builder Workspace

This workspace now contains a separated Python backend and a Node-based frontend.

## Structure

- `backend/` — Python REST API for parsing BOM Excel files
- `frontend/` — Node/Vite web UI for uploading and previewing files
- `import tkinter as tk.py` — legacy Tkinter application still present for reference

## Getting started

### Backend

1. Open a terminal in `backend/`
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
3. Activate it:
   ```bash
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the backend:
   ```bash
   python app.py
   ```

The backend listens on `http://localhost:5000`.

### Frontend

1. Open a terminal in `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```

The frontend will open in your browser and send uploads to `http://localhost:5000/api/parse`.

## Notes


## Credentials and local development (.env)

When running the backend locally you must provide Business Central credentials. For development you can place them in a `.env` file at the repository root (do NOT commit this file).

Example `.env` (DO NOT COMMIT):

```
BC_CLIENT_ID=21e698d9-1eab-42be-beb7-76096e1af3db
BC_CLIENT_SECRET=waJ8Q~KQ5XQV0k7WFzXGyMmAjEy9XW_w6OhGWcdR
BC_TENANT_ID=697d6604-5c29-4ca0-9dea-9db421a85492
```

The backend and some example scripts use `python-dotenv` (optional) to load `.env` into the process environment during development. To enable this locally:

1. Install the package in your backend virtualenv:

```bash
pip install python-dotenv
```

2. Keep a template in source control instead of secrets, e.g. create `.env.example` with the same keys but empty values, and add `.env` to `.gitignore`:

```
# .gitignore
.env
```

Setting environment variables manually:
- PowerShell (session):
   ```powershell
   $env:BC_CLIENT_ID = "<value>"
   $env:BC_CLIENT_SECRET = "<value>"
   $env:BC_TENANT_ID = "<value>"
   ```
- WSL / bash (session):
   ```bash
   export BC_CLIENT_ID="<value>"
   export BC_CLIENT_SECRET="<value>"
   export BC_TENANT_ID="<value>"
   ```

After setting the variables (or creating `.env`), restart the backend. The app will read the values from the process environment and use them to request an OAuth token from Azure AD. If any required variable is missing the backend will fail fast with a clear error message.

For production deployments, do not use `.env`. Use a managed secret store (Azure Key Vault, Kubernetes secrets, Docker secrets, or your cloud provider's secret manager) or a platform mechanism for environment variables.
