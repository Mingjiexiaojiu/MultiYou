## ADDED Requirements

### Requirement: OpenAI-compatible unified model provider
The system SHALL provide a single `OpenAICompatProvider` class that calls any model supporting the `/v1/chat/completions` endpoint.

#### Scenario: Call DeepSeek cloud model
- **WHEN** the provider is initialized with a DeepSeek model config (endpoint: `https://api.deepseek.com`, model_id: `deepseek-chat`, is_local: false)
- **THEN** the provider SHALL retrieve the API Key from keyring
- **AND** send a POST request to `https://api.deepseek.com/v1/chat/completions` with Bearer auth header
- **AND** return the assistant message content from the response

#### Scenario: Call Ollama local model
- **WHEN** the provider is initialized with an Ollama model config (endpoint: `http://localhost:11434`, model_id: `llama3`, is_local: true)
- **THEN** the provider SHALL NOT include an Authorization header
- **AND** send a POST request to `http://localhost:11434/v1/chat/completions`
- **AND** return the assistant message content from the response

#### Scenario: Model API timeout
- **WHEN** the LLM API does not respond within 60 seconds
- **THEN** the provider SHALL raise a timeout error

### Requirement: Model configuration CRUD
The system SHALL provide REST endpoints to manage model configurations.

#### Scenario: List all models
- **WHEN** a GET request is sent to `/api/models`
- **THEN** the system SHALL return all configured model records

#### Scenario: Create model configuration
- **WHEN** a POST request is sent to `/api/models` with name, model_id, provider, endpoint, and optionally api_key and is_local
- **THEN** the system SHALL create a model record
- **AND** if api_key is provided, store it in keyring and save the reference key in the database

#### Scenario: Update model configuration
- **WHEN** a PUT request is sent to `/api/models/{id}` with updated fields
- **THEN** the system SHALL update the corresponding model record
- **AND** if api_key is changed, update the keyring entry

#### Scenario: Delete model configuration
- **WHEN** a DELETE request is sent to `/api/models/{id}`
- **THEN** the system SHALL delete the model record
- **AND** remove the corresponding keyring entry if one exists

### Requirement: Model connectivity test
The system SHALL provide an endpoint to test whether a model configuration is reachable.

#### Scenario: Successful connectivity test
- **WHEN** a POST request is sent to `/api/models/{id}/test`
- **THEN** the system SHALL send a minimal chat completion request to the configured endpoint
- **AND** return `{"success": true, "message": "模型响应正常", "latency_ms": <ms>}`

#### Scenario: Failed connectivity test
- **WHEN** the model endpoint is unreachable or returns an error
- **THEN** the system SHALL return `{"success": false, "message": "<error details>"}`

### Requirement: API Key secure storage via keyring
The system SHALL store cloud model API Keys using the OS-level keyring (Windows Credential Manager).

#### Scenario: Store API Key
- **WHEN** a model with api_key is created or updated
- **THEN** the system SHALL call `keyring.set_password("multiyou", "apikey_{provider}", api_key)`
- **AND** the database model record SHALL store only the reference identifier, NOT the plaintext key

#### Scenario: Retrieve API Key
- **WHEN** the OpenAICompatProvider initializes with a cloud model
- **THEN** the system SHALL call `keyring.get_password("multiyou", reference_key)` to retrieve the actual key

### Requirement: Default model seed data
The system SHALL insert a default DeepSeek model configuration on first database initialization.

#### Scenario: First startup seeds default model
- **WHEN** the database is created for the first time
- **THEN** the system SHALL insert a model record: name="DeepSeek V3", model_id="deepseek-chat", provider="deepseek", endpoint="https://api.deepseek.com", is_local=0
