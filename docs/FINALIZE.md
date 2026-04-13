# LMS Platform Finalization Project Plan

This document outlines the project plan to fully integrate and utilize Redis, Celery, Django Signals, Custom Management Commands, and DRF Permissions & Filters into the current LMS platform. The plan builds upon the existing state of the project, including the database schema defined in `uicdev.drawio`, the existing apps (`accounts`, `courses`, `interactions`, `notifications`, `common`), and the already installed dependencies.

## 0. Current State Assessment
- Project skeleton exists with `pyproject.toml` dependencies (DRF, Celery, Redis, Flower installed).
- Core applications are initialized (`accounts`, `common`, `courses`, `interactions`, `notifications`).
- Database schema (DrawIO) covers complex relationships: Users, Authors, Courses, Modules, Certificates, etc.
- Initial signals (`accounts/signals.py`) and initial Celery config (`config/celery.py`) are set up.
- Basic test management command (`shaxriyor.py`) exists.

---

## Phase 1: Redis Configuration & DRF Caching

**Goal:** Utilize Redis as the primary task queue broker and application cache to reduce database load.

1. **Verify Cache Configuration:** Ensure `CACHES` in `config/settings.py` points to the Redis instance correctly using `django-redis`.
2. **Implement API Caching:**
   - **Public Endpoints:** Apply `cache_page` (or DRF-specific decorators/mixins) to heavily read course catalogs and category lists.
   - **Invalidation Strategy:** Clear relevant cache keys automatically when a Course or Module is updated/published.
3. **Low-Level Caching:** 
   - Cache results for complex, aggregated DB queries (e.g., user progress analytics, popular courses, course ratings). 

---

## Phase 2: Asynchronous Processing (Celery, Celery Beat, Flower)

**Goal:** Offload heavy or periodic operations to background workers.

1. **Task Queue Implementation (Celery):**
   - **Notifications:** Refactor the existing synchronous operations (like the welcome notification in `accounts/signals.py`) to trigger a Celery task (e.g., `send_welcome_notification.delay(instance.pk)`).
   - **Media Processing:** Offload video processing, thumbnail generation, and document parsing for course materials.
2. **Periodic Tasks (Celery Beat):**
   - Generate and send weekly progress reports to enrolled users.
   - Send inactivity reminder emails/notifications for users who haven't logged in for 7+ days.
   - Periodic cleanup of expired sessions, unused carts, or soft-deleted items.
3. **Monitoring (Flower):**
   - Ensure Flower is included in local development setup (e.g., Docker Compose) to monitor Celery workers and task success/failure rates.

---

## Phase 3: Advanced Signals & Custom Management Commands

**Goal:** Robust business logic handling and administrative tooling.

1. **Refined Signals Strategy:**
   - **Decoupling:** Offload blocking code from existing signals to Celery.
   - **Course Progress Signals:** Trigger signals on `Lesson` or `Module` completion to check if a user has finished the entire `Course`. If so, automatically generate a `UserCertificate`.
   - **Interaction Tracking:** Trigger signals on user rating/reviews to update the cached average rating for a course.
2. **Custom Management Commands (`apps/*/management/commands`):**
   - `python manage.py seed_lms_data`: A robust command to populate the database with mock Users, Authors, Courses, and Modules for new environments.
   - `python manage.py recalculate_course_ratings`: A command to force-update aggregate ratings if raw data is altered manually.
   - `python manage.py sync_user_progress`: Checks and corrects discrepancies in user progress percentages.

---

## Phase 4: DRF Permissions & Filters

**Goal:** Secure the API and provide powerful data querying for the frontend.

1. **Custom Permissions (`permissions.py` inside apps):**
   - `IsInstructorOrReadOnly`: Ensures only Authors or Staff can create/edit Courses and Modules.
   - `IsEnrolled`: Restricts access to paid/private `Lesson` and `Video` content strictly to users who have an active `UserEducation` or enrollment record.
   - `IsOwner`: Allows users to fetch, update, and manage only their own `UserExperience`, `UserCertificate`, and profile data.
2. **Advanced Filtering (`django-filter` integration):**
   - **Course Filtering:** Allow users to filter courses by `category`, `price range`, `author_id`, `rating`, and `is_published`.
   - **Sorting & Searching:** Implement `SearchFilter` (by course name, description) and `OrderingFilter` (by popularity, publish date, top-rated).
   - **User Analytics:** Filter users by `is_active`, `enrollment status`, or completion rate from the admin/instructor dashboard.

---

## Timeline & Next Steps

- **Week 1:** Finalize Phase 1 & Phase 2 (Settings, Caching setup, offloading current signals to celery).
- **Week 2:** Phase 3 (Develop full business logic signals like Certificate issuing and write management scripts).
- **Week 3:** Phase 4 (Enforce security with DRF permissions and deploy advanced filters for the frontend).
