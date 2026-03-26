## ADDED Requirements

### Requirement: Six-step onboarding wizard flow
The application SHALL present a mandatory 6-step onboarding wizard on first launch, guiding the user through all required setup.

#### Scenario: First-time user sees onboarding
- **WHEN** a new user logs in for the first time (`onboarding_done === false`)
- **THEN** the application SHALL display the onboarding wizard starting at Step 1 (Welcome)
- **AND** the user SHALL NOT be able to access the main application until onboarding is complete

#### Scenario: Returning user skips onboarding
- **WHEN** a user with `onboarding_done === true` logs in
- **THEN** the application SHALL redirect directly to the Home page

### Requirement: Step 1 - Welcome page
The wizard SHALL display a welcome page introducing MultiYou.

#### Scenario: Welcome page display
- **WHEN** the onboarding wizard starts
- **THEN** the system SHALL display a welcome message with product introduction and core value proposition
- **AND** a "Next" button to proceed to Step 2

### Requirement: Step 2 - Account registration
The wizard SHALL allow the user to create an account.

#### Scenario: Account creation in wizard
- **WHEN** the user fills in username, password, and password confirmation on Step 2
- **AND** clicks "Next"
- **THEN** the system SHALL call `POST /api/auth/register` to create the account
- **AND** automatically log in the user
- **AND** proceed to Step 3

#### Scenario: Password mismatch
- **WHEN** the password and confirmation do not match
- **THEN** the system SHALL show a validation error and NOT proceed

### Requirement: Step 3 - Model configuration
The wizard SHALL allow the user to configure an AI model provider.

#### Scenario: DeepSeek default configuration
- **WHEN** Step 3 is displayed
- **THEN** the system SHALL pre-select DeepSeek as the default provider
- **AND** pre-fill the endpoint as `https://api.deepseek.com`
- **AND** prompt the user to enter an API Key

#### Scenario: Model connectivity test
- **WHEN** the user clicks the "Test" button after entering API Key
- **THEN** the system SHALL call `POST /api/models/{id}/test`
- **AND** display success/failure with latency information

#### Scenario: Skip model config with local Ollama
- **WHEN** the user selects Ollama as provider
- **THEN** the system SHALL NOT require an API Key
- **AND** SHALL pre-fill endpoint as `http://localhost:11434`

### Requirement: Step 4 - Photo upload and cropping
The wizard SHALL allow the user to upload a photo and manually crop the face region.

#### Scenario: Photo upload and crop
- **WHEN** the user uploads a JPG/PNG image
- **THEN** the system SHALL display the image in a vue-cropper component with 1:1 aspect ratio
- **AND** the user SHALL manually position the crop box over the face area
- **AND** a pixel-art preview SHALL be shown alongside the cropper

#### Scenario: Re-upload photo
- **WHEN** the user clicks "Re-upload"
- **THEN** the system SHALL clear the current image and allow a new upload

### Requirement: Step 5 - Persona configuration
The wizard SHALL allow the user to configure the avatar's persona.

#### Scenario: Persona setup
- **WHEN** Step 5 is displayed
- **THEN** the user SHALL enter an avatar name and a System Prompt describing the persona
- **AND** the system SHALL provide placeholder text as guidance

### Requirement: Step 6 - Completion and submission
The wizard SHALL show a summary and submit all configurations in one request.

#### Scenario: Summary and one-click submit
- **WHEN** Step 6 is displayed
- **THEN** the system SHALL display a summary of all configured items (account, model, avatar preview, persona)
- **AND** a "Complete" button SHALL submit everything via `POST /api/onboarding/setup`
- **AND** upon success, set `onboarding_done = true` for the user
- **AND** redirect to the Home page

### Requirement: Onboarding setup API
The backend SHALL provide an endpoint to process all onboarding data in a single request.

#### Scenario: Successful onboarding submission
- **WHEN** a POST request is sent to `/api/onboarding/setup` with model config, photo file, crop data, persona info, and avatar name
- **THEN** the system SHALL create the model config (with API Key stored in keyring)
- **AND** create the persona record
- **AND** process the image (crop + pixelate) and save the avatar
- **AND** create the avatar record linking persona and model
- **AND** set the user's `onboarding_done` to `true`
- **AND** return the created avatar ID
