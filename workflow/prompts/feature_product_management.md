### Mục Tiêu

Triển khai các API endpoint cho phép quản lý sản phẩm (`Product`) và các biến thể sản phẩm (`ProductVariant`). Bao gồm các chức năng CRUD đầy đủ: lấy danh sách có phân trang, lấy chi tiết, tạo mới, cập nhật và xóa sản phẩm.

### Cấu Trúc MongoDB

**Bảng `products`:**
```json
{
  "_id": ObjectId,
  "name": "Áo Thun Nam Polo Basic",
  "slug": "ao-thun-nam-polo-basic",
  "description": "...",
  "featuredImage": { "url": "...", "alt": "..." },
  "category": ObjectId,
  "brand": "LocalBrandVN",
  "isActive": true,
  "createdAt": Date,
  "updatedAt": Date
}
```

**Bảng `product_variants`:**
```json
{
  "_id": ObjectId,
  "productId": ObjectId,
  "sku": "ATP-NAM-POLO-BLACK-S",
  "price": 199000,
  "stock": 45,
  "attributeValues": [
    {
      "attributeId": ObjectId,
      "value": "Đen"
    },
    {
      "attributeId": ObjectId,
      "value": "S"
    }
  ],
  "isDefaultVariant": false, # MỚI: Biến thể mặc định
  "featuredImage": { "url": "...", "alt": "..." },
  "images": [ { "url": "...", "alt": "..." } ],
  "createdAt": Date,
  "updatedAt": Date
}
```

### Yêu Cầu Chi Tiết

**1. Các Endpoint API (Controller/Router)**

*   **GET `/admin/products`**
    *   **Mô tả:** Lấy danh sách tất cả các sản phẩm có hỗ trợ phân trang (`page`, `page_size`), tìm kiếm theo tên/slug và lọc.
    *   **Response:** `UnifiedResponse[ProductListResponse]` schema.
*   **GET `/admin/products/{product_id}`**
    *   **Mô tả:** Lấy thông tin chi tiết của một sản phẩm theo `product_id`.
    *   **Response:** `UnifiedResponse[ProductDetailResponse]` schema.
*   **POST `/admin/products`**
    *   **Mô tả:** Tạo một sản phẩm mới cùng với các biến thể của nó.
    *   **Request Body:** `ProductCreate` schema (sẽ bao gồm cả thông tin biến thể).
    *   **Response:** `UnifiedResponse[ProductDetailResponse]` schema (chi tiết sản phẩm vừa tạo).
*   **PUT `/admin/products/{product_id}`**
    *   **Mô tả:** Cập nhật thông tin của một sản phẩm hiện có theo `product_id`.
    *   **Request Body:** `ProductUpdate` schema.
    *   **Response:** `UnifiedResponse[ProductDetailResponse]` schema (chi tiết sản phẩm đã cập nhật).
*   **DELETE `/admin/products/{product_id}`**
    *   **Mô tả:** Xóa một sản phẩm và tất cả các biến thể liên quan của nó theo `product_id`.
    *   **Response:** `UnifiedResponse[str]` (message thông báo xóa thành công).

**2. Schema (Pydantic v2)**

Tạo các Pydantic schema sau, tuân thủ chặt chẽ tất cả các `schema_rules.md` (đặc biệt về Pydantic v2, đặt tên, `Field` với `description`, `min_length`/`max_length`, `field_validator`, `PyObjectId` cho `_id` và `model_config`):

*   **`ImageSchema`**: Schema cho đối tượng hình ảnh (`url: str`, `alt: str | None`).
*   **`AttributeValueEmbed`**: Schema cho đối tượng trong mảng `attributeValues` của `ProductVariant`. (`attributeId: PyObjectId`, `value: str`).
*   **`ProductVariantCreate`**: Schema cho dữ liệu tạo biến thể sản phẩm.
    *   `sku: str` (duy nhất, validate regex)
    *   `price: float` (min 0)
    *   `stock: int` (min 0)
    *   `attributeValues: list[AttributeValueEmbed]`
    *   `isDefaultVariant: bool` (mặc định False, MỚI)
    *   `featuredImage: ImageSchema | None`
    *   `images: list[ImageSchema]`
