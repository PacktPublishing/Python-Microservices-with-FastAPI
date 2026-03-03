# Babysitter Catalog API

A DDD-inspired CRUD microservice for managing babysitter profiles, built with
**FastAPI**, **Beanie** (async ODM), and **MongoDB**.

---

## Project structure

```
sitters-catalog/
├── main.py                          # Root re-export (fastapi dev entry)
├── pyproject.toml
├── .env.example
│
└── babysitter_catalog/
    ├── main.py                      # App factory + lifespan
    ├── config.py                    # pydantic-settings
    │
    ├── domain/
    │   ├── babysitter.py            # BabysitterDocument (Beanie model)
    │   └── value_objects.py         # Location, ContactInfo, AvailabilitySlot
    │
    ├── application/
    │   ├── dtos.py                  # Create / Update / Response / Search DTOs
    │   └── babysitter_service.py    # Use-case methods
    │
    ├── infrastructure/
    │   └── mongo_repository.py      # Beanie query wrappers
    │
    └── presentation/
        └── babysitter_router.py     # FastAPI APIRouter — all CRUD endpoints
```

---

## Setup

### 1. Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A running MongoDB instance (local or Atlas)

### 2. Clone & install

```bash
git clone <repo-url>
cd sitters-catalog

# with uv
uv sync

# or with pip
pip install -e .
```

### 3. Configure environment

```bash
cp .env.example .env
# edit .env and set MONGO_URI to your connection string
```

---

## Running

### Development (auto-reload)

```bash
fastapi dev
# or explicitly:
fastapi dev babysitter_catalog/main.py
```

### Production

```bash
fastapi run
# or with uvicorn directly:
uvicorn babysitter_catalog.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Interactive docs are available at `http://localhost:8000/docs`.

---

## API endpoints

| Method | Path                              | Description                        |
|--------|-----------------------------------|------------------------------------|
| GET    | /health                           | Health check                       |
| POST   | /api/v1/babysitters/              | Create a babysitter                |
| GET    | /api/v1/babysitters/              | List / search babysitters          |
| GET    | /api/v1/babysitters/featured      | Top 5 by experience                |
| GET    | /api/v1/babysitters/{id}          | Get by ID                          |
| PUT    | /api/v1/babysitters/{id}          | Full update                        |
| PATCH  | /api/v1/babysitters/{id}          | Partial update                     |
| DELETE | /api/v1/babysitters/{id}          | Hard delete                        |
| POST   | /api/v1/babysitters/{id}/deactivate | Soft-delete (is_active=False)    |

---

## Sample curl commands

> Replace `BASE=http://localhost:8000` and `ID=<objectid>` as needed.

### Create a babysitter

```bash
curl -s -X POST "$BASE/api/v1/babysitters/" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alice",
    "last_name": "Dupont",
    "age": 28,
    "bio": "Experienced nanny with a love for creative play.",
    "hourly_rate": 18.50,
    "years_of_experience": 5,
    "languages": ["English", "French"],
    "certifications": ["First Aid", "CPR"],
    "availability": [
      {"day": "Monday", "from_hour": 8, "to_hour": 18},
      {"day": "Wednesday", "from_hour": 8, "to_hour": 18}
    ],
    "contact": {"email": "alice@example.com", "phone": "+33612345678"},
    "location": {"city": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522}
  }' | jq
```

### List all active babysitters (default page)

```bash
curl -s "$BASE/api/v1/babysitters/" | jq
```

### Search with filters

```bash
curl -s "$BASE/api/v1/babysitters/?city=Paris&min_rate=15&language=French&limit=10" | jq
```

### Get featured (top 5 by experience)

```bash
curl -s "$BASE/api/v1/babysitters/featured" | jq
```

### Get by ID

```bash
curl -s "$BASE/api/v1/babysitters/$ID" | jq
```

### Full update (PUT)

```bash
curl -s -X PUT "$BASE/api/v1/babysitters/$ID" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alice",
    "last_name": "Dupont",
    "age": 29,
    "hourly_rate": 20.00,
    "years_of_experience": 6,
    "languages": ["English", "French", "Spanish"],
    "certifications": ["First Aid"],
    "availability": [],
    "contact": {"email": "alice@example.com"},
    "location": {"city": "Lyon", "country": "France"}
  }' | jq
```

### Partial update (PATCH)

```bash
curl -s -X PATCH "$BASE/api/v1/babysitters/$ID" \
  -H "Content-Type: application/json" \
  -d '{"hourly_rate": 22.00, "bio": "Updated bio."}' | jq
```

### Soft-delete (deactivate)

```bash
curl -s -X POST "$BASE/api/v1/babysitters/$ID/deactivate" | jq
```

### Hard delete

```bash
curl -s -X DELETE "$BASE/api/v1/babysitters/$ID" -w "%{http_code}"
# returns 204 No Content
```

---

## MongoDB index recommendations

Run these in `mongosh` (or via a migration script) for optimal query performance:

```js
use babysitter_catalog

// Compound index for the most common search pattern
db.babysitters.createIndex(
  { "location.city": 1, "hourly_rate": 1, "is_active": 1 },
  { name: "idx_city_rate_active" }
)

// Language array index (multikey)
db.babysitters.createIndex(
  { languages: 1 },
  { name: "idx_languages" }
)

// Experience descending — powers the /featured endpoint
db.babysitters.createIndex(
  { years_of_experience: -1, is_active: 1 },
  { name: "idx_experience_active" }
)

// Unique email index
db.babysitters.createIndex(
  { "contact.email": 1 },
  { unique: true, name: "idx_email_unique" }
)

// Audit / time-range queries
db.babysitters.createIndex(
  { created_at: -1 },
  { name: "idx_created_at" }
)
```
