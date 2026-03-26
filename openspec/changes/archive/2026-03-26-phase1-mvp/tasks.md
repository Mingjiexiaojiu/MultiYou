## 1. Packaging Prototype Validation (Highest Risk)

- [x] 1.1 Create Electron project skeleton with `main.js` entry point
- [x] 1.2 Download and configure Windows embedded Python (`python-3.x-embed-amd64.zip`)
- [x] 1.3 Create `setup-python-embed.ps1` script to automate embedded Python setup and pip bootstrapping
- [x] 1.4 Create minimal FastAPI app with `/health` endpoint
- [x] 1.5 Implement `BackendManager` class: spawn Python subprocess, health check polling (500ms × 20), process kill
- [x] 1.6 Wire `BackendManager` into Electron lifecycle: `app.whenReady()` → start backend → wait for health → load BrowserWindow; `before-quit` → kill backend
- [x] 1.7 Implement `app.isPackaged` dev/prod path switching for Python executable and backend code paths
- [x] 1.8 Configure `electron-builder` with `extraResources` for `python-backend/` directory
- [ ] 1.9 Build Windows NSIS installer and verify embedded Python backend starts correctly
- [ ] 1.10 Verify `keyring` library works within embedded Python environment

## 2. Backend Project Skeleton

- [x] 2.1 Initialize Python backend project with FastAPI, uvicorn, and `requirements.txt`
- [x] 2.2 Set up SQLAlchemy (sync mode) with SQLite engine and `SessionLocal` factory
- [x] 2.3 Define all SQLAlchemy ORM models: User, Persona, Model, Avatar, Session, ChatLog
- [x] 2.4 Create Pydantic request/response schemas for all endpoints
- [x] 2.5 Implement database initialization and `seed.py` with default DeepSeek V3 model config
- [x] 2.6 Set up FastAPI app with CORS middleware, router registration, and `/health` endpoint

## 3. User Authentication

- [x] 3.1 Implement `POST /api/auth/register` with bcrypt password hashing (passlib)
- [x] 3.2 Implement `POST /api/auth/login` returning JWT token with 24h expiry (python-jose)
- [x] 3.3 Implement JWT authentication dependency (`get_current_user`) for protected routes
- [x] 3.4 Return `onboarding_done` status in login response

## 4. Model Configuration & Key Storage

- [x] 4.1 Implement `key_service.py`: `store_api_key()` and `get_api_key()` using keyring
- [x] 4.2 Implement `GET /api/models` — list all configured models
- [x] 4.3 Implement `POST /api/models` — create model config, store API Key in keyring if provided
- [x] 4.4 Implement `PUT /api/models/{id}` — update model config, update keyring entry if API Key changed
- [x] 4.5 Implement `DELETE /api/models/{id}` — delete model config and corresponding keyring entry
- [x] 4.6 Implement `POST /api/models/{id}/test` — send minimal chat completion to test connectivity, return success/latency

## 5. Unified Model Provider

- [x] 5.1 Implement `OpenAICompatProvider` class: init from model config, retrieve API Key from keyring for cloud models
- [x] 5.2 Implement `call()` method: POST to `{endpoint}/v1/chat/completions` with httpx, 60s timeout
- [x] 5.3 Handle auth header (Bearer token for cloud, none for local Ollama)
- [x] 5.4 Handle error responses and timeout exceptions

## 6. Image Processing

- [x] 6.1 Implement `image_service.py`: `pixelate_avatar(image_bytes, output_path)` — resize to 512×512, downscale to 32×32 NEAREST, upscale to 128×128 NEAREST
- [x] 6.2 Implement temp file handling: save upload to temp, process, delete original after pixelation
- [x] 6.3 Validate file type (JPG/PNG only) and file size (≤5MB) in upload endpoint

## 7. Avatar & Persona Management

- [x] 7.1 Implement `POST /api/personas` — create persona with name, system_prompt, description
- [x] 7.2 Implement `GET /api/personas` — list user's personas
- [x] 7.3 Implement `POST /api/avatars` — create avatar (multipart: file + name + persona_id + model_id), run image pipeline
- [x] 7.4 Implement `GET /api/avatars` — list user's avatars with persona and model details
- [x] 7.5 Implement `GET /api/avatars/{id}` — get single avatar details, 404 if not found or unauthorized

## 8. Chat & Session System

