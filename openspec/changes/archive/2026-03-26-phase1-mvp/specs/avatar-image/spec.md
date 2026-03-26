## ADDED Requirements

### Requirement: Frontend manual image cropping
The system SHALL provide a vue-cropper component for users to manually select the face region of an uploaded photo.

#### Scenario: Upload and crop photo
- **WHEN** the user selects a JPG or PNG image file
- **THEN** the system SHALL display the image in a vue-cropper@next component
- **AND** the cropper SHALL enforce a 1:1 (square) aspect ratio
- **AND** the cropper SHALL limit the crop box to within the image boundaries (viewMode: 1)
- **AND** the default crop area SHALL cover 60% of the image

#### Scenario: Export cropped image
- **WHEN** the user confirms the crop selection
- **THEN** the system SHALL export the cropped region as a 512x512 PNG blob
- **AND** send the blob to the backend for pixelation

#### Scenario: File type validation
- **WHEN** the user attempts to upload a non-JPG/PNG file
- **THEN** the system SHALL reject the upload with a validation message

#### Scenario: File size validation
- **WHEN** the user attempts to upload a file larger than 5MB
- **THEN** the system SHALL reject the upload with a size limit message

### Requirement: Backend Pillow pixelation
The backend SHALL pixelate a cropped square image to produce a pixel-art style avatar.

#### Scenario: Successful pixelation
- **WHEN** the backend receives a cropped image (bytes)
- **THEN** the system SHALL resize the image to 512x512 using LANCZOS
- **AND** downscale to 32x32 using NEAREST interpolation
- **AND** upscale to 128x128 using NEAREST interpolation
- **AND** save the result as a PNG file in `assets/avatar/`
- **AND** return the file path

### Requirement: Original image cleanup
The system SHALL delete the user's original uploaded photo after pixelation is complete.

#### Scenario: Original deleted after processing
- **WHEN** the pixelated avatar has been successfully saved
- **THEN** the system SHALL delete the temporary original upload file
- **AND** only the pixelated result SHALL persist on disk
