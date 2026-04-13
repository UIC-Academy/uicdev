# Celery, Celery Beat & Flower - Amaliy dars rejasi

**Sana:** 06.04.2025
**Mavzu:** Asynchronous Task Processing with Celery
**Davomiylik:** ~2.5 soat

---

## Hozirgi holat (nima tayyor)

- `config/celery.py` — Celery app yaratilgan, `autodiscover_tasks()` ishlaydi
- `config/__init__.py` — celery_app eksport qilingan
- `config/settings.py` — `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (Redis), timezone va limits sozlangan
- `apps/common/tasks.py` — bitta `test_task` bor (3 soniya sleep)
- `apps/common/views/test_task.py` — `TestTaskAPIView` endpointi bor (`/testtask/`)
- `pyproject.toml` — `celery` va `flower` dependency sifatida qo'shilgan
- **Nima yetishmaydi:** `django-celery-beat` o'rnatilmagan, periodic task yo'q, real business logic task yo'q

---

## 1-qism: Nazariya (20 min)

### Celery nima?
- Distributed task queue — og'ir/uzoq ishlarni background'da bajarish
- Broker (Redis) — tasklar navbati, Result backend — natijani saqlash
- Worker — tasklarni olib, bajaruvchi process

### Arxitektura diagrammasi
```
Django App  --->  Redis (Broker)  --->  Celery Worker
    ^                                       |
    |                                       v
    +------  Redis (Result Backend)  <------+
```

### Celery Beat nima?
- Periodic task scheduler — cron kabi, lekin Celery ichida
- `django-celery-beat` — periodic tasklarni DB orqali admin paneldan boshqarish

### Flower nima?
- Celery uchun real-time web monitoring tool
- Worker status, task progress, grafikllar ko'rsatadi

---

## 2-qism: Mavjud setupni tekshirish (15 min)

### 2.1 Redis ishlayaptimi?
```bash
redis-cli ping
# PONG bo'lishi kerak
```

### 2.2 Celery worker ishga tushirish
```bash
cd /path/to/project
uv run celery -A config worker -l info
```

### 2.3 Test task'ni sinash
Boshqa terminalda:
```bash
# Server ishga tushirish
uv run python manage.py runserver
```

Brauzerda yoki curl bilan:
```bash
curl http://localhost:8000/common/testtask/
# {"message": "Task started"}
```

Worker terminalida `Task finished` chiqishi kerak.

### 2.4 Flower ishga tushirish
Uchinchi terminalda:
```bash
uv run celery -A config flower --port=5555
```
Brauzerda `http://localhost:5555` — worker status, active tasks ko'rinadi.

---

## 3-qism: 1-Task — Country/Region import from JSON (30 min)

**Maqsad:** `docs/countries.json` va `docs/regions.json` fayllaridan Country va Region modellarini DB ga yuklash. Bu real hayotda katta data importlari uchun ishlatiladi — API dan data tortish, CSV/JSON import va hokazo.

### 3.1 Task yozish

`apps/common/tasks.py` ga qo'shish:

```python
import json
import time

from celery import shared_task
from django.conf import settings


@shared_task
def test_task():
    time.sleep(3)
    print("Task finished")
    return True


@shared_task
def import_countries_and_regions():
    """Import countries and regions from JSON files into the database."""
    from apps.common.models import Country, Region

    base_dir = settings.BASE_DIR

    # 1. Load countries
    with open(base_dir / "docs" / "countries.json") as f:
        countries_data = json.load(f)

    country_map = {}  # json_id -> db_object
    for item in countries_data:
        country, created = Country.objects.get_or_create(
            name=item["name"],
        )
        country_map[item["id"]] = country

    countries_count = len(countries_data)

    # 2. Load regions
    with open(base_dir / "docs" / "regions.json") as f:
        regions_data = json.load(f)

    regions_count = 0
    for item in regions_data:
        country = country_map.get(item["country_id"])
        if country:
            Region.objects.get_or_create(
                name=item["name"],
                country=country,
            )
            regions_count += 1

    return f"Imported {countries_count} countries and {regions_count} regions"
```

**Muhim tushuntirish:**
- `get_or_create` — takroriy import xavfsiz (idempotent)
- Model importlarni function ichida qilamiz — circular import'dan saqlanish
- `@shared_task` — har qanday Celery app bilan ishlaydi

### 3.2 View yozish — taskni trigger qilish

`apps/common/views/test_task.py` ni yangilash:

```python
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.tasks import import_countries_and_regions, test_task


class TestTaskAPIView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        test_task.delay()
        return Response({"message": "Task started"})


class ImportDataAPIView(GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        result = import_countries_and_regions.delay()
        return Response({
            "message": "Import task started",
            "task_id": result.id,
        })
```

### 3.3 URL qo'shish

`apps/common/urls.py` ga:
```python
path("import-data/", ImportDataAPIView.as_view(), name="import-data"),
```

`apps/common/views/__init__.py` ga `ImportDataAPIView` ni import qilish.

### 3.4 Sinab ko'rish
```bash
curl -X POST http://localhost:8000/common/import-data/
```

- Worker logida import natijasi ko'rinadi
- Flower da task success holati ko'rinadi
- Admin panelda Country va Region lar paydo bo'ladi

### 3.5 Task natijasini tekshirish (bonus)

```python
# Django shell orqali
from celery.result import AsyncResult
result = AsyncResult("task-id-from-response")
print(result.status)   # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)   # "Imported 195 countries and 3500 regions"
```

---

## 4-qism: 2-Task — Lesson rating recalculation (25 min)

