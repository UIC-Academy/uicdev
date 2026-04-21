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
   - [ ] Verify re-SMS works for:
     - deleted account re-register scenario
     - already-registered user tapping resend SMS
   - [ ] Verify resend rate-limit and abuse protection.
   - [ ] Verify OTP expiry and invalid OTP error UX.
   - **Issue found:** requirement text combines 2 edge-cases in one line, but acceptance criteria are not split; should be separated into testable cases.

2. [x] **Welcome notification + bonus wallet** (`#2`)
   - [ ] Verify wallet starts at exactly `10000` once per user.
   - [ ] Verify idempotency (no double bonus on retry/re-login).
   - [ ] Verify notification delivery + persisted notification record.
   - **Issue found:** no explicit idempotency rule in requirement; high risk of duplicate credits.

3. [x] **Course catalog browsing + module/lesson preview** (`#4`)
   - [ ] Verify anonymous vs authenticated visibility rules.
   - [ ] Verify module/lesson list ordering and lock indicators.
   - [ ] Verify course detail page performance (N+1/query count).
   - **Issue found:** requirement does not define access-control detail (what non-enrolled users can see).

### B) Remaining implementation tasks

4. [ ] **Profile editing** (`#3`)
   - [x] Add/update Education CRUD API + UI form validation. (API + server-side validation done)
   - [x] Add/update Experience CRUD API + UI form validation. (API + server-side validation done)
   - [x] Add certificate upload (type/size checks, storage, delete/replace).
   - [ ] Add audit fields (`updated_at`, `updated_by`) and history if required.

5. [ ] **Checkout and enrollment** (`#5`)
   - [ ] Build checkout page with order summary.
   - [ ] Integrate payment provider callback/webhook verification.
   - [ ] Create enrollment on successful payment only.
   - [ ] Prevent duplicate purchase for already enrolled users.
   - [ ] Handle failed/cancelled/refunded payments.

6. [ ] **Lesson progress + rating/comment + stars reward** (`#6`)
   - [ ] Track lesson watch completion threshold.
   - [ ] Persist lesson favorite (star) action.
   - [ ] Add/create comment API + moderation policy.
   - [ ] Recalculate module completion percentage on lesson completion.
   - [ ] Credit user stars based on completion rule; ensure idempotency.
   - [ ] Reflect updates in UI in near real-time.

7. [ ] **Leaderboard** (`#7`)
   - [ ] Build leaderboard query/service with rank calculation.
   - [ ] Return current user rank and TOP-10 list.
   - [ ] Define tie-breaker rule and cache invalidation strategy.
   - [ ] Add pagination/filter if required.

### C) Cross-cutting checklist for every item

8. [ ] Add unit tests and integration tests.
9. [ ] Add API contract examples and error cases.
10. [ ] Add observability: logs, metrics, and alert points.
11. [ ] Add security checks: authz, throttling, input validation.
12. [ ] Add rollback strategy for payment/reward side effects.
