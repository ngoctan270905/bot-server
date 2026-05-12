# Feature Prompt: Update User Information API (Admin)

## 1. Feature Name
Update User Information (Admin)

## 2. User Story
As an administrator, I want to update the details of a specific user, including their full name, email, phone number, and avatar, so that I can maintain accurate user records and manage their profiles effectively.

## 3. API Endpoint
- **Method:** `PUT`
- **Path:** `/api/v1/users/{user_id}`
- **Description:** Updates the information of a specific user by their ID.

## 4. Request Parameters
- **Path Parameters:**
    - `user_id`: String, required. The unique identifier of the user to be updated.
- **Form Data (multipart/form-data):**
    - `fullname`: String, optional. New full name of the user (min_length=3, max_length=50).
    - `email`: String, optional. New email address of the user.
    - `phone_number`: String, optional. New phone number of the user (min_length=10, max_length=15).
    - `avatar_file`: File (UploadFile), optional. New avatar image file for the user. If provided, the existing avatar will be replaced.

## 5. Request Body Example
```http
PUT /api/v1/users/60d0fe4f5311236168a109ca
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="fullname"

New Fullname
--boundary
Content-Disposition: form-data; name="email"

new.email@example.com
--boundary
Content-Disposition: form-data; name="phone_number"

+84123456789
--boundary
Content-Disposition: form-data; name="avatar_file"; filename="new_avatar.png"
Content-Type: image/png

<binary content of new_avatar.png>
--boundary--
```

## 6. Response Schema
### `UserUpdateResponse`
This schema defines the structure for the API response after a user's information has been successfully updated.

```json
{
  "success": true,
  "message": "Cập nhật thông tin người dùng thành công",
  "data": {
    "id": "60d0fe4f5311236168a109ca",
    "fullname": "New Fullname",
    "email": "new.email@example.com",
    "phone_number": "+84123456789",
    "is_active": true,
    "role": "user",
    "avatar_url": "https://example.com/static/uploads/new_avatar_id.png"
  }
}
```

### `UserUpdateResponse.data` Object
This object represents the updated user's details.

- `id`: String, required. Unique identifier for the updated user.
- `fullname`: String, required. Updated full name of the user.
- `email`: String, required. Updated email address of the user.
- `phone_number`: String, optional. Updated phone number of the user.
- `is_active`: Boolean, required. Current active status of the user account.
- `role`: String, required. The role assigned to the user (e.g., "admin", "user", "editor").
- `avatar_url`: String, optional. URL to the updated user's avatar image.

## 7. Business Logic/Validation
- Only authenticated users with "admin" role should be able to access this endpoint.
- The `user_id` in the path must correspond to an existing user.
- Email format validation should be applied.
- Phone number should only contain digits.
- If `avatar_file` is provided, it should be a valid image file. The old avatar file should be removed from storage, and the new one saved. The `avatar_url` in the database should be updated to reflect the new file's path.
- If `email` is updated, ensure it's unique (unless it's the user's current email).

## 8. Error Handling
- `401 Unauthorized`: If the user is not authenticated.
- `403 Forbidden`: If the authenticated user does not have "admin" permissions.
- `404 Not Found`: If the `user_id` does not correspond to an existing user.
- `400 Bad Request`: For invalid input data (e.g., invalid email format, phone number, or file type).
- `409 Conflict`: If the new email address already exists for another user.
- `500 Internal Server Error`: For unexpected server issues (e.g., file upload failure, database error).

## 9. Dependencies
- User repository for fetching and updating user data.
- File storage service for handling avatar uploads and deletions.
- Authentication and authorization middleware (specifically `get_admin_user`).
- Pydantic models (`UserUpdate`, `UserUpdateResponse`) for request/response validation.