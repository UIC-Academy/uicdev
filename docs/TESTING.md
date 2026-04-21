# TESTING GUIDE

## Chapter 1: Django Test Runner (`manage.py test`)

### 1) Purpose
- Best when you want native Django behavior out of the box.
- Uses `unittest` style (`TestCase`, `TransactionTestCase`) with Django DB isolation helpers.

### 2) Basic commands

```bash
# Run all tests
python manage.py test

# Run a specific app
python manage.py test apps.courses

# Run one test module
python manage.py test apps.courses.tests.test_enrollment

# Run one class or method
python manage.py test apps.courses.tests.test_enrollment.EnrollmentTests
python manage.py test apps.courses.tests.test_enrollment.EnrollmentTests.test_duplicate_enroll_blocked
```

### 3) Typical structure
- Keep tests near app code:
  - `apps/<app_name>/tests/test_*.py`
- Prefer `TestCase` for DB tests (transaction wrapped, rolled back).
- Use `setUpTestData` for shared fixtures and faster setup.

### 4) Good fit in this project
- Enrollment/payment integrity checks.
- Progress recalculation correctness.
- Notification/wallet credit idempotency checks.

---

## Chapter 2: Pytest (`pytest` + `pytest-django`)

### 1) Purpose
- Best for concise test syntax, rich fixtures, and plugin ecosystem.
- Supports both unit and integration style with flexible parametrization.

### 2) Minimal setup

```bash
pip install pytest pytest-django
```

`pytest.ini` example:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = -ra -q
```

### 3) Basic commands

```bash
# Run all tests
pytest

# Run one file
pytest apps/courses/tests/test_enrollment.py

# Run one test
pytest apps/courses/tests/test_enrollment.py::test_duplicate_enroll_blocked

# Stop on first fail
pytest -x

# Coverage (if installed)
pytest --cov=apps --cov-report=term-missing
```

### 4) Typical patterns
- Use fixtures for users/courses/enrollments.
- Use `@pytest.mark.django_db` for DB-access tests.
- Use `@pytest.mark.parametrize` for rule matrices (e.g., payment states).

### 5) Good fit in this project
- Fast unit tests for business rules (rewards, rank scoring, permissions).
- Matrix tests for checkout and webhook scenarios.
- API contract tests with reusable client fixtures.

---

## Django Test vs Pytest (Comparison)

### 1) Readability and speed
- Django test runner: explicit and stable, but can be verbose.
- Pytest: usually shorter and easier to scale with fixtures.

### 2) Ecosystem and extensibility
- Django test runner: enough for core backend testing.
- Pytest: stronger plugin ecosystem (`pytest-cov`, `xdist`, snapshot tools).

### 3) Team workflow recommendation
- If your current suite is mostly `unittest.TestCase`, keep Django runner for stability.
- If you are expanding test coverage quickly, prefer pytest for faster authoring and parametrized scenarios.

### 4) Practical recommendation for this repo
- Keep existing Django tests working.
- Add pytest for new tests and advanced scenarios.
- Use one CI command eventually (example): `pytest` as the primary runner, while supporting legacy Django-style tests during transition.
