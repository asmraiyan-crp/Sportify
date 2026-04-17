# Database Setup Guide for Sportify Backend

## Database Configuration

The backend uses SQLAlchemy ORM to connect to a PostgreSQL database. Configuration is handled via environment variables.

### Environment Variables

```bash
# PostgreSQL Database URL
# Format: postgresql://username:password@host:port/database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sportify

# Optional: Enable SQL query logging (default: false)
SQL_ECHO=false
```

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sportify"
   export SQL_ECHO="false"
   ```

3. **Create database tables:**
   The tables are automatically created when the Flask app starts. Alternatively, you can manually initialize:
   ```bash
   python3 -c "from database import init_db; init_db()"
   ```

## Database Models

The backend includes 17 SQLAlchemy ORM models:

- **Core**: Sport, League, Team, Player
- **Matches**: GameMatch, PlayerMatchStat
- **Users**: Profile, Review, Comment, PlayerRating
- **Media**: Highlight
- **Events**: FanEvent, EventRegistration
- **Relationships**: UserFollowTeam, UserFollowPlayer, TeamLeague
- **Admin**: SyncLog

## API Test Endpoints

The `/api/v1/test` blueprint provides endpoints to verify database connectivity:

### 1. Health Check
```bash
GET /api/v1/test/health
```
**Response:**
```json
{
  "ok": true,
  "status": "Backend is running"
}
```

### 2. Database Connection Test
```bash
GET /api/v1/test/db-test
```
**Response:**
```json
{
  "ok": true,
  "message": "Database connection successful",
  "data": {
    "sports_count": 3,
    "sports": [
      {
        "sport_id": 1,
        "name": "Football",
        "description": "Association football / soccer",
        "created_at": "2026-04-13T10:00:00+00:00"
      }
    ]
  }
}
```

### 3. Models Information
```bash
GET /api/v1/test/models-info
```
**Response:**
```json
{
  "ok": true,
  "message": "Available models",
  "data": {
    "total_models": 17,
    "models": [
      {
        "class_name": "Sport",
        "table_name": "sport",
        "columns_count": 4,
        "relationships_count": 3
      }
    ]
  }
}
```

## Running the Backend

1. **Start the Flask development server:**
   ```bash
   python3 app.py
   ```

2. **Server runs on:**
   - URL: `http://localhost:5000`
   - API Base: `http://localhost:5000/api/v1`

3. **Test endpoints:**
   ```bash
   # Health check
   curl http://localhost:5000/api/v1/test/health
   
   # Database test
   curl http://localhost:5000/api/v1/test/db-test
   
   # Models info
   curl http://localhost:5000/api/v1/test/models-info
   ```

## PostgreSQL Setup (macOS/Linux/Windows)

### Using Docker (Recommended)
```bash
# Start PostgreSQL container
docker run --name sportify-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=sportify \
  -p 5432:5432 \
  -d postgres:15

# Verify connection
psql -h localhost -U postgres -d sportify
```

### Manual PostgreSQL Installation

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
createdb sportify
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb sportify
```

**Windows:**
- Download PostgreSQL from https://www.postgresql.org/download/
- Run installer with default settings
- Note: username: `postgres`, password: (set during installation)
- Create database:
  ```
  createdb -U postgres sportify
  ```

## Connecting to the Database

Once PostgreSQL is running, set the environment variable and start the app:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/sportify"
python3 app.py
```

The API will automatically create all tables on startup.

## Troubleshooting

### Connection Refused
- Ensure PostgreSQL is running
- Check `DATABASE_URL` is correct
- Verify PostgreSQL port (default: 5432)

### Table Already Exists
- This is normal - the app checks and skips creation if tables exist

### Permission Denied
- Check PostgreSQL user credentials in `DATABASE_URL`
- Verify user has CREATE permissions

## Next Steps

1. ✅ Database setup complete
2. ✅ API endpoints verified
3. Next: Implement business logic using the ORM models
