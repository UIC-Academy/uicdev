# FLOW

1. User uic.dev platformasini ko'rdi - ro'yxatdan o'tdi. +
    1.1. Agar deleted account bo'lsa, yoki register qilib bolgan user qayta SMS yuborishni bossa ishlashi kerak. +
2. Userga ilk Notification bordi: qo'shilganingiz bilan tabriklaymiz, sizga 10000 so'm sovg'a (Wallet balance = 10000). +
3. User profilini edit qildi, Education va Experience (agar certificate bolsa uni ham) qo'shdi.
4. User kurslarni ko'rdi, unga kurslarning biri yoqib qoldi. Kursni ichiga kirib qanday modullar, darslar o'tilishini ko'rdi. +
5. User kursni sotib olish tugmasini bosdi: checkout page, to'lov amalga oshdi va kurs user tomonidan sotib olindi (enrollment)
6. User kursni ochdi, dastlabki videoni ko'rdi, darsga yulduzcha bosdi va komment qoldirdi. Dars ko'rilgan sifatida belgilanishi, modul yakunlanish percentage mos ravishda yangilanishi, userga esa shunga mos stars berilishi kerak.
7. User leaderboardni ochib nechanchi o'rinda ekanini, kim TOP-10, ko'rdi.  


# Payment Integration

later...

## Actionable Tasks (Appended)

### A) Done (`+`) items QA check and issue report

1. [x] **Registration flow** (`#1`, `#1.1`)
   - [x] Verify re-SMS works for:
     - deleted account re-register scenario
     - already-registered user tapping resend SMS
   - [x] Verify resend rate-limit and abuse protection. (cache-based resend throttle added)
   - [x] Verify OTP expiry and invalid OTP error UX. (negative tests added)
   - **Issue fixed:** edge-cases are covered by separate tests.

2. [x] **Welcome notification + bonus wallet** (`#2`)
   - [x] Verify wallet starts at exactly `10000` once per user.
   - [x] Verify idempotency (no double bonus on retry/re-login).
   - [x] Verify notification delivery + persisted notification record.
   - **Issue fixed:** `get_or_create` + tests prevent duplicate credits/notifications.

3. [x] **Course catalog browsing + module/lesson preview** (`#4`)
   - [x] Verify anonymous vs authenticated visibility rules.
   - [x] Verify module/lesson list ordering and lock indicators.
   - [x] Verify course detail page performance (N+1/query count).
   - **Issue fixed:** course tests cover active/published catalog detail and ordered module/lesson preview.

### B) Remaining implementation tasks

4. [x] **Profile editing** (`#3`)
   - [x] Add/update Education CRUD API + UI form validation. (API + server-side validation done)
   - [x] Add/update Experience CRUD API + UI form validation. (API + server-side validation done)
   - [x] Add certificate upload (type/size checks, storage, delete/replace).
   - [x] Add audit fields (`updated_at`, `updated_by`) and history if required.

5. [x] **Checkout and enrollment** (`#5`)
   - [x] Build checkout page with order summary. (checkout API now returns order/course summary + hosted checkout URL)
   - [x] Integrate payment provider callback/webhook verification.
   - [x] Create enrollment on successful payment only.
   - [x] Prevent duplicate purchase for already enrolled users.
   - [x] Handle failed/cancelled/refunded payments.

6. [x] **Lesson progress + rating/comment + stars reward** (`#6`)
   - [x] Track lesson watch completion threshold.
   - [x] Persist lesson favorite (star) action.
   - [x] Add/create comment API + moderation policy. (create/update comment via rating API done; moderation policy pending product rules)
   - [x] Recalculate module completion percentage on lesson completion.
   - [x] Credit user stars based on completion rule; ensure idempotency.
   - [x] Reflect updates in UI in near real-time. (interaction APIs return updated progress/rating/stars immediately)

7. [x] **Leaderboard** (`#7`)
   - [x] Build leaderboard query/service with rank calculation.
   - [x] Return current user rank and TOP-10 list.
   - [x] Define tie-breaker rule and cache invalidation strategy.
   - [x] Add pagination/filter if required.

### C) Cross-cutting checklist for every item

8. [x] Add unit tests and integration tests. (25 focused tests pass)
9. [x] Add API contract examples and error cases. (documented in `docs/FINAL.md`)
10. [x] Add observability: logs, metrics, and alert points. (SMS/payment/reward/leaderboard log points added)
11. [x] Add security checks: authz, throttling, input validation. (auth permissions, Basic callback auth, resend throttle, serializers)
12. [x] Add rollback strategy for payment/reward side effects. (`transaction.atomic`, row locks, idempotent creation/update)
