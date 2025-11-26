# Pre-Next.js Optimization Checklist

**Quick Reference**: Use this checklist to track progress on optimization roadmap.

## Phase 1: Foundation (CRITICAL) ⏱️ 2 weeks

### Database Layer 🔴
- [ ] Integrate connection pooling into `database.py` (50+ functions)
- [ ] Replace all direct `connect_to_db()` calls with `get_db_connection()` context manager
- [ ] Fix 30+ SQL injection vulnerabilities (parameterized queries)
- [ ] Add transaction management to multi-step operations
- [ ] Test connection pool under load (100+ concurrent connections)

**Files to Update**:
```
✓ database_pool.py - Already created
□ database.py - 90+ functions need refactoring
□ phase1_enhanced_ui.py - 20+ direct connection calls
□ ui/tasks_users_ui.py
□ ui/tab_validation.py
□ ui/tab_review.py
□ ui/tab_project.py
□ ui/tab_data_imports.py
□ tools/* - 15+ utility scripts
```

**Validation Tests**:
- [ ] Connection pool reuses connections (verify with connection ID tracking)
- [ ] No SQL injection (run security scanner)
- [ ] All queries use parameterized statements
- [ ] Transactions rollback on error

---

### Security 🔴
- [ ] Remove hardcoded default password from `config.py`
- [ ] Require all environment variables (no defaults for sensitive data)
- [ ] Implement JWT authentication
  - [ ] Create `backend/middleware/auth.py`
  - [ ] Add `/api/auth/login` endpoint
  - [ ] Add `/api/auth/logout` endpoint
  - [ ] Add `@jwt_required()` decorator to all API endpoints
- [ ] Fix CORS configuration (restrict to specific origins)
- [ ] Add input sanitization middleware
- [ ] Implement CSRF protection

**New Files to Create**:
```
□ backend/middleware/auth.py
□ backend/middleware/validation.py
□ backend/schemas/auth.py
```

**Validation Tests**:
- [ ] Cannot access API without valid JWT token
- [ ] CORS only allows approved origins
- [ ] XSS attempts are sanitized
- [ ] CSRF tokens validated

---

### Configuration 🔴
- [ ] Add config validation on startup
- [ ] Create environment-specific configs (dev/staging/prod)
- [ ] Document all required environment variables in `.env.example`
- [ ] Set up secret management (environment variables, not code)
- [ ] Validate DB connection on startup (fail fast)

**New Files to Create**:
```
□ .env.example - Template for environment variables
□ config_validator.py - Startup validation
```

**Validation Tests**:
- [ ] App fails to start if required env vars missing
- [ ] No secrets in source code
- [ ] Different configs work for each environment

---

## Phase 2: Service Layer (HIGH) ⏱️ 3 weeks

### Business Logic Extraction 🟡
- [ ] Consolidate review services
  - [ ] Decide: Migrate to `services/review_service.py` OR refactor `review_management_service.py`
  - [ ] Port all unique features from legacy to new service
  - [ ] Update UI to use consolidated service
  - [ ] Deprecate old service

- [ ] Create Task Service
  - [ ] Extract logic from `phase1_enhanced_ui.py`
  - [ ] Create `core/services/task_service.py`
  - [ ] Implement TaskService class with CRUD operations
  - [ ] Add dependency management logic
  - [ ] Add status cascade rules

- [ ] Create Billing Service
  - [ ] Extract billing logic from UI
  - [ ] Create `core/services/billing_service.py`
  - [ ] Implement BillingService class
  - [ ] Add calculation methods
  - [ ] Add claim generation

- [ ] Create Validation Service
  - [ ] Centralize all validation rules
  - [ ] Create `core/services/validation_service.py`
  - [ ] Single source of truth for business rules
  - [ ] Remove duplicate validation code

**New Files to Create**:
```
□ core/services/task_service.py (~500 lines)
□ core/services/billing_service.py (~400 lines)
□ core/services/validation_service.py (~300 lines)
□ core/services/__init__.py
```

**Validation Tests**:
- [ ] All business logic works without UI
- [ ] Services can be imported by both desktop and web apps
- [ ] No code duplication between layers
- [ ] Validation rules consistent everywhere

---

### REST API Development 🟡
- [ ] Review Management Endpoints
  - [ ] `GET /api/reviews` - List all reviews
  - [ ] `POST /api/reviews` - Create review cycle
  - [ ] `GET /api/reviews/<id>` - Get review details
  - [ ] `PATCH /api/reviews/<id>` - Update review
  - [ ] `DELETE /api/reviews/<id>` - Delete review
  - [ ] `POST /api/reviews/<id>/schedule` - Generate schedule
  - [ ] `GET /api/reviews/<id>/progress` - Get progress

- [ ] Task Management Endpoints
  - [ ] `GET /api/tasks` - List tasks
  - [ ] `POST /api/tasks` - Create task
  - [ ] `GET /api/tasks/<id>` - Get task details
  - [ ] `PATCH /api/tasks/<id>` - Update task
  - [ ] `DELETE /api/tasks/<id>` - Delete task
  - [ ] `GET /api/tasks/<id>/dependencies` - Get dependencies
  - [ ] `POST /api/tasks/<id>/dependencies` - Add dependency

