## ADDED Requirements

### Requirement: Send message and receive reply
The system SHALL allow users to send a message in a session and receive an AI-generated reply.

#### Scenario: Successful chat exchange
- **WHEN** a POST request is sent to `/api/chat` with `session_id` and `message`
- **THEN** the system SHALL look up the session's avatar, persona, and model configuration
- **AND** load the last 20 messages from chat_log for context
- **AND** build the messages array: [system prompt, history, user message]
- **AND** call the OpenAICompatProvider with the constructed messages
- **AND** save both the user message and assistant reply to chat_log
- **AND** update the session's `updated_at` timestamp
- **AND** return the reply text and session_id

#### Scenario: Session not found
- **WHEN** the session_id does not exist or belongs to another user's avatar
- **THEN** the system SHALL return HTTP 404

### Requirement: Create new session
The system SHALL allow users to create a new conversation session for an avatar.

#### Scenario: Successful session creation
- **WHEN** a POST request is sent to `/api/sessions` with `avatar_id`
- **THEN** the system SHALL create a session record with title "新对话" and current timestamp
- **AND** return the session id, title, and start_time

### Requirement: List sessions for avatar
The system SHALL allow users to list all conversation sessions for a specific avatar.

#### Scenario: Get session list
- **WHEN** a GET request is sent to `/api/avatars/{id}/sessions`
- **THEN** the system SHALL return all sessions for that avatar, ordered by `updated_at` descending
- **AND** each session SHALL include id, title, and updated_at

### Requirement: Update session title
The system SHALL allow users to update a session's title.

#### Scenario: Rename session
- **WHEN** a PUT request is sent to `/api/sessions/{id}` with a new title
- **THEN** the system SHALL update the session's title field

### Requirement: Retrieve session chat history
The system SHALL allow users to retrieve all messages in a session.

#### Scenario: Get chat logs
- **WHEN** a GET request is sent to `/api/sessions/{id}/logs`
- **THEN** the system SHALL return all chat_log entries for that session, ordered by timestamp ascending
- **AND** each entry SHALL include role, content, and timestamp

### Requirement: Context window sliding
The chat service SHALL use a sliding window of the most recent 20 messages for LLM context.

#### Scenario: History exceeds window size
- **WHEN** a session has more than 20 messages in chat_log
- **THEN** the system SHALL include only the last 20 messages (excluding the system prompt) when building the LLM request
- **AND** the system prompt SHALL always be included as the first message

### Requirement: Chat page with session sidebar
The frontend chat page SHALL display a session list sidebar alongside the conversation.

#### Scenario: Session sidebar display
- **WHEN** the user navigates to `/chat/:avatarId`
- **THEN** the page SHALL show a sidebar listing all sessions for the avatar
- **AND** a "+ New Session" button at the top of the sidebar
- **AND** the currently active session SHALL be visually highlighted

#### Scenario: Switch between sessions
- **WHEN** the user clicks a different session in the sidebar
- **THEN** the chat area SHALL load and display that session's message history

#### Scenario: Create new session from chat page
- **WHEN** the user clicks "+ New Session"
- **THEN** the system SHALL call `POST /api/sessions` to create a new session
- **AND** automatically switch to the newly created session
