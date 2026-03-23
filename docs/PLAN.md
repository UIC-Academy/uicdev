# PLAN

We are implementing an LMS platform in Django REST Framework with @docs/uicdev.drawio schema. The flow should be in the following order:

1. Setup the environment
2. Implement models based on schema (but not makemigrations && migrate yet)
3. Implement Custom User Model (I'll do myself, showing 3 approaches)
4. Implement admin configs with proper list, edit, etc. views
5. Implement Authentication (Basic (custom), Session (buit-in), JWT(`rest_framework_simplejwt`))