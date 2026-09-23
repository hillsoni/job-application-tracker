# Job Application Tracker

A small Django project I built to track job applications across different
hiring stages. It has a REST API with token auth, Redis caching, Celery
for background tasks, and a basic HTML dashboard.

Stack: Python 3.13, Django 6.1, Django REST Framework, Celery, Redis, MySQL 8.4+.

---

## Running with Docker (easiest way)

If you have Docker and Docker Compose installed, this is all you need:

```bash
git clone https://github.com/hillsoni/job-application-tracker.git
cd job-application-tracker

cp .env.example .env
# open .env and set your SECRET_KEY, DB_PASSWORD, etc.

docker-compose up --build
```

That spins up MySQL, Redis, runs migrations, starts the Django server, and
starts the Celery worker — all in one go.

Once it's up:
- Dashboard → http://127.0.0.1:8000/dashboard/
- Admin panel → http://127.0.0.1:8000/admin/
- API → http://127.0.0.1:8000/api/applications/

You'll want a superuser to log in. In a separate terminal (make sure to run migrate first if the container is still booting):

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## Running manually

If you'd rather not use Docker, you'll need Python 3.13, MySQL 8.4+, and Redis
installed locally. Then:

```bash
git clone https://github.com/hillsoni/job-application-tracker.git
cd job-application-tracker

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Environment

```bash
cp .env.example .env
```

Fill in `.env` — the important ones for manual setup:

```
SECRET_KEY=<generate one below>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=mysql://<user>:<password>@localhost:3306/job_tracker_db
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Database

```sql
CREATE DATABASE job_tracker_db;
```

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Redis

**Linux:**
```bash
sudo apt install redis-server
sudo service redis-server start
```

**Windows** — Redis doesn't run natively on Windows, use WSL:
```bash
wsl --install   # skip if you already have WSL
# then inside WSL:
sudo apt install redis-server
sudo service redis-server start
```

Quick check:
```bash
redis-cli ping   # should print PONG
```

### Starting everything

You need three terminals running at the same time:

```bash
# terminal 1 — Django
python manage.py runserver

# terminal 2 — Celery (Windows needs --pool=solo)
celery -A config worker -l info --pool=solo

# macOS/Linux
celery -A config worker -l info
```

---

## API

Every request needs a token. Get one first:

```bash
curl -X POST http://127.0.0.1:8000/api/auth-token/ \
  -d "username=<user>&password=<pass>"
# returns {"token": "abc123..."}
```

From here on, add `-H "Authorization: Token <token>"` to every request.

**List your applications:**
```bash
curl http://127.0.0.1:8000/api/applications/ \
  -H "Authorization: Token <token>"
```

**Filter by status:**
```bash
curl "http://127.0.0.1:8000/api/applications/?status=Interview" \
  -H "Authorization: Token <token>"
```

**Add a new one:**
```bash
curl -X POST http://127.0.0.1:8000/api/applications/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "company_name": "Logieagle",
        "role": "Python Engineer",
        "status": "Applied",
        "applied_date": "2026-09-20",
        "notes": "LinkedIn"
      }'
```

**Get a single one:**
```bash
curl http://127.0.0.1:8000/api/applications/<id>/ \
  -H "Authorization: Token <token>"
```

**Update the status** (this triggers the Celery notification and creates a status log entry):
```bash
curl -X PATCH http://127.0.0.1:8000/api/applications/<id>/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "Interview"}'
```

**Delete:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/applications/<id>/ \
  -H "Authorization: Token <token>"
```

**Stats summary (cached):**
```bash
curl http://127.0.0.1:8000/api/applications/dashboard_stats/ \
  -H "Authorization: Token <token>"
```

---

## A few things worth knowing

**Caching** — the application list and status stats are cached per user for
5 minutes using Redis. Cache keys are `applications_user_{id}` and
`dashboard_stats_user_{id}`. Any create, update, or delete wipes both keys
so the next request always gets fresh data.

**Status change signals** — The prompt explicitly required using `post_save`. 
To achieve this safely and detect changes without falsely triggering on every save, 
I added an `__init__` override to the `JobApplication` model to track the original 
status when the row is loaded from the DB. The `post_save` signal then compares against this tracked state.

**User scoping** — every API query is filtered by `request.user` under the
hood, so there's no way for one account to see another's applications.

**Django Version** — The requested Django 4.x, but also mandated Python 3.13. Since Django 4.x does not officially support Python 3.13 (which causes native database driver compilation issues), I upgraded the project to Django 6.1 (which has full 3.13 support) to ensure a stable and bug-free environment.

**Docker Port Conflicts** — The `docker-compose.yml` maps MySQL to port `3307` on the host to avoid conflicting with any local MySQL servers you might already have running on port `3306`. If your port `3306` is free, you can safely change this mapping back to `"3306:3306"` in the compose file.

---

## Project structure

```
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── templates/
│   └── registration/
│       └── login.html
├── tracker/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── middleware.py
│   ├── tasks.py
│   ├── signals.py
│   ├── admin.py
│   └── templates/tracker/
│       ├── dashboard.html
│       └── form.html
└── config/
    ├── settings.py
    ├── celery.py
    └── urls.py
```