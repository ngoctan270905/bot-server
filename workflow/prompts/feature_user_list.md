# Feature Prompt: User Account Listing API (Offset Pagination)

## 1. Feature Name
List User Accounts

## 2. User Story
As an administrator, I want to retrieve a list of all user accounts, including their essential details like avatar, fullname, email, phone number, role, is_active status, and creation date, using page-based pagination so that I can effectively manage user access and information.

## 3. API Endpoint
- **Method:** `GET`
- **Path:** `/api/v1/users`
- **Description:** Retrieves a paginated list of user accounts using offset-based pagination.

## 4. Request Parameters
- **Query Parameters (Optional):**
    - `page`: Integer, default 1, min 1. The page number for pagination.
    - `page_size`: Integer, default 10, min 1, max 100. The number of items per page.
    - `search`: String, optional. A keyword to search by user fullname or email.
    - `role`: String, optional. Filter users by a specific role (e.g., "admin", "user").
    - `is_active`: Boolean, optional. Filter users by active status (True or False).

## 5. Response Schema
### `UserListResponse`
This schema defines the structure for the API response when listing user accounts using offset pagination.

```json
{
  "total_count": 100,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": "60d0fe4f5311236168a109ca",
      "avatar_url": "https://example.com/avatars/user1.jpg",
      "fullname": "John Doe",
      "email": "john.doe@example.com",
      "phone_number": "+84912345678",
      "role": "user",
      "is_active": true,
      "created_at": "2023-01-15T10:00:00Z"
    },
    {
      "id": "60d0fe4f5311236168a109cb",
      "avatar_url": "https://example.com/avatars/admin1.jpg",
      "fullname": "Jane Smith",
      "email": "jane.smith@example.com",
      "phone_number": "+84987654321",
      "role": "admin",
      "is_active": true,
      "created_at": "2022-11-20T14:30:00Z"
    }
  ]
}
```

### `UserListItem` Object
This object represents a single user's details within the `items` array of `UserListResponse`.

- `id`: String, required. Unique identifier for the user.
- `avatar_url`: String, optional. URL to the user's avatar image.
- `fullname`: String, required. Full name of the user.
- `email`: String, required. User's email address.
- `phone_number`: String, optional. User's phone number.
- `role`: String, required. The role assigned to the user (e.g., "admin", "user", "editor").
- `is_active`: Boolean, required. Current active status of the user account.
- `created_at`: String (ISO 8601 format), required. Timestamp when the user account was created.

## 6. Business Logic/Validation
- Only authenticated users with "admin" or appropriate "manager" roles should be able to access this endpoint.
- Offset-based pagination should be implemented.
- Search functionality should allow filtering by `fullname` and `email`.
- Role and `is_active` filters should be exact matches.

## 7. Error Handling
- `401 Unauthorized`: If the user is not authenticated.
- `403 Forbidden`: If the authenticated user does not have the necessary permissions.
- `400 Bad Request`: For invalid query parameters (e.g., `page` or `page_size` are not positive integers).
- `500 Internal Server Error`: For unexpected server issues.

## 8. Dependencies
- User repository for fetching user data.
- Authentication and authorization middleware.
- Pydantic models for request/response validation.

## 9. Potential Future Enhancements
- Sorting options (e.g., sort by `created_at`, `fullname`).
- More advanced filtering capabilities.
- Export functionality (e.g., CSV, Excel).