- [x] 8.1 Implement `POST /api/sessions` — create new session for avatar with default title "新对话"
- [x] 8.2 Implement `GET /api/avatars/{id}/sessions` — list sessions ordered by `updated_at` desc
- [x] 8.3 Implement `PUT /api/sessions/{id}` — update session title
- [x] 8.4 Implement `GET /api/sessions/{id}/logs` — get chat history ordered by timestamp asc
- [x] 8.5 Implement `build_messages()` — construct messages array with system prompt + sliding window (last 20 messages) + user message
- [x] 8.6 Implement `POST /api/chat` — receive session_id + message, call OpenAICompatProvider, save user + assistant messages, update session.updated_at

## 9. Onboarding API

- [x] 9.1 Implement `POST /api/onboarding/setup` — accept multipart form data with all onboarding fields
- [x] 9.2 In setup handler: create model config (with keyring), create persona, process image, create avatar
- [x] 9.3 Set user's `onboarding_done = true` on successful completion
- [x] 9.4 Return created avatar_id in response

## 10. Frontend Project Skeleton

- [x] 10.1 Initialize Vue 3 + Vite project in `frontend/vue-app/`
- [x] 10.2 Install and configure Pinia with `pinia-plugin-persistedstate` for localStorage persistence
- [x] 10.3 Install and configure Vue Router
- [x] 10.4 Install axios and create API client with base URL `http://localhost:8000` and Bearer token interceptor
- [x] 10.5 Create `useAuthStore` (Pinia): token, userId, onboardingDone, login/logout actions
- [x] 10.6 Create `useAvatarStore` (Pinia): avatars, currentAvatar, sessions, currentSession, fetch actions
- [x] 10.7 Configure router guards: redirect to `/login` if unauthenticated, redirect to `/onboarding` if `onboardingDone === false`

## 11. Frontend Login & Registration Pages

- [x] 11.1 Create `Login.vue` — username/password form, call login API, store token in AuthStore, redirect to home
- [x] 11.2 Create `Register.vue` — username/password/confirm form, call register API, auto-login on success

## 12. Frontend Onboarding Wizard

- [x] 12.1 Create onboarding layout with step indicator (● ● ○ ○ ○ ○) and navigation (prev/next)
- [x] 12.2 Create `Welcome.vue` (Step 1) — product introduction and "Get Started" button
- [x] 12.3 Create `AccountSetup.vue` (Step 2) — register form with password confirmation, call register API
- [x] 12.4 Create `ModelConfig.vue` (Step 3) — provider dropdown (DeepSeek default), API Key input, test button
- [x] 12.5 Install `vue-cropper@next` and create `ImageCropper.vue` component — 1:1 aspect, viewMode 1, export 512×512 PNG
- [x] 12.6 Create `PhotoUpload.vue` (Step 4) — file upload + ImageCropper + pixel preview side-by-side
- [x] 12.7 Create `PersonaSetup.vue` (Step 5) — avatar name input, System Prompt textarea with placeholder
- [x] 12.8 Create `Complete.vue` (Step 6) — summary display, "Complete" button calling `/api/onboarding/setup`

## 13. Frontend Main Pages

- [x] 13.1 Create `Home.vue` — display avatar cards grid, "+ Create Avatar" button, click card navigates to chat
- [x] 13.2 Create `CreateAvatar.vue` — photo upload with ImageCropper, persona selector, model selector, submit form
- [x] 13.3 Create `SessionList.vue` component — session list sidebar with "+ New Session" button, active session highlight
- [x] 13.4 Create `ChatMessage.vue` component — user/assistant message bubble with pixel avatar display
- [x] 13.5 Create `Chat.vue` — session sidebar + chat area + message input, load history on session switch, send message via POST /api/chat

## 14. Integration Testing & Bug Fixes

- [ ] 14.1 Test full onboarding flow: launch → wizard → model config → photo crop → persona → avatar creation
- [ ] 14.2 Test chat flow: create session → send message → receive reply → switch sessions → new session
- [ ] 14.3 Test model switching: configure Ollama alongside DeepSeek, verify both work
- [ ] 14.4 Test auth flow: register → login → token refresh → route guards
- [ ] 14.5 Test process lifecycle: app start → backend starts → app close → backend killed (no zombie)
- [ ] 14.6 Fix any bugs found during integration testing

## 15. Windows Packaging & Final Verification

- [ ] 15.1 Run `electron-builder` to produce Windows NSIS installer
- [ ] 15.2 Install on a clean Windows machine (or VM) and verify full flow works
- [ ] 15.3 Verify embedded Python + all dependencies load correctly in packaged app
- [ ] 15.4 Verify keyring works in packaged environment (API Key storage/retrieval)
- [ ] 15.5 Verify no Python zombie processes after app close
