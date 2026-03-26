## ADDED Requirements

### Requirement: Create avatar
The system SHALL allow users to create an avatar by associating a persona, model configuration, and pixelated image.

#### Scenario: Successful avatar creation
- **WHEN** a POST request is sent to `/api/avatars` with a photo file, avatar name, persona_id, and model_id
- **THEN** the system SHALL process the photo through the image pipeline (crop → pixelate)
- **AND** create an avatar record linking the user, persona, model, and generated image path
- **AND** return the created avatar with its details

### Requirement: List user avatars
The system SHALL allow users to retrieve all their avatars.

#### Scenario: Get all avatars for current user
- **WHEN** a GET request is sent to `/api/avatars`
- **THEN** the system SHALL return all avatar records belonging to the authenticated user
- **AND** each avatar SHALL include name, image_path, persona info, and model info

### Requirement: Get avatar details
The system SHALL allow users to retrieve detailed information for a specific avatar.

#### Scenario: Get single avatar
- **WHEN** a GET request is sent to `/api/avatars/{id}`
- **THEN** the system SHALL return the avatar's full details including associated persona and model

#### Scenario: Avatar not found or unauthorized
- **WHEN** the avatar ID does not exist or belongs to another user
- **THEN** the system SHALL return HTTP 404

### Requirement: Persona CRUD
The system SHALL provide endpoints to create and list persona templates.

#### Scenario: Create persona
- **WHEN** a POST request is sent to `/api/personas` with name, system_prompt, and optional description
- **THEN** the system SHALL create a persona record associated with the authenticated user

#### Scenario: List personas
- **WHEN** a GET request is sent to `/api/personas`
- **THEN** the system SHALL return all persona records belonging to the authenticated user
