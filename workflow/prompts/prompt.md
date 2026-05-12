# FastAPI Base Architecture Plan

## Goal
Xây dựng production-ready FastAPI base scaffold
(chưa có business feature)

---

## Phase 1 – Structure Design
- Thiết kế cấu trúc thư mục
- Định nghĩa vai trò từng module
- Không viết code

## Phase 2 – Core Foundation
- Config (BaseSettings)
- Logging (structured JSON)
- Unified response schema
- Custom exceptions

## Phase 3 – Database Lifecycle (Async PyMongo Native)
PyMongo Async Client (AsyncMongoClient)
Application lifespan management
Dependency injection (database + client)
Graceful shutdown handling
Test-friendly database override support

## Phase 4 – Middleware & Rate Limit
- Request ID middleware
- slowapi integration
- 429 override handler

## Phase 5 – Security Skeleton
- JWT utility (with expiration)
- bcrypt password hashing
- Auth dependency stub

## Phase 6 – App Wiring
- main.py assembly
- Override 422 & 401
- /api/v1/health
- OpenAPI response examples