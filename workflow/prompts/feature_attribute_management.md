### Mục Tiêu

Triển khai các API endpoint cho phép quản lý thuộc tính sản phẩm (`Attribute`). Bao gồm các chức năng: lấy danh sách tất cả thuộc tính, tạo thuộc tính mới và cập nhật thuộc tính hiện có.

### Cấu Trúc MongoDB cho `Attribute`

```json
{
  "_id": ObjectId,
  "name": "Color",
  "code": "color",
  "type": "color", // Các loại được hỗ trợ: "color", "button", "radio", "select_box", "text", "number"
  "isVariantAttribute": true,
  "isFilterable": true,
  "values": [ // Array of sub-documents
    {
      "value": "Đen",
      "colorCode": "#000000" // 'colorCode' chỉ xuất hiện nếu 'type' là "color"
    }
  ],
  "createdAt": Date,
  "updatedAt": Date
}
```

### Yêu Cầu Chi Tiết

**1. Các Endpoint API (Controller/Router)**

*   **GET `/admin/attributes`**
    *   **Mô tả:** Lấy danh sách tất cả các thuộc tính sản phẩm.
    *   **Response:** `AttributeListAll` schema.
*   **POST `/admin/attributes`**
    *   **Mô tả:** Tạo một thuộc tính sản phẩm mới.
    *   **Request Body:** `AttributeCreate` schema.
    *   **Response:** `AttributeCreateResponse` schema (chi tiết thuộc tính vừa tạo).
*   **PUT `/admin/attributes/{attribute_id}`**
    *   **Mô tả:** Cập nhật thông tin của một thuộc tính sản phẩm theo `attribute_id`.
    *   **Request Body:** `AttributeUpdate` schema.
    *   **Response:** `AttributeUpdateResponse` schema (chi tiết thuộc tính đã cập nhật).

**2. Schema (Pydantic v2)**

Tạo các Pydantic schema sau, tuân thủ chặt chẽ tất cả các `schema_rules.md` (đặc biệt về Pydantic v2, đặt tên, `Field` với `description`, `min_length`/`max_length`, `field_validator`, `PyObjectId` cho `_id` và `model_config`):

*   `AttributeValue`: Schema cho các phần tử trong mảng `values`.
    *   `value: str` (bắt buộc, có validate độ dài)
    *   `colorCode: str | None` (tùy chọn, chỉ khi `type` là 'color', có regex pattern cho hex color)
*   `AttributeCreate`: Schema cho dữ liệu tạo thuộc tính mới.
    *   `name: str` (bắt buộc, validate độ dài và không được rỗng)
    *   `code: str` (bắt buộc, validate độ dài, không được rỗng và regex pattern chỉ cho phép chữ thường, số, gạch dưới)
    *   `type: Literal["color", "button", "radio", "select_box", "text", "number"]` (bắt buộc)
    *   `isVariantAttribute: bool` (mặc định False)
    *   `isFilterable: bool` (mặc định False)
    *   `values: list[AttributeValue]` (mặc định rỗng)
*   `AttributeCreateResponse`: Schema trả về sau khi tạo thuộc tính thành công (bao gồm `id`, `createdAt`, `updatedAt`).
*   `AttributeUpdate`: Schema cho dữ liệu cập nhật thuộc tính. Tất cả các trường đều là tùy chọn (`Optional`) và có thể là `None`.
*   `AttributeUpdateResponse`: Schema trả về sau khi cập nhật thuộc tính thành công.
*   `AttributeListAll`: Schema cho danh sách các thuộc tính (chứa một list các `AttributeCreateResponse` hoặc `AttributeDetailResponse`).

**Ví dụ Dữ Liệu cho Schema:**

```python
# AttributeValue
example_attribute_value = {
    "value": "Đen",
    "colorCode": "#000000"
}

# AttributeCreate Request Body
example_attribute_create_request = {
    "name": "Color",
    "code": "color",
    "type": "color",
    "isVariantAttribute": True,
    "isFilterable": True,
    "values": [
        {"value": "Đen", "colorCode": "#000000"},
        {"value": "Trắng", "colorCode": "#FFFFFF"}
    ]
}

# AttributeCreateResponse / AttributeDetailResponse
example_attribute_response = {
    "id": "65e6e8e8e8e8e8e8e8e8e8e8",
    "name": "Color",
    "code": "color",
    "type": "color",
    "isVariantAttribute": True,
    "isFilterable": True,
    "values": [
        {"value": "Đen", "colorCode": "#000000"}
    ],
    "createdAt": "2023-01-01T10:00:00Z",
    "updatedAt": "2023-01-01T10:00:00Z"
}

# AttributeUpdate Request Body
example_attribute_update_request = {
    "name": "Color (Mới)",
    "isFilterable": False,
    "values": [
        {"value": "Xám", "colorCode": "#CCCCCC"}
    ]
}

# AttributeListAll Response
example_attribute_list_response = {
    "attributes": [
        # ... list of example_attribute_response objects ...
    ]
}
```

**3. Repository (`AttributeRepository`)**

Triển khai `AttributeRepository` với các phương thức sau, tuân thủ tất cả các `repository_rules.md` (đặc biệt về `AsyncCollection`, nhận `dict` làm tham số, không logic nghiệp vụ, chuyển `ObjectId` sang `str` trước khi trả về, không dùng `aggregate`):

*   `get_all(self) -> list[dict]`: Lấy tất cả thuộc tính.
*   `create(self, data: dict) -> dict`: Thêm thuộc tính mới.
*   `update(self, attribute_id: str, data: dict) -> dict | None`: Cập nhật thuộc tính theo ID.

**4. Service (`AttributeService`)**

Triển khai `AttributeService` với các phương thức sau, tuân thủ tất cả các `service_rule.md` (đặc biệt về inject `Repository`, xử lý business logic, tránh N+1 Query, convert dữ liệu từ repository sang Pydantic Schema trước khi trả về, sử dụng Python 3.12+ syntax):

*   `get_all_attributes(self) -> list[AttributeCreateResponse]`: Lấy tất cả thuộc tính, chuyển đổi sang Schema.
*   `create_attribute(self, attribute_data: AttributeCreate) -> AttributeCreateResponse`: Tạo thuộc tính, xử lý logic (nếu có), lưu vào repo, chuyển đổi sang Schema.
*   `update_attribute(self, attribute_id: str, attribute_data: AttributeUpdate) -> AttributeUpdateResponse | None`: Cập nhật thuộc tính, xử lý logic (kiểm tra tồn tại), lưu vào repo, chuyển đổi sang Schema.

### Yêu Cầu Chung

*   Sử dụng Python 3.12+ và các tính năng `async/await` của FastAPI.
*   Tuân thủ nguyên tắc Clean Architecture.
*   Code phải rõ ràng, dễ đọc, chuẩn backend production.
