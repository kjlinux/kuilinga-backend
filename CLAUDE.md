# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KUILINGA is a **FastAPI-based employee attendance management system** with IoT device integration. It's a multi-tenant SaaS backend supporting real-time attendance tracking via HTTP REST API and MQTT protocol.

**Technology Stack:**
- FastAPI (async Python web framework)
- PostgreSQL 14+ with SQLAlchemy ORM
- Alembic for database migrations
- JWT authentication with RBAC (Role-Based Access Control)
- MQTT (HiveMQ) for IoT device communication
- WebSocket for real-time updates
- Pydantic for data validation

## Development Commands

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and MQTT broker
docker-compose up -d

# Initialize database with demo data
python scripts/init_db.py
```

### Running the Application
```bash
# Development mode (with hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode (multiple workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Migrations
```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Database Seeding
```bash
# Full initialization with demo data
python scripts/init_db.py

# Additional seeding scripts
python scripts/seed.py          # Standard seeding
python scripts/seed_quick.py    # Quick minimal seeding
python scripts/seed_data.py     # Extended data seeding

# Database maintenance
python scripts/check_db.py      # Validate database state
python scripts/cleanup_db.py    # Clean up test data
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_auth.py

# Run specific test function
pytest tests/test_api/test_auth.py::test_login_success
```

### API Documentation
Once running, access interactive docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Architecture Overview

### Layered Architecture Pattern
```
API Layer (endpoints)
    ↓
Service Layer (business logic)
    ↓
CRUD Layer (database operations)
    ↓
Models/Schemas Layer (ORM & validation)
    ↓
Database Layer (PostgreSQL)
```

### Key Directory Structure
- **app/api/v1/endpoints/** - API route handlers (17 modules: auth, users, employees, attendance, devices, etc.)
- **app/models/** - SQLAlchemy ORM models (User, Employee, Attendance, Organization, etc.)
- **app/schemas/** - Pydantic validation schemas (request/response DTOs)
- **app/crud/** - Database CRUD operations (inherits from generic CRUDBase)
- **app/services/** - Business logic (MQTT client, attendance service, report generation, export service)
- **app/core/** - Security utilities (JWT, password hashing, permissions)
- **app/dependencies.py** - FastAPI dependency injection (auth, DB sessions, permission checking)
- **app/templates/reports/** - Jinja2 HTML templates for PDF report generation

### Authentication Flow
1. User logs in with credentials → JWT access token (30 min) + refresh token (7 days)
2. Access token included in `Authorization: Bearer <token>` header
3. `get_current_user()` dependency validates JWT and retrieves User
4. Permission/role checking via `PermissionChecker` or `require_role()` dependencies
5. Refresh token endpoint generates new access token without re-login

## Critical Architecture Patterns

### Multi-Tenancy
All data is scoped to an **Organization**. Every User, Employee, Department, and Site belongs to an organization. When querying data, always filter by the current user's organization to maintain tenant isolation.

### Dual User System
- **User** - Authentication entity (email, password, JWT subject, roles)
- **Employee** - Business entity (name, badge ID, position, department, site)
- Relationship: User ↔ Employee is 1:1 (optional, not all users are employees)

### Role-Based Access Control (RBAC)
- Users have Roles (many-to-many via `user_roles` table)
- Roles have Permissions (many-to-many)
- Common roles: `admin`, `manager`, `employee`, `viewer`
- Permissions: granular actions like `attendance:create`, `employee:update`, `report:view`
- Use `PermissionChecker(["permission:name"])` dependency in endpoints
- Superusers bypass all permission checks

### IoT Integration - Dual Protocol Support

**HTTP Method:**
```python
POST /api/v1/attendances/
Headers: Authorization: Bearer <JWT>
Body: {
  "timestamp": "2023-10-27T10:00:00Z",
  "type": "in",  # or "out"
  "employee_id": "uuid-string",
  "device_id": "uuid-string"
}
```

**MQTT Method:**
- Devices publish to: `kuilinga/devices/{device_serial}/attendance`
- Payload uses **badge_id** instead of employee UUID:
```json
{
  "timestamp": "2023-10-27T10:01:00Z",
  "type": "in",
  "badge_id": "EMP-BADGE-456"
}
```
- Backend auto-matches badge_id to employee
- Real-time broadcast to WebSocket clients after processing
- MQTT client starts/stops with FastAPI lifecycle events

### CRUD Base Pattern
All CRUD classes inherit from `CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]`:
```python
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def get(self, db: Session, id: Any) -> Optional[ModelType]
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> Dict
    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType
    def update(self, db: Session, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType
    def remove(self, db: Session, id: Any) -> Optional[ModelType]
```
Extend this for model-specific operations (e.g., `CRUDUser.get_by_email()`)

### Database Conventions
- **UUID Primary Keys**: All models use string-based UUIDs (auto-generated by `BaseModel`)
- **Table Naming**: Auto-generated as plural lowercase (e.g., `User` → `users`)
- **Foreign Keys**: Cascade deletes where appropriate (Employee deletion → Attendance/Leave records)
- **Timestamps**: Models typically have `created_at` and `updated_at` fields
- **Soft Deletes**: Not implemented; use hard deletes

## Configuration Management

Environment variables are managed via Pydantic Settings (`app/config.py`). Always add new config to both:
1. `.env.example` - Template with placeholder values
2. `Settings` class in `app/config.py` - Type-safe configuration

Critical environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing secret (MUST be changed in production)
- `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT` - IoT device broker
- `BACKEND_CORS_ORIGINS` - Allowed frontend origins (JSON array)

## Working with Models

### Creating New Models
1. Create model in `app/models/your_model.py` inheriting from `BaseModel`
2. Define relationships using SQLAlchemy `relationship()` and foreign keys
3. Import in `app/db/base.py` for Alembic auto-detection
4. Create Pydantic schemas in `app/schemas/your_model.py` (Create, Update, Response)
5. Create CRUD class in `app/crud/your_model.py` extending `CRUDBase`
6. Generate migration: `alembic revision --autogenerate -m "add your_model"`
7. Review and apply: `alembic upgrade head`

### Important Model Relationships
- Organization → Users, Employees, Departments, Sites (1:N)
- User → Employee (1:1)
- User ↔ Role ↔ Permission (M:N)
- Employee → Attendance, Leave (1:N)
- Employee → Department, Site (N:1)
- Device → Attendance (1:N)

## Dependency Injection Patterns

Common dependencies in `app/dependencies.py`:
- `get_db()` - Database session (always close after use)
- `get_current_user()` - Authenticated user from JWT
- `get_current_active_user()` - Active user only
- `get_current_active_superuser()` - Superuser check
- `get_current_active_employee()` - User must be linked to Employee
- `get_current_active_manager()` - Manager role check
- `PermissionChecker(["perm1", "perm2"])` - Granular permission validation
- `require_role("role_name")` - Role-based endpoint protection

Example endpoint with dependencies:
```python
@router.get("/employees/")
def list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker(["employee:view"])),
    skip: int = 0,
    limit: int = 100,
):
    # Only returns employees from current_user's organization
    pass