**Maqsad:** `LessonRate` jadvaldagi barcha baholardan `Lesson.current_rating` ni qayta hisoblash. Real loyihalarda bunday denormalized fieldlarni periodic yangilab turish keng tarqalgan pattern.

### 4.1 Task yozish

`apps/interactions/tasks.py` (yangi fayl):

```python
from celery import shared_task
from django.db.models import Avg


@shared_task
def recalculate_lesson_ratings():
    """Recalculate current_rating for all lessons based on LessonRate entries."""
    from apps.courses.models import Lesson
    from apps.interactions.models import LessonRate

    lessons = Lesson.objects.all()
    updated_count = 0

    for lesson in lessons:
        avg = LessonRate.objects.filter(lesson=lesson).aggregate(
            avg_rating=Avg("star_count")
        )["avg_rating"]

        new_rating = round(avg, 2) if avg else 0.0

        if lesson.current_rating != new_rating:
            lesson.current_rating = new_rating
            lesson.save(update_fields=["current_rating"])
            updated_count += 1

    return f"Updated ratings for {updated_count} lessons"
```

### 4.2 Sinab ko'rish (manual chaqirish)

Django shell orqali:
```python
from apps.interactions.tasks import recalculate_lesson_ratings
result = recalculate_lesson_ratings.delay()
print(result.get(timeout=10))
```

---

## 5-qism: Celery Beat — Periodic Tasks (30 min)

### 5.1 django-celery-beat o'rnatish

```bash
uv add django-celery-beat
```

### 5.2 Settings ga qo'shish

`config/settings.py`:
```python
EXTERNAL_APPS = [
    ...
    "django_celery_beat",
]
```

### 5.3 Migrate
```bash
uv run python manage.py migrate
```

Bu 4 ta jadval yaratadi: `PeriodicTask`, `IntervalSchedule`, `CrontabSchedule`, `SolarSchedule`.

### 5.4 Beat scheduler sozlash

`config/settings.py` ga qo'shish:
```python
# Celery Beat
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

### 5.5 Periodic task yaratish — 2 usul

**A) Settings orqali (code-based):**

`config/settings.py` ga qo'shish:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "recalculate-lesson-ratings-every-hour": {
        "task": "apps.interactions.tasks.recalculate_lesson_ratings",
        "schedule": crontab(minute=0, hour="*/1"),  # Har soatda 1 marta
    },
}
```

**B) Admin panel orqali (DB-based) — dars davomida ko'rsatish:**

1. Admin panelga kirish (`/admin/`)
2. "Periodic Tasks" bo'limiga o'tish
3. Interval yaratish: har 30 soniyada (demo uchun)
4. Periodic Task yaratish:
   - Name: `Recalculate lesson ratings`
   - Task: `apps.interactions.tasks.recalculate_lesson_ratings`
   - Interval: yuqoridagi interval
   - Enabled: True

### 5.6 Beat ishga tushirish

To'rtinchi terminalda:
```bash
uv run celery -A config beat -l info
```

### 5.7 Hammasi birga ishlayaptimi — tekshirish

4 ta terminal ochiq bo'lishi kerak:
```
Terminal 1: uv run python manage.py runserver          # Django
Terminal 2: uv run celery -A config worker -l info     # Worker
Terminal 3: uv run celery -A config beat -l info       # Beat
Terminal 4: uv run celery -A config flower --port=5555 # Flower
```

- Beat logida `recalculate_lesson_ratings` task yuborilayotganini ko'rish
- Worker logida task bajarilganini ko'rish
- Flower dashboardda periodic task natijalarini ko'rish

---

## 6-qism: Flower bilan monitoring (15 min)

### Flower dashboardni ko'rib chiqish

`http://localhost:5555` da:

1. **Dashboard** — active workers, task statistics
2. **Tasks** — barcha tasklar ro'yxati, status (SUCCESS/FAILURE/PENDING)
3. **Worker** — har bir worker haqida batafsil info (processed, active, load)
4. **Broker** — Redis queue holati

### Amaliy mashq:
- Import task'ni bir necha marta trigger qiling
- Flower'da task history ko'ring
- Bitta task'ni UUID orqali toping
- Failed task simulatsiya qiling (task ichida xato qiling) — Flower'da FAILURE ko'ring

---

## 7-qism: Yakuniy amaliy mashq (15 min)

Talabalar mustaqil bajaradilar:

1. `apps/notifications/tasks.py` yarating — `cleanup_old_notifications` task:
   - 30 kundan eski notificationlarni o'chiradi
   - Nechta o'chirilganini return qiladi

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def cleanup_old_notifications():
    """Delete notifications older than 30 days."""
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    return f"Deleted {count} old notifications"
```

2. Admin paneldan periodic task sifatida qo'shing — haftada 1 marta ishlasin

---

## Xulosa va takrorlash

| Tushuncha | Qisqacha |
|-----------|----------|
| `@shared_task` | Celery task dekoratori |
| `.delay()` | Taskni async yuborish |
| `.get()` | Natijani kutish (sync) |
| `AsyncResult` | Task holatini tekshirish |
| Celery Worker | Tasklarni bajaruvchi process |
| Celery Beat | Periodic scheduler |
| `django-celery-beat` | Beat + Django admin integratsiya |
| Flower | Real-time monitoring dashboard |

### Uy vazifasi
- `import_countries_and_regions` task'ga progress tracking qo'shing (necha % bajarildi)
- Yangi task yozing: barcha `is_deleted=True` bo'lgan User larni 90 kundan keyin DB dan to'liq o'chirish
- Bu task'ni Celery Beat orqali haftada bir marta ishlaydigan qiling
