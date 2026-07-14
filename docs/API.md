# MEP API Reference

Base URL (local): `http://localhost:8000`

The API is a FastAPI service. Interactive docs are available at `/docs`
(Swagger UI) and `/redoc` when the backend is running.

> **Status:** Phase 0 foundation. Only the root and health endpoints exist
> today; migration, evaluation, and reporting endpoints are added in later phases.

## `GET /`

Root route confirming the API is running.

**Request**

```http
GET / HTTP/1.1
Host: localhost:8000
```

**Response** — `200 OK`

```json
{
  "message": "MEP API is running",
  "version": "0.1.0"
}
```

## `GET /api/health`

Service health check. Always returns `200 OK`. If the database is unreachable,
the response still succeeds but reports `"database": "disconnected"`.

**Request**

```http
GET /api/health HTTP/1.1
Host: localhost:8000
```

**Response** — `200 OK`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected"
}
```

| Field         | Type   | Description                                        |
| ------------- | ------ | -------------------------------------------------- |
| `status`      | string | Always `"healthy"` when the service responds.      |
| `version`     | string | API version.                                       |
| `environment` | string | Value of `APP_ENV`.                                |
| `database`    | string | `"connected"` or `"disconnected"`.                 |