- [ ] Billing Endpoints
  - [ ] `GET /api/billing/claims` - List claims
  - [ ] `POST /api/billing/claims` - Create claim
  - [ ] `GET /api/billing/claims/<id>` - Get claim details
  - [ ] `PATCH /api/billing/claims/<id>` - Update claim
  - [ ] `POST /api/billing/calculate` - Calculate billing

- [ ] Add Pydantic Validation
  - [ ] Create schema models for each endpoint
  - [ ] Validate all incoming requests
  - [ ] Return validation errors with 400 status

**New Files to Create**:
```
□ backend/routes/reviews.py (~400 lines)
□ backend/routes/tasks.py (~350 lines)
□ backend/routes/billing.py (~300 lines)
□ backend/schemas/review.py
□ backend/schemas/task.py
□ backend/schemas/billing.py
```

**Validation Tests**:
- [ ] All endpoints documented in OpenAPI/Swagger
- [ ] All endpoints have error handling
- [ ] All endpoints validate input with Pydantic
- [ ] All endpoints return consistent JSON structure

---

### Folder Restructure 🟡
- [ ] Create new directory structure
  ```
  □ core/
  □ core/services/
  □ core/database/
  □ core/database/repositories/
  □ core/database/models/
  □ desktop/
  □ desktop/tabs/
  □ backend/routes/
  □ backend/middleware/
  □ backend/schemas/
  ```

- [ ] Move files to new locations
  - [ ] `database_pool.py` → `core/database/connection_pool.py`
  - [ ] `database.py` → `core/database/legacy.py`
  - [ ] `phase1_enhanced_ui.py` → `desktop/app.py`
  - [ ] Split UI tabs into `desktop/tabs/` modules
  - [ ] Move services to `core/services/`

- [ ] Update all imports
  - [ ] Update import statements in all files
  - [ ] Test application still runs
  - [ ] Update documentation

**Validation Tests**:
- [ ] Application launches without errors
- [ ] All imports resolve correctly
- [ ] Tests still pass
- [ ] No circular import dependencies

---

## Phase 3: Quality & Performance (MEDIUM) ⏱️ 2 weeks

### Testing 🟢
- [ ] Service Layer Unit Tests
  - [ ] `tests/unit/services/test_review_service.py`
  - [ ] `tests/unit/services/test_task_service.py`
  - [ ] `tests/unit/services/test_billing_service.py`
  - [ ] `tests/unit/services/test_validation_service.py`
  - [ ] Target: 80%+ coverage

- [ ] API Integration Tests
  - [ ] `tests/integration/test_review_api.py`
  - [ ] `tests/integration/test_task_api.py`
  - [ ] `tests/integration/test_billing_api.py`
  - [ ] `tests/integration/test_auth_api.py`

- [ ] Database Tests
  - [ ] `tests/database/test_connection_pool.py`
  - [ ] `tests/database/test_repositories.py`

- [ ] Set up CI/CD
  - [ ] Configure GitHub Actions / Azure Pipelines
  - [ ] Run tests on every commit
  - [ ] Enforce test coverage thresholds

**Validation Tests**:
- [ ] All tests pass in CI
- [ ] Coverage > 80% for service layer
- [ ] Coverage > 70% for API layer
- [ ] No flaky tests

---

### Performance 🟢
- [ ] Fix N+1 Query Problems
  - [ ] Audit all data loading code
  - [ ] Replace loops with JOINs
  - [ ] Use database views where appropriate

- [ ] Implement Caching
  - [ ] Install Redis
  - [ ] Add Flask-Caching
  - [ ] Cache reference data (users, templates)
  - [ ] Cache project lists
  - [ ] Implement cache invalidation

- [ ] Background Jobs
  - [ ] Install Celery
  - [ ] Move ACC imports to background tasks
  - [ ] Move Revit health imports to background tasks
  - [ ] Add progress tracking for long operations

- [ ] Add Performance Monitoring
  - [ ] Log slow queries (> 1 second)
  - [ ] Track API response times
  - [ ] Set up alerting for performance degradation

**Validation Tests**:
- [ ] Page load times < 1 second
- [ ] API responses < 500ms
- [ ] No queries taking > 2 seconds
- [ ] Cache hit rate > 80%

---

### Code Quality 🟢
- [ ] Standardize Error Handling
  - [ ] Create exception hierarchy
  - [ ] Remove all `print()` error logging
  - [ ] Add API error handlers
  - [ ] Return consistent error responses

- [ ] Implement Structured Logging
  - [ ] Configure JSON logging
  - [ ] Add request ID tracking
  - [ ] Log all API calls
  - [ ] Log all database errors
  - [ ] Add performance logging

- [ ] Address TODOs
  - [ ] Review all 20+ TODO comments
  - [ ] Create tickets for incomplete features
  - [ ] Prioritize and fix critical TODOs

- [ ] Code Review & Cleanup
  - [ ] Remove dead code
  - [ ] Remove commented-out code
  - [ ] Fix linting errors
  - [ ] Add docstrings to all public functions