*   **`ProductVariantResponse`**: Schema trả về cho biến thể sản phẩm (bao gồm `id`, `productId`, `createdAt`, `updatedAt`, `isDefaultVariant`).
*   **`ProductVariantUpdate`**: Schema cho dữ liệu cập nhật biến thể sản phẩm. Tất cả các trường là tùy chọn (`isDefaultVariant: bool | None` MỚI).
*   **`ProductCreate`**: Schema cho dữ liệu tạo sản phẩm mới.
    *   `name: str` (validate độ dài, không rỗng)
    *   `slug: str` (duy nhất, validate regex)
    *   `description: str | None`
    *   `featuredImage: ImageSchema | None`
    *   `category: PyObjectId` (ID của danh mục)
    *   `brand: str | None`
    *   `isActive: bool` (mặc định True)
    *   `variants: list[ProductVariantCreate]` (bắt buộc phải có ít nhất 1 biến thể)
*   **`ProductDetailResponse`**: Schema trả về chi tiết sản phẩm (bao gồm `id`, `createdAt`, `updatedAt`, và `variants: list[ProductVariantResponse]`).
*   **`ProductUpdate`**: Schema cho dữ liệu cập nhật sản phẩm. Tất cả các trường đều là tùy chọn (`Optional`).
*   **`ProductResponse`**: Một phiên bản đơn giản của `ProductDetailResponse` dùng làm phần tử trong danh sách.
*   **`ProductListResponse`**: Schema chứa danh sách các sản phẩm và tổng số (`items: list[ProductResponse]`, `total_count: int`).

**Ví dụ Dữ Liệu cho Schema:**

```python
# ImageSchema
example_image_schema = {
    "url": "https://example.com/image.jpg",
    "alt": "Ảnh sản phẩm"
}

# AttributeValueEmbed
example_attribute_value_embed = {
    "attributeId": "65e6e8e8e8e8e8e8e8e8e8a1",
    "value": "Đen"
}

# ProductVariantCreate
example_variant_create = {
    "sku": "ATP-NAM-POLO-BLACK-S",
    "price": 199000,
    "stock": 45,
    "attributeValues": [
        {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
        {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"}
    ],
    "isDefaultVariant": True, # MỚI
    "featuredImage": {"url": "...", "alt": "..."},
    "images": [{"url": "...", "alt": "..."}]
}

# ProductCreate Request Body
example_product_create_request = {
    "name": "Áo Thun Nam Polo Basic",
    "slug": "ao-thun-nam-polo-basic",
    "description": "Áo thun nam chất liệu cotton cao cấp, thoáng mát...",
    "featuredImage": {"url": "...", "alt": "..."},
    "category": "65e6e8e8e8e8e8e8e8e8e8b1",
    "brand": "LocalBrandVN",
    "isActive": True,
    "variants": [example_variant_create]
}

# ProductDetailResponse / ProductResponse
example_product_response = {
    "id": "65e6e8e8e8e8e8e8e8e8e8c1",
    "name": "Áo Thun Nam Polo Basic",
    "slug": "ao-thun-nam-polo-basic",
    "description": "Áo thun nam chất liệu cotton cao cấp, thoáng mát...",
    "featuredImage": {"url": "...", "alt": "..."},
    "category": "65e6e8e8e8e8e8e8e8e8e8b1",
    "brand": "LocalBrandVN",
    "isActive": True,
    "createdAt": "2023-01-01T10:00:00Z",
    "updatedAt": "2023-01-01T10:00:00Z",
    "variants": [{
        "id": "65e6e8e8e8e8e8e8e8e8e8d1",
        "productId": "65e6e8e8e8e8e8e8e8e8e8c1",
        "sku": "ATP-NAM-POLO-BLACK-S",
        "price": 199000,
        "stock": 45,
        "attributeValues": [
            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a1", "value": "Đen"},
            {"attributeId": "65e6e8e8e8e8e8e8e8e8e8a2", "value": "S"}
        ],
        "isDefaultVariant": True, # MỚI
        "featuredImage": {"url": "...", "alt": "..."},
        "images": [{"url": "...", "alt": "..."}],
        "createdAt": "2023-01-01T10:00:00Z",
        "updatedAt": "2023-01-01T10:00:00Z"
    }]
}

# ProductListResponse
example_product_list_response = {
    "items": [example_product_response], # List of ProductResponse (can be simplified version without variants)
    "total_count": 1
}

# ProductUpdate Request Body
example_product_update_request = {
    "name": "Áo Thun Nam Polo Cao Cấp",
    "isActive": False
}
```

**3. Repository (`ProductRepository`, `ProductVariantRepository`)**

Triển khai `ProductRepository` và `ProductVariantRepository` với các phương thức sau, tuân thủ tất cả các `repository_rules.md` (đặc biệt: **Cấm sử dụng thư viện Mortor**, chỉ dùng `pymongo.asynchronous.collection.AsyncCollection`, nhận `dict` làm tham số, không logic nghiệp vụ, chuyển `ObjectId` sang `str` trước khi trả về, không dùng `aggregate`):

