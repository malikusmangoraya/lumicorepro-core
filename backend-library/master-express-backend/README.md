# Master Express Backend - Pro Mode

Professional Express.js backend with complete CRUD operations, JWT authentication, PostgreSQL integration, and production-ready middleware.

## Features

✅ **Complete Authentication System**
- User registration & login
- JWT token-based auth
- Password hashing with bcrypt
- Protected routes middleware
- Role-based authorization

✅ **Database Integration**
- PostgreSQL with Sequelize ORM
- Automatic model synchronization
- UUID primary keys
- Timestamps (createdAt, updatedAt)
- Data validation

✅ **Security & Performance**
- Helmet security headers
- CORS configuration
- Rate limiting
- Request compression
- Morgan logging
- Input validation

✅ **API Endpoints**
- `/api/auth/register` - User registration
- `/api/auth/login` - User login
- `/api/auth/me` - Get current user (protected)
- `/api/auth/profile` - Update profile (protected)
- `/api/auth/change-password` - Change password (protected)
- `/api/contact` - Contact form submission
- `/api/newsletter/subscribe` - Newsletter subscription
- `/api/newsletter/unsubscribe` - Newsletter unsubscription
- `/api/health` - Health check

## Quick Start

### Prerequisites
- Node.js 18+
- PostgreSQL 14+

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Edit .env with your database credentials
```

### Database Setup

```sql
-- Create database in PostgreSQL
CREATE DATABASE lumicore_db;
```

### Run Development Server

```bash
npm run dev
```

Server runs on `http://localhost:5000`

### Test API

```bash
# Health check
curl http://localhost:5000/api/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"password123"}'
```

## Project Structure

```
backend/
├── config/
│   └── db.js              # Database configuration
├── controllers/
│   ├── authController.js  # Auth logic
│   ├── contactController.js
│   └── newsletterController.js
├── middleware/
│   ├── auth.js            # JWT verification
│   └── errorHandler.js    # Global error handling
├── models/
│   └── User.js            # User model
├── routes/
│   ├── authRoutes.js
│   ├── contactRoutes.js
│   └── newsletterRoutes.js
├── .env.example
├── package.json
└── server.js              # Entry point
```

## Environment Variables

See `.env.example` for all required variables.

## Production Deployment

```bash
# Build for production
NODE_ENV=production npm start
```

## API Documentation

All endpoints return JSON in this format:

**Success Response:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description"
}
```

## License

MIT