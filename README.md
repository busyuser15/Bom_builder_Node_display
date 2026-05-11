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

- The current backend is a starting scaffold and parses `.xlsx` / `.xlsm` BOM sheets.
- The old Tkinter script remains in the workspace for reference while the new Node UI is built.