**Validation Tests**:
- [ ] No print() statements in production code
- [ ] All exceptions properly typed
- [ ] All functions have docstrings
- [ ] Linter passes with no warnings

---

## Phase 4: Next.js Implementation ⏱️ 4 weeks

### Prerequisites Checklist ✅
Before starting Next.js, verify ALL of the following:

- [ ] ✅ Database connection pooling fully integrated
- [ ] ✅ No SQL injection vulnerabilities
- [ ] ✅ JWT authentication working
- [ ] ✅ Complete REST API for core features (reviews, tasks, billing)
- [ ] ✅ Service layer fully extracted
- [ ] ✅ All Phase 1 security issues resolved
- [ ] ✅ Configuration validated in all environments
- [ ] ✅ Core unit tests passing (>80% coverage)
- [ ] ✅ API integration tests passing
- [ ] ✅ Performance benchmarks met

### Next.js Setup 🟢
- [ ] Initialize Next.js 14 project in `frontend/`
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --app
  ```

- [ ] Configure project
  - [ ] TypeScript configuration
  - [ ] Tailwind CSS setup
  - [ ] ESLint configuration
  - [ ] Prettier setup
  - [ ] Path aliases (@components, @lib, etc.)

- [ ] API Client
  - [ ] Install Axios
  - [ ] Create API client with JWT interceptors
  - [ ] Add error handling
  - [ ] Add request/response logging

- [ ] Authentication
  - [ ] Login page
  - [ ] JWT token storage
  - [ ] Protected routes
  - [ ] Auth context provider

**New Files to Create**:
```
□ frontend/app/layout.tsx
□ frontend/app/page.tsx
□ frontend/lib/api-client.ts
□ frontend/lib/auth.ts
□ frontend/components/auth/LoginForm.tsx
```

---

### Core Features 🟢
- [ ] Project Management UI
  - [ ] Project list page
  - [ ] Project detail page
  - [ ] Create project form
  - [ ] Edit project form
  - [ ] Delete confirmation

- [ ] Review Management UI
  - [ ] Review cycles list
  - [ ] Create review cycle form
  - [ ] Review schedule calendar
  - [ ] Progress dashboard
  - [ ] Review details page

- [ ] Task Management UI
  - [ ] Task list with filters
  - [ ] Task board (Kanban view)
  - [ ] Create task form
  - [ ] Task dependencies visualization
  - [ ] Task detail page

- [ ] Billing UI
  - [ ] Claims list
  - [ ] Create claim form
  - [ ] Billing calculations
  - [ ] Invoice generation

**Validation Tests**:
- [ ] All CRUD operations work via UI
- [ ] Forms validate input correctly
- [ ] Error messages display properly
- [ ] Loading states show during async operations
- [ ] Responsive design works on mobile

---

### Polish 🟢
- [ ] UI/UX
  - [ ] Consistent design system
  - [ ] Loading skeletons
  - [ ] Error boundaries
  - [ ] Toast notifications
  - [ ] Responsive layouts

- [ ] Performance
  - [ ] Image optimization
  - [ ] Code splitting
  - [ ] Lazy loading
  - [ ] Caching strategy

- [ ] Deployment
  - [ ] Environment configuration
  - [ ] Build process
  - [ ] Docker containers
  - [ ] Deployment pipeline

**Validation Tests**:
- [ ] Lighthouse score > 90
- [ ] No console errors
- [ ] Works on Chrome, Firefox, Safari, Edge
- [ ] Mobile responsive
- [ ] Accessible (WCAG AA)

---

## Progress Tracking

**Last Updated**: [DATE]

### Completion Summary
- Phase 1: Foundation - [ ] 0% (0/15 items)
- Phase 2: Service Layer - [ ] 0% (0/22 items)
- Phase 3: Quality & Performance - [ ] 0% (0/16 items)
- Phase 4: Next.js - [ ] 0% (Blocked until Phases 1-3 complete)

**Overall Progress**: [ ] 0% (0/53 items)

---

## Quick Commands

### Run Tests
```bash
# All tests
pytest tests/

# Specific test category
pytest tests/unit/services/
pytest tests/integration/

# With coverage
pytest --cov=core --cov=backend tests/
```

### Security Scan
```bash
# SQL injection check
bandit -r . -f json -o security-report.json

# Dependency vulnerabilities
pip-audit
```

### Performance Benchmarks
```bash
# API load testing
locust -f tests/performance/api_load_test.py

# Database connection pool test
python tests/performance/test_connection_pool.py
```

### Code Quality
```bash
# Linting
flake8 core/ backend/

# Type checking
mypy core/ backend/

# Format code
black core/ backend/
```

---

## Decision Log

**Track key decisions made during optimization**:

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| [DATE] | Review Service Consolidation: Option __ | [Reasoning] | [Files affected] |
| | | | |

---

## Notes & Issues

**Track blockers and important notes**:

- 

---

**Checklist Version**: 1.0  
**Aligns With**: PRE_NEXTJS_OPTIMIZATION_AUDIT.md v1.0
