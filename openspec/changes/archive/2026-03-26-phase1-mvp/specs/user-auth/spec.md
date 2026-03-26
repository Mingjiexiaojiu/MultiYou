## ADDED Requirements

### Requirement: User registration
The system SHALL allow new users to register with a username and password.

#### Scenario: Successful registration
- **WHEN** a POST request is sent to `/api/auth/register` with `{"username": "alice", "password": "secure123"}`
- **THEN** the system SHALL create a new user record with the username
- **AND** the password SHALL be hashed with bcrypt (passlib) before storage
- **AND** the response SHALL include the created user ID

#### Scenario: Duplicate username registration
- **WHEN** a POST request is sent to `/api/auth/register` with a username that already exists
- **THEN** the system SHALL return HTTP 409 with an error message

#### Scenario: Empty or invalid credentials
- **WHEN** a POST request is sent with empty username or password
- **THEN** the system SHALL return HTTP 422 with validation error details

### Requirement: User login
The system SHALL authenticate users and return a JWT token.

#### Scenario: Successful login
- **WHEN** a POST request is sent to `/api/auth/login` with valid credentials
- **THEN** the system SHALL return a JWT token with 24-hour expiry
- **AND** the response SHALL include `user_id`, `token`, and `onboarding_done` status

#### Scenario: Invalid credentials
- **WHEN** a POST request is sent with incorrect username or password
- **THEN** the system SHALL return HTTP 401

### Requirement: JWT authentication middleware
All API endpoints (except `/api/auth/register`, `/api/auth/login`, `/health`) SHALL require a valid JWT token.

#### Scenario: Valid token access
- **WHEN** a request includes a valid `Authorization: Bearer <token>` header
- **THEN** the request SHALL be processed normally with the authenticated user context

#### Scenario: Missing or invalid token
- **WHEN** a request to a protected endpoint has no token or an expired/invalid token
- **THEN** the system SHALL return HTTP 401

### Requirement: Frontend route guards
The Vue Router SHALL enforce authentication and onboarding completion.

#### Scenario: Unauthenticated access redirects to login
- **WHEN** a user without a token navigates to any protected route
- **THEN** the router SHALL redirect to `/login`

#### Scenario: Onboarding not complete redirects to wizard
- **WHEN** a logged-in user with `onboardingDone === false` navigates to any route other than `/onboarding`
- **THEN** the router SHALL redirect to `/onboarding`
