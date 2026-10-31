<<<<<<< HEAD
<<<<<<< HEAD
# LearnHub Academy — Single-App Django LMS

This project uses exactly one Django application: `academy`.

## Requirements

- Python 3.11+
- Django 5.2+
- Pillow
- PostgreSQL for production (optional; SQLite is used by default for development)

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create migrations:

```bash
python manage.py makemigrations academy
python manage.py migrate
```

Create administrator:

```bash
python manage.py createsuperuser
```

Run:

```bash
python manage.py runserver
```

Open:

- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Password reset in development

The development configuration uses Django's console email backend. When a password reset is requested, the reset URL appears in the terminal running `runserver`.

For production, configure SMTP environment variables and use a real email backend.

## PostgreSQL

Set:

```text
DB_ENGINE=postgresql
POSTGRES_DB=learning_platform
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Then run:

```bash
python manage.py migrate
```

## Production

Set:

```text
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

Then:

```bash
python manage.py collectstatic
python manage.py check --deploy
```

## Test

```bash
python manage.py test academy
```

## Roles

Public registration allows:

- JAMB
- A-Level
- University
- Tutor

ADMIN is deliberately excluded from public registration. Create an administrator with:

```bash
python manage.py createsuperuser
```

## Course limits

- JAMB: 4
- A-Level: 3
- University: configurable in Django Admin → Platform Settings

## Security model

The backend enforces:

- authenticated access
- role-based dashboard access
- registered-course access
- registered-course lesson access
- tutor ownership of courses and lessons
- server-side course limits
- server-side course category validation
- CSRF protection
- Django password hashing
- file extension and size validation
- suspended-account blocking

There is no payment functionality.
=======
# dcdracademyweb
>>>>>>> 9a25d01dd3c3e07ee68e0b68b6594ca6b47ee171
=======
# dcdr
>>>>>>> 682bb32ddbd2b59092212b94443241b4b53d56fc