```

## Real-Time Features

### WebSocket Connection Management
- Connection manager in `app/websocket/connection_manager.py`
- Clients connect to `/api/v1/ws`
- Broadcast attendance events to all connected clients
- Used for live dashboard updates

### MQTT Client Lifecycle
- Initialized in `app/services/mqtt_client.py`
- Starts on FastAPI `startup` event (`app.main.py`)
- Subscribes to `kuilinga/devices/+/attendance` (wildcard for all devices)
- Stops on `shutdown` event
- Handles reconnection automatically

## Report Generation

Reports are generated via `app/services/report_service.py` and `app/services/export_service.py`:
- **Excel**: Uses `pandas` + `openpyxl` for `.xlsx` exports
- **PDF**: Uses `weasyprint` with Jinja2 HTML templates
- **Templates**: HTML in `app/templates/reports/` for styled reports
- Common reports: attendance summary, daily stats, employee timesheets, leave reports

## Default Credentials

After running `python scripts/init_db.py`:
- **Email**: `admin@kuilinga.com`
- **Password**: `admin123`
- **Role**: Superuser with all permissions

## Common Pitfalls

1. **Organization Isolation**: Always filter queries by `current_user.organization_id` unless explicitly fetching cross-organization data (admin only)
2. **JWT Expiry**: Access tokens expire in 30 minutes; frontend must handle refresh token flow
3. **MQTT vs HTTP**: Use badge_id for MQTT, employee_id (UUID) for HTTP attendance
4. **Cascade Deletes**: Deleting an Employee will cascade delete their Attendance and Leave records
5. **Database Sessions**: Always use dependency injection for `get_db()`, never create manual sessions in endpoints
6. **Migration Conflicts**: Review auto-generated migrations before applying; Alembic may miss complex changes

## API Conventions

- **Versioning**: All routes prefixed with `/api/v1/`
- **Pagination**: Use `skip` and `limit` query params (default: 0, 100)
- **Response Format**: JSON with snake_case keys
- **Error Responses**: HTTP status codes (401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Validation Error, 500 Internal Server Error)
- **Datetime Format**: ISO 8601 UTC (e.g., `2023-10-27T10:00:00Z`)
- **IDs**: String-based UUIDs (not integers)

## Testing Strategy

- Test files mirror `app/` structure in `tests/`
- Use `conftest.py` for pytest fixtures (test database, test client, mock users)
- Mock external dependencies (MQTT, email, SMS)
- Focus on endpoint tests (authentication, authorization, business logic)
- Database tests use transactions rolled back after each test
