# 🚀 FXC Bot Looters Platform - Complete Guide

## 📋 Overview

A SaaS platform for automated bot account creation across multiple platforms (DeFi Products, Darino, and more).

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS)
    ↓
Backend (Flask API) - Modular Blueprint Structure
    ↓
Database (Supabase PostgreSQL)
```

---

## 📁 Project Structure

```
fxc-bot-looters/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
│
├── auth/
│   ├── __init__.py
│   └── routes.py              # Login, Signup, Profile
│
├── bots/
│   ├── __init__.py
│   ├── defi.py                # DeFi Products bot
│   ├── darino.py              # Darino bot
│   └── [future_bots].py       # Add more bots easily
│
├── dashboard/
│   ├── __init__.py
│   └── routes.py              # Dashboard, Stats, Search
│
├── database/
│   ├── __init__.py
│   └── supabase_client.py     # Database connection
│
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

---

## 🗄️ Supabase Database Setup

### Step 1: Create Supabase Project
1. Go to [https://supabase.com](https://supabase.com)
2. Create new project
3. Save your `SUPABASE_URL` and `SUPABASE_KEY`

### Step 2: Create Tables

#### Table 1: `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    referral_code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add index for faster queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_referral ON users(referral_code);
```

#### Table 2: `bot_accounts`
```sql
CREATE TABLE bot_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bot_type TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    promo_code TEXT,
    status TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_bot_accounts_user ON bot_accounts(user_id);
CREATE INDEX idx_bot_accounts_bot_type ON bot_accounts(bot_type);
CREATE INDEX idx_bot_accounts_status ON bot_accounts(status);
```

#### Table 3: `bots`
```sql
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    logo_url TEXT,
    website TEXT,
    requires_promo BOOLEAN DEFAULT FALSE,
    promo_format TEXT,
    category TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert initial bots
INSERT INTO bots (name, slug, description, website, requires_promo, promo_format, category) VALUES
('DeFi Products', 'defi', 'Automated account creation for DeFi Products investment platform', 'https://defiproducts.vip', TRUE, '6 digits', 'Finance'),
('Darino', 'darino', 'Automated account creation for Darino task platform', 'https://darino.vip', FALSE, 'Optional', 'Tasks');
```

---

## 🚀 Deployment Steps

### Option 1: Deploy to Render (Recommended)

#### Step 1: Prepare Files
Create `__init__.py` files in each folder:
```bash
# Create empty __init__.py files
touch auth/__init__.py
touch bots/__init__.py
touch dashboard/__init__.py
touch database/__init__.py
```

#### Step 2: Create `.env` File (locally for testing)
```env
SECRET_KEY=your-super-secret-key-change-this
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
PORT=5000
```

#### Step 3: Deploy to Render
1. Push code to GitHub
2. Create new **Web Service** on Render
3. Connect your GitHub repo
4. Set **Start Command**: `gunicorn app:app`
5. Add **Environment Variables**:
   - `SECRET_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
6. Deploy!

---

## 🔌 API Endpoints Reference

### Authentication
```
POST /auth/signup
POST /auth/login
GET  /auth/profile (requires token)
POST /auth/verify
```

### DeFi Bot
```
GET  /bot/defi/info
POST /bot/defi/create (requires token)
GET  /bot/defi/accounts (requires token)
```

### Darino Bot
```
GET  /bot/darino/info
POST /bot/darino/create (requires token)
GET  /bot/darino/accounts (requires token)
```

### Dashboard
```
GET  /dashboard/bots
GET  /dashboard/stats (requires token)
GET  /dashboard/accounts (requires token)
GET  /dashboard/referral (requires token)
GET  /dashboard/search?q=keyword&category=Finance
```

---

## 📝 API Request Examples

### 1. Signup
```javascript
fetch('https://your-api.onrender.com/auth/signup', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
})
```

### 2. Create DeFi Accounts
```javascript
fetch('https://your-api.onrender.com/bot/defi/create', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_JWT_TOKEN'
    },
    body: JSON.stringify({
        promo_code: '791580',
        count: 5
    })
})
```

### 3. Get Dashboard Stats
```javascript
fetch('https://your-api.onrender.com/dashboard/stats', {
    headers: {
        'Authorization': 'Bearer YOUR_JWT_TOKEN'
    }
})
```

---

## ➕ Adding New Bots (Easy!)

### Step 1: Create New Bot File
Create `bots/newbot.py`:

```python
from flask import Blueprint, request, jsonify
# ... your bot logic

newbot_bp = Blueprint('newbot', __name__)

@newbot_bp.route("/create", methods=["POST"])
def create_accounts():
    # Your account creation logic
    pass
```

### Step 2: Register Blueprint
In `app.py`:
```python
from bots.newbot import newbot_bp
app.register_blueprint(newbot_bp, url_prefix='/bot/newbot')
```

### Step 3: Add to Database
```sql
INSERT INTO bots (name, slug, description, website, category) 
VALUES ('New Bot', 'newbot', 'Description', 'https://website.com', 'Category');
```

That's it! Your new bot is live! 🎉

---

## 🎨 Frontend Integration

Update `script.js` API_BASE:
```javascript
const API_BASE = 'https://your-api.onrender.com';
```

---

## 🔒 Security Best Practices

1. **Always use HTTPS** in production
2. **Never commit** `.env` file to GitHub
3. **Use strong SECRET_KEY** (generate with `openssl rand -hex 32`)
4. **Validate all inputs** on backend
5. **Use JWT tokens** for authentication
6. **Rate limit** API endpoints (add Flask-Limiter)

---

## 🧪 Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your-url"
export SUPABASE_KEY="your-key"
export SECRET_KEY="your-secret"

# Run locally
python app.py

# API will run at http://localhost:5000
```

---

## 📊 Monitoring & Logs

- Check Render logs for errors
- Monitor Supabase dashboard for database queries
- Add logging for important events

---

## 🚀 Future Enhancements

- [ ] Add rate limiting
- [ ] Add email verification
- [ ] Add payment integration (for premium features)
- [ ] Add admin dashboard
- [ ] Add webhook notifications
- [ ] Add account analytics
- [ ] Add batch export (CSV/JSON)

---

## 🆘 Troubleshooting

### Issue: "Module not found"
**Solution**: Make sure all `__init__.py` files exist in each folder

### Issue: "Supabase connection failed"
**Solution**: Check your `SUPABASE_URL` and `SUPABASE_KEY` in environment variables

### Issue: "CORS error"
**Solution**: Make sure `flask-cors` is installed and `CORS(app)` is in `app.py`

---

## 📞 Support

- Check Render logs for backend errors
- Check browser console for frontend errors
- Verify Supabase connection in dashboard

---

## 🎯 Summary

You now have:
- ✅ **Modular Flask API** - Easy to add new bots
- ✅ **Authentication System** - JWT-based login
- ✅ **Database Integration** - Supabase PostgreSQL
- ✅ **Multiple Bots** - DeFi, Darino (add more anytime)
- ✅ **Dashboard** - Stats, search, accounts
- ✅ **Scalable Architecture** - Ready for growth

**Just add `darino.py`, `newbot.py`, etc., and register the blueprint!** 🚀
