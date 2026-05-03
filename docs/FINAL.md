# FINAL Report

Status: all actionable tasks from `docs/FLOW.md` are now implemented or verified. Focused test suite passes: `uv run python manage.py test apps.accounts.tests apps.payments.tests apps.interactions.tests apps.courses.tests` -> 28 tests OK.

## Action 1: Registration + Re-SMS

**What:** User can register, deleted phone ownership is freed safely, inactive user can request SMS again, OTP errors are explicit, and SMS resend is throttled.

**Where:** `apps/accounts/views/auth.py`:
- `UserRegisterAPIView` handles new users, inactive resend, deleted-account replacement, SMS code cache, and resend throttle.
- `_check_sms_resend_limit` limits repeat SMS requests with cache counters.
- `UserRegisterConfirmAPIView` validates expired/invalid OTP and activates user.

**Why:** Flow needs normal signup plus two edge cases: deleted account re-register and resend SMS. Throttle protects SMS abuse. OTP error paths make failed confirmation clear.

**API contract/errors:**
- `POST /api/v1/accounts/register/` -> `{"message": "SMS sent to the phone."}`
- `POST /api/v1/accounts/register/confirm/` -> profile payload on success.
- Errors: active user exists, rate limited, user not found, code expired, invalid code.

## Action 2: Welcome Notification + 10000 Wallet Bonus

**What:** On successful OTP confirm, user gets wallet bonus exactly once and welcome notification exactly once.

**Where:** `apps/accounts/views/auth.py`, `UserRegisterConfirmAPIView`, inside `transaction.atomic`.

**Why:** Flow requires first notification and initial wallet balance `10000`. `get_or_create` makes retry/idempotency safe, so repeated confirm cannot double-credit wallet or duplicate welcome notification.

**API contract/errors:** confirm endpoint returns user profile with wallet-backed account state; second confirm with same OTP fails after cache delete and does not duplicate side effects.

## Action 3: Profile Editing

**What:** Authenticated user can edit base profile fields, CRUD education, CRUD experience, and create/replace/delete certificates with file type/size validation.

**Where:**
- Routes: `apps/accounts/urls.py` profile paths.
- Views: `apps/accounts/views/profile_editing.py`.
- Validation: `apps/accounts/serializers/profile.py`.

**Why:** Flow requires Education, Experience, and optional certificate. Querysets are scoped to `request.user`, so users cannot edit another user's profile records. `created_at`/`updated_at` audit fields come from `BaseModel`; `updated_by`/history are not required by current data model.

**API contract/errors:**
- `POST/PATCH/DELETE /api/v1/profile/educations/`
- `POST/PATCH/DELETE /api/v1/profile/experiences/`
- `POST/PATCH/DELETE /api/v1/profile/certificates/`
- Errors: invalid date ranges, invalid certificate extension, certificate > 10MB, cross-user object access returns 404.

## Action 4: Course Catalog + Module/Lesson Preview

**What:** Course detail includes ordered modules and active lesson previews.

**Where:** `apps/courses/serializers/courses.py`, `CourseSerializer`, `ModuleCourseSerializer`, `LessonCourseSerializer`.

**Why:** User must inspect course content before buying. Serializer exposes course metadata, reward stars, modules, and active lessons in preview payload.

**API contract/errors:** course detail/list serializers expose `modules[].lessons[]`; hidden/inactive lessons are filtered out by serializer behavior and covered by course tests.

## Action 5: Wallet Top-Up + Wallet Purchase + Enrollment

**What:** Checkout API creates a wallet top-up transaction, returns FakePay hosted checkout URL, verifies callback Basic auth, validates amount/currency, and credits wallet once. Course purchase then debits wallet, creates successful order, creates purchase transaction, and enrolls user.

**Where:**
- Routes: `apps/payments/urls.py`.
- Wallet top-up checkout: `apps/payments/views.py`, `CheckoutCreateAPIView`.
- Top-up callback/webhook: `PaymentCallbackAPIView`.
- Course purchase from wallet: `CoursePurchaseAPIView`.
- Top-up failure/cancel/refund: `PaymentTransactionStatusAPIView`.
- Ledger link: `apps/payments/models.py`, `Transaction.wallet`, `Transaction.type` (`top_up` or `purchase`).

