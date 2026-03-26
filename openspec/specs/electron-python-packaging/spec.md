## ADDED Requirements

### Requirement: Backend process lifecycle management
The Electron main process SHALL spawn a FastAPI Python subprocess on application startup and manage its entire lifecycle (start, health check, shutdown).

#### Scenario: Successful backend startup in development
- **WHEN** the Electron app starts in development mode (`app.isPackaged === false`)
- **THEN** the BackendManager SHALL spawn the system/venv Python to run `uvicorn main:app --port 8000`
- **AND** poll `GET /health` every 500ms for up to 20 attempts
- **AND** load the BrowserWindow only after receiving a 200 response

#### Scenario: Successful backend startup in production
- **WHEN** the Electron app starts in packaged mode (`app.isPackaged === true`)
- **THEN** the BackendManager SHALL use the embedded Python at `resources/python-backend/python-embed/python.exe`
- **AND** set the working directory to `resources/python-backend/backend/`
- **AND** follow the same health check polling flow

#### Scenario: Backend fails to start
- **WHEN** the health check polling exhausts all 20 attempts without a 200 response
- **THEN** the application SHALL display an error dialog to the user
- **AND** the application SHALL exit gracefully

#### Scenario: Application quit cleans up backend
- **WHEN** the user closes the application (Electron `before-quit` event)
- **THEN** the BackendManager SHALL call `process.kill()` on the Python subprocess
- **AND** the Python process SHALL NOT remain as a zombie holding port 8000

### Requirement: Health check endpoint
The FastAPI backend SHALL expose a `GET /health` endpoint at the root level (not under `/api/`).

#### Scenario: Health check returns OK
- **WHEN** a GET request is sent to `/health`
- **THEN** the response status code SHALL be 200
- **AND** the response body SHALL be `{"status": "ok"}`

### Requirement: Electron-builder packaging configuration
The project SHALL use electron-builder with `extraResources` to bundle the Python backend and embedded Python runtime.

#### Scenario: Windows NSIS build includes Python backend
- **WHEN** the project is built for Windows using electron-builder
- **THEN** the `python-backend/` directory SHALL be copied to `resources/python-backend/` in the output
- **AND** `__pycache__/` directories SHALL be excluded from the bundle

### Requirement: Development/production path switching
The BackendManager SHALL use `app.isPackaged` to determine Python executable and backend code paths.

#### Scenario: Development mode paths
- **WHEN** `app.isPackaged` is `false`
- **THEN** the Python path SHALL resolve to the system `python` command
- **AND** the backend path SHALL resolve to the local `backend/main.py`

#### Scenario: Production mode paths
- **WHEN** `app.isPackaged` is `true`
- **THEN** the Python path SHALL resolve to `process.resourcesPath/python-backend/python-embed/python.exe`
- **AND** the backend path SHALL resolve to `process.resourcesPath/python-backend/backend/main.py`