*   **`ProductRepository`**:
    *   `get_all(self, page: int, page_size: int, search: str | None, filters: dict | None) -> tuple[list[dict], int]`: Lấy tất cả sản phẩm có phân trang, tìm kiếm, lọc.
    *   `get_by_id(self, product_id: str) -> dict | None`: Lấy chi tiết sản phẩm.
    *   `create(self, data: dict) -> dict`: Thêm sản phẩm mới.
    *   `update(self, product_id: str, data: dict) -> dict | None`: Cập nhật sản phẩm.
    *   `delete(self, product_id: str) -> bool`: Xóa sản phẩm.
    *   `get_by_slug(self, slug: str) -> dict | None`: Lấy sản phẩm theo slug (để kiểm tra duy nhất).
*   **`ProductVariantRepository`**:
    *   `get_by_product_id(self, product_id: str) -> list[dict]`: Lấy tất cả biến thể của một sản phẩm.
    *   `create_many(self, variants_data: list[dict]) -> list[dict]`: Thêm nhiều biến thể (khi tạo sản phẩm).
    *   `delete_by_product_id(self, product_id: str) -> int`: Xóa tất cả biến thể của một sản phẩm.
    *   `update_variant(self, variant_id: str, data: dict) -> dict | None`: Cập nhật một biến thể cụ thể (nếu cần, có thể dùng trong `ProductService` để quản lý biến thể).
    *   `get_by_sku(self, sku: str) -> dict | None`: Lấy biến thể theo SKU (để kiểm tra duy nhất).
    *   **MỚI:** `set_default_variant(self, product_id: str, variant_id: str) -> None`: Đặt một biến thể làm mặc định và đảm bảo chỉ có một biến thể mặc định cho mỗi sản phẩm.

**4. Service (`ProductService`)**

Triển khai `ProductService` với các phương thức sau, tuân thủ tất cả các `service_rule.md` (đặc biệt về inject `Repository`, xử lý business logic, tránh N+1 Query, convert dữ liệu từ repository sang Pydantic Schema trước khi trả về, sử dụng Python 3.12+ syntax, và **áp dụng luồng phân trang giống CategoryService**):

*   `__init__(self, product_repo: ProductRepository, product_variant_repo: ProductVariantRepository, category_repo: CategoryRepository, attribute_repo: AttributeRepository)`: Inject tất cả các repository cần thiết.
*   `get_all_products(self, page: int, page_size: int, search: str | None, filters: dict | None) -> ProductListResponse`: Lấy danh sách sản phẩm có phân trang, tìm kiếm, lọc. Xử lý logic để trả về `ProductListResponse`.
*   `get_product_detail(self, product_id: str) -> ProductDetailResponse | None`: Lấy chi tiết sản phẩm, bao gồm cả biến thể.
*   `create_product(self, product_data: ProductCreate) -> ProductDetailResponse`: Tạo sản phẩm, bao gồm:
    *   Kiểm tra tính duy nhất của `name` và `slug`.
    *   Kiểm tra `category` tồn tại.
    *   Kiểm tra `attributeId` trong `attributeValues` của biến thể tồn tại.
    *   Đảm bảo chỉ có **một** `isDefaultVariant` là `True` trong danh sách các biến thể đầu vào.
    *   Tạo sản phẩm chính.
    *   Gán `productId` cho các biến thể và tạo các biến thể.
*   `update_product(self, product_id: str, product_data: ProductUpdate) -> ProductDetailResponse | None`: Cập nhật sản phẩm, bao gồm:
    *   Kiểm tra sản phẩm tồn tại.
    *   Kiểm tra tính duy nhất của `slug` (nếu cập nhật).
    *   Cập nhật thông tin sản phẩm chính.
    *   Xử lý logic cập nhật/thêm/xóa biến thể (ví dụ: nếu `variants` được cung cấp trong `ProductUpdate`, xóa các biến thể cũ và tạo mới hoặc cập nhật các biến thể hiện có).
    *   Đảm bảo chỉ có **một** `isDefaultVariant` là `True` cho mỗi sản phẩm sau khi cập nhật.
*   `delete_product(self, product_id: str) -> bool`: Xóa sản phẩm và tất cả các biến thể liên quan.

**5. Yêu Cầu Chung**

*   Sử dụng Python 3.12+ và các tính năng `async/await` của FastAPI.
*   Tuân thủ nguyên tắc Clean Architecture.
*   Code phải rõ ràng, dễ đọc, chuẩn backend production.
*   Thêm dependency `get_admin_user` cho tất cả các endpoint quản trị.