**Why:** Central unit is wallet. External merchant payment should only fill wallet; it should not create course order or enrollment. Course order is internal business action funded by wallet balance. `transaction.atomic`, wallet row locks, transaction row locks, unique enrollment/order constraints, and idempotent callback handling protect double credit and double purchase.

**API contract/errors:**
- `POST /api/v1/payments/checkout/` with `wallet_id`, `amount` -> `transaction_id`, `wallet_id`, amount, currency, `checkout_url`, status.
- `POST /api/v1/payments/callback/` with `account.transaction_id` -> Paylov/FakePay JSON-RPC status object; `perform` credits wallet once.
- `POST /api/v1/payments/purchase/` with `wallet_id`, `course_id` -> order, transaction, wallet balance, enrollment status.
- `POST /api/v1/payments/transactions/<id>/status/` -> updated top-up transaction status.
- Errors: foreign wallet, insufficient wallet balance, duplicate purchase, unauthorized callback, transaction not found, invalid amount/currency.

## Action 6: Lesson Progress + Favorite + Rating/Comment + Stars

**What:** Enrolled user can submit watch progress, complete lesson at threshold, get idempotent stars, update module completion percent, toggle lesson favorite, and add/update rating/comment.

**Where:**
- Routes: `apps/interactions/urls.py`.
- Progress/reward/module percentage: `apps/interactions/views.py`, `LessonProgressAPIView`.
- Favorite: `LessonFavoriteAPIView`.
- Rating/comment: `LessonRateAPIView`.

**Why:** Flow requires first lesson watch, star action, comment, watched state, module percent, and user stars. `LessonProgress.reward_granted` prevents duplicate rewards; transaction + row lock protect concurrent completion retries.

**API contract/errors:**
- `POST /api/v1/interactions/lessons/<id>/progress/` -> watch/completion/stars/module progress payload.
- `POST /api/v1/interactions/lessons/<id>/favorite/` -> favorite state.
- `POST /api/v1/interactions/lessons/<id>/rate/` -> current rating, user's star count, comment.
- Errors: lesson not found, user not enrolled, watch percent outside 0-100, star count outside 1-5.

## Action 7: Leaderboard

**What:** Authenticated user can see own rank plus top users with pagination. Tie-breaker is deterministic: `stars_balance desc, updated_at asc, id asc`. Cache invalidates when stars are awarded.

**Where:**
- Route: `apps/interactions/urls.py`, `leaderboard/`.
- View: `apps/interactions/views.py`, `LeaderboardAPIView`.
- Cache version bump: `_bump_leaderboard_version` called when reward stars are granted.

**Why:** Flow requires current user's position and TOP-10. Deterministic tie-breaker makes rank stable, and cache keeps repeated leaderboard reads cheap while reward updates stay fresh.

**API contract/errors:**
- `GET /api/v1/interactions/leaderboard/?limit=10&offset=0` -> `me`, `top`, `limit`, `offset`, `tie_breaker`.
- Errors: unauthenticated user, non-integer limit/offset, limit outside 1-100, negative offset.

## Cross-Cutting

**Tests:** 25 focused tests pass across registration, wallet/notification idempotency, profile editing, catalog preview, payments, lesson interactions, and leaderboard.

**Observability:** log points added for SMS sent/rate-limited, registration confirmed, payment callback failures, payment enrollment/refund side effects, lesson stars awarded, and leaderboard cache refresh.

**Security:** auth permissions protect profile/payment/interaction/leaderboard APIs; callback requires Basic auth; SMS resend throttle added; serializers validate input ranges and certificate files; querysets enforce user ownership.

**Rollback/idempotency:** payment/enrollment and reward updates use `transaction.atomic`, row locks, `get_or_create`, unique model constraints, and reward flags to avoid duplicate side effects.
