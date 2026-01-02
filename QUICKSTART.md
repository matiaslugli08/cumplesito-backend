# Backend Quick Start Guide

## 🚀 Fast Setup (5 minutes)

### 1. Database Setup

Create the PostgreSQL database:

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE wishlist_db;

# Exit
\q
```

### 2. Environment Configuration

```bash
cd backend

# Copy example env file
cp .env.example .env

# Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edit `.env` and add your configuration:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/wishlist_db
SECRET_KEY=paste-generated-key-here
```

### 3. Install Dependencies

**Option A: Using the setup script**
```bash
chmod +x setup.sh
./setup.sh
```

**Option B: Manual installation**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the Server

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the server
uvicorn app.main:app --reload
```

Server will be available at: **http://localhost:8000**

### 5. Test the API

Visit the interactive documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📋 What I Need From You

To complete the setup, please provide:

1. **PostgreSQL Connection Details:**
   - Username (default: `postgres`)
   - Password
   - Host (default: `localhost`)
   - Port (default: `5432`)
   - Database name (recommended: `wishlist_db`)

2. **CORS Configuration:**
   - Frontend URL (default: `http://localhost:3000`)

---

## 🧪 Quick Test

Once the server is running, test it:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

---

## 🔧 Running Both Frontend and Backend

### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```
**Running on:** http://localhost:8000

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```
**Running on:** http://localhost:3000

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings and env vars
│   ├── database.py       # DB connection
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── routers/          # API endpoints
│   └── utils/            # Auth & dependencies
├── .env                  # Your config (create this)
├── .env.example          # Template
├── requirements.txt      # Python packages
└── README.md             # Full documentation
```

---

## 🔒 Security Notes

- Never commit `.env` file (it's in `.gitignore`)
- Always use a strong `SECRET_KEY` in production
- Change default PostgreSQL password
- Use HTTPS in production

---

## ❓ Troubleshooting

### "Module not found" error
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "Could not connect to database" error
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `.env`
- Test connection: `psql -U postgres -d wishlist_db`

### Port 8000 already in use
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

---

## 📞 Ready to Go?

Once you provide the database credentials, I can help you:
1. Create the `.env` file with your settings
2. Initialize the database
3. Test the endpoints
4. Connect the frontend to the backend

**What are your PostgreSQL credentials?**
