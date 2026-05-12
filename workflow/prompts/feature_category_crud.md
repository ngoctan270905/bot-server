# Feature: Category CRUD Operations

This document outlines the prompts for implementing CRUD operations for categories, with a focus on repository returning raw dicts and service handling Pydantic model conversion.

## Category Schema (app/schemas/category.py)

### Prompt for `CategoryBase`
```
Create a Pydantic `CategoryBase` model with the following fields and validations:
- `name`: string, required, min_length=3, max_length=100
- `slug`: string, optional, max_length=120. If not provided, it should be generated from `name`.
- `description`: string, optional, max_length=500
- `image_url`: string (http url), optional. Should validate as a URL if present.
- `parent_id`: str, optional. Should be a valid ObjectId string.
- `level`: int, default=1, greater_than_or_equal_to=1.
- `sort_order`: int, default=0, greater_than_or_equal_to=0.
- `is_active`: bool, default=True
```

### Prompt for `CategoryCreate`
```
Create a Pydantic `CategoryCreate` model that inherits from `CategoryBase`.
The `slug` field should remain optional.
```

### Prompt for `CategoryUpdate`
```
Create a Pydantic `CategoryUpdate` model that inherits from `CategoryBase`. All fields should be optional to allow partial updates.
```

### Prompt for `CategoryResponse`
```
Create a Pydantic `CategoryResponse` model that inherits from `CategoryBase`.
It should include the following additional fields:
- `id`: str (alias for `_id`), required. Should be a valid ObjectId string.
- `created_at`: datetime, required.
- `updated_at`: datetime, required.
Configure it to allow population by field name.
```

### Prompt for `CategoryListResponse`
```
Create a Pydantic `CategoryListResponse` model that represents a list of `CategoryResponse` objects.
```

## Category Repository (app/repositories/category_repository.py)

### Prompt for `CategoryRepository` Class
```
Create a `CategoryRepository` class with methods for interacting with a MongoDB collection named 'categories'.
It should handle conversion of ObjectId to str for output.
It should have the following asynchronous methods, receiving and returning `dict` objects:
- `create_category(category_data: dict) -> dict`: Inserts a new category document and returns the created category dictionary with `_id` converted to `str`.
- `get_category_by_id(category_id: str) -> Optional[dict]`: Retrieves a single category by its ObjectId string and returns its dictionary representation with `_id` converted to `str`.
- `get_all_categories(skip: int = 0, limit: int = 100) -> List[dict]`: Retrieves a list of all category dictionaries with pagination, converting `_id` to `str` for each.
- `update_category(category_id: str, update_data: dict) -> Optional[dict]`: Updates an existing category by ID with provided data and returns the updated category dictionary with `_id` converted to `str`.
- `delete_category(category_id: str) -> bool`: Deletes a category by ID and returns True if successful, False otherwise.
- `get_category_by_slug(slug: str) -> Optional[dict]`: Retrieves a single category by its slug and returns its dictionary representation with `_id` converted to `str`.
- `is_slug_taken(slug: str, exclude_id: Optional[str] = None) -> bool`: Checks if a slug is already taken, optionally excluding a specific category ID.
- `get_children_categories(parent_id: str) -> List[dict]`: Retrieves all children category dictionaries for a given parent ID, converting `_id` to `str` for each.
```

## Category Service (app/services/category_service.py)

### Prompt for `CategoryService` Class
```
Create an asynchronous `CategoryService` class that uses `CategoryRepository` for database interactions.
It should handle conversion between Pydantic models (CategoryCreate, CategoryUpdate, CategoryResponse) and raw dictionaries for the repository.
It should include the following methods:
- `create_category(category_data: CategoryCreate, image_file: Optional[UploadFile]) -> CategoryResponse`:
    - Generates a unique slug if not provided.
    - Handles image upload (if `image_file` is provided) to a storage service (e.g., local disk, cloud storage) and sets `image_url`.
    - Calculates the `level` based on `parent_id`.
    - Converts `category_data` to a dictionary and calls the repository to save the category.
    - Converts the returned dictionary from the repository to `CategoryResponse` and returns it.
- `get_category_by_id(category_id: str) -> CategoryResponse`: Retrieves a category by ID. Raises `HTTPException` if not found. Converts the returned dictionary from the repository to `CategoryResponse`.
- `get_all_categories(skip: int = 0, limit: int = 100) -> List[CategoryResponse]`: Retrieves all categories. Converts each returned dictionary from the repository to `CategoryResponse`.
- `update_category(category_id: str, update_data: CategoryUpdate, image_file: Optional[UploadFile]) -> CategoryResponse`:
    - Retrieves the existing category using the repository.
    - If `name` or `slug` is updated, ensure slug remains unique.
    - Handles image upload/replacement if `image_file` is provided.
    - Updates `image_url` and other fields in the existing category dictionary.
    - Recalculates `level` if `parent_id` changes.
    - Converts the `update_data` Pydantic model to a dictionary, merges it with the existing data, and calls the repository to update.
    - Converts the returned dictionary from the repository to `CategoryResponse` and returns it. Raises `HTTPException` if not found.
- `delete_category(category_id: str) -> bool`: Deletes a category. Raises `HTTPException` if not found or if it has children categories.
```

## Dependencies (app/api/v1/dependencies.py)

### Prompt for `get_category_service`
```
Add an asynchronous dependency function `get_category_service` that provides an instance of `CategoryService` with its required `CategoryRepository` injected.
```

## Endpoints/Router (app/api/v1/endpoints/categories.py)

### Prompt for `APIRouter` for Categories
```
Create a new `APIRouter` instance for category endpoints.
Implement the following asynchronous endpoints using `CategoryService` and appropriate Pydantic models for request/response:

1.  **POST /categories**
    -   **Request:** Accept individual `Form` parameters for `name`, `slug` (optional), `description` (optional), `parent_id` (optional), `level` (optional), `sort_order` (optional), `is_active` (optional). Also accept `image: UploadFile` (optional).
    -   **Logic:**
        -   Construct a `CategoryCreate` Pydantic model from the received form data.
        -   Pass the `CategoryCreate` model and `image` (UploadFile) to `CategoryService.create_category`.
    -   **Response:** `CategoryResponse`
    -   **Description:** Create a new category.

2.  **GET /categories**
    -   **Query Parameters:** `skip: int = 0`, `limit: int = 100`
    -   **Response:** `CategoryListResponse`
    -   **Description:** Get a list of all categories.

3.  **GET /categories/{category_id}**
    -   **Path Parameter:** `category_id: str`
    -   **Response:** `CategoryResponse`
    -   **Description:** Get a single category by ID.

4.  **PUT /categories/{category_id}**
    -   **Path Parameter:** `category_id: str`
    -   **Request:** Accept individual `Form` parameters for `name` (optional), `slug` (optional), `description` (optional), `parent_id` (optional), `level` (optional), `sort_order` (optional), `is_active` (optional). Also accept `image: UploadFile` (optional).
    -   **Logic:**
        -   Construct a `CategoryUpdate` Pydantic model from the received form data.
        -   Pass the `category_id`, `CategoryUpdate` model, and `image` (UploadFile) to `CategoryService.update_category`.
    -   **Response:** `CategoryResponse`
    -   **Description:** Update an existing category by ID.

5.  **DELETE /categories/{category_id}**
    -   **Path Parameter:** `category_id: str`
    -   **Response:** `dict` (e.g., `{"message": "Category deleted successfully"}`)
    -   **Description:** Delete a category by ID.
