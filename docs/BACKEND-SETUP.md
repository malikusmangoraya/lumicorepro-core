# LumiCorePro Backend Setup Guide

## Full-Stack Features Overview

This backend provides comprehensive features for international market standards:

### ✅ Core Features
- **Authentication & Authorization**: JWT-based auth with OAuth support
- **User Management**: Roles, permissions, profiles, preferences
- **Product Management**: E-commerce product catalog with categories
- **Order Management**: Complete order lifecycle
- **Payment Processing**: Stripe integration with webhook support
- **File Upload System**: Secure file uploads with image optimization
- **Real-time Notifications**: WebSocket-based notifications
- **Search Engine**: Elasticsearch-powered full-text search
- **Analytics & Reporting**: Business intelligence dashboard
- **Email Service**: Transactional emails with templates
- **API Documentation**: Swagger/OpenAPI auto-generated docs
- **Rate Limiting**: DDoS protection with IP-based limits
- **Caching Layer**: Redis for performance optimization
- **Security**: Helmet, CORS, input validation, SQL injection protection

## Prerequisites

- Node.js >= 18.x
- MongoDB >= 6.x
- Redis >= 7.x
- Elasticsearch >= 8.x (optional, for advanced search)

## Installation

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
```

### 3. Install Services

#### MongoDB (Local)
```bash
# Windows (using Chocolatey)
choco install mongodb

# macOS
brew install mongodb-community

# Or use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas
```

#### Redis (Local)
```bash
# Windows (using Chocolatey)
choco install redis

# macOS
brew install redis

# Start Redis server
redis-server
```

#### Elasticsearch (Optional - for advanced search)
```bash
# Download from: https://www.elastic.co/downloads/elasticsearch
# Or use Docker:
docker run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:8.12.0
```

### 4. Start Backend Server

```bash
# Development mode with auto-reload
npm run dev

# Production mode
npm start
```

Server will start on `http://localhost:5000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:5000/api-docs
- **Health Check**: http://localhost:5000/api/health

## Project Structure

```
backend/
├── config/
│   ├── database.js          # MongoDB connection
│   ├── swagger.js           # API documentation config
│   └── redis.js             # Redis connection
├── controllers/
│   ├── auth.controller.js   # Authentication logic
│   ├── user.controller.js   # User management
│   ├── product.controller.js # Product operations
│   ├── order.controller.js   # Order processing
│   ├── payment.controller.js # Payment handling
│   ├── analytics.controller.js # Analytics data
│   ├── upload.controller.js  # File uploads
│   ├── search.controller.js  # Search operations
│   └── notification.controller.js # Notifications
├── middleware/
│   ├── auth.js              # JWT verification middleware
│   ├── errorHandler.js      # Error handling middleware
│   ├── validation.js        # Request validation
│   └── upload.js            # Multer file upload config
├── models/
│   ├── User.js              # User schema
│   ├── Product.js           # Product schema
│   ├── Order.js             # Order schema
│   └── Payment.js           # Payment schema
├── routes/
│   ├── auth.routes.js       # /api/auth routes
│   ├── user.routes.js       # /api/users routes
│   ├── product.routes.js    # /api/products routes
│   └── ...                  # Other route files
├── services/
│   ├── email.js             # Email service (Nodemailer)
│   ├── payment.js           # Stripe payment service
│   ├── upload.js            # File upload service
│   ├── search.js            # Elasticsearch service
│   └── analytics.js         # Analytics service
├── utils/
│   ├── logger.js            # Winston logger
│   ├── helpers.js           # Utility functions
│   └── validators.js        # Validation helpers
├── tests/
│   ├── auth.test.js         # Auth tests
│   ├── user.test.js         # User tests
│   └── ...                  # Other test files
├── .env.example             # Environment variables template
├── package.json             # Dependencies
└── server.js                # Main server file
```

## Key Features Implementation

### 1. Authentication System
- JWT tokens with refresh tokens
- Password hashing with bcrypt
- Role-based access control (user, admin, vendor)
- Email verification
- Password reset functionality

### 2. Payment Processing (Stripe)
- One-time payments
- Subscription billing
- Webhook handling for payment events
- Refund processing

### 3. File Upload System
- Image optimization with Sharp
- Cloud storage support (AWS S3 / Cloudinary)
- Virus scanning integration
- File type validation

### 4. Real-time Notifications
- WebSocket connections via Socket.io
- Email notifications
- Push notifications ready

### 5. Search Engine
- Elasticsearch integration
- Full-text search
- Auto-complete suggestions
- Search analytics

### 6. Analytics Dashboard
- User behavior tracking
- Sales analytics
- Product performance metrics
- Custom reports

## Testing

```bash
# Run all tests
npm test

# Run tests with coverage report
npm test -- --coverage

# Run specific test file
npm test -- auth.test.js
```

## Deployment

### Environment Variables for Production

```bash
NODE_ENV=production
PORT=5000
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/lumicorepro
JWT_SECRET=<generate-random-64-char-string>
REDIS_URL=redis://<your-redis-url>
STRIPE_SECRET_KEY=sk_live_<your-key>
EMAIL_USER=<your-email>
EMAIL_PASS=<your-app-password>
```

### Docker Deployment

```bash
# Build Docker image
docker build -t lumicorepro-backend .

# Run container
docker run -p 5000:5000 --env-file .env lumicorepro-backend
```

### PM2 Process Manager

```bash
# Install PM2 globally
npm install -g pm2

# Start application
pm2 start server.js --name lumicorepro-backend

# Save PM2 process list
pm2 save

# Setup startup script
pm2 startup
```

## Security Checklist

- ✅ Helmet.js for HTTP headers security
- ✅ CORS configuration
- ✅ Rate limiting (express-rate-limit)
- ✅ JWT authentication
- ✅ Input validation (express-validator)
- ✅ SQL injection protection (Mongoose)
- ✅ XSS protection
- ✅ File upload validation
- ✅ Environment variables for secrets
- ✅ HTTPS in production

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/refresh` - Refresh access token
- `GET  /api/auth/profile` - Get user profile
- `PUT  /api/auth/profile` - Update user profile

### Users
- `GET    /api/users` - Get all users (admin)
- `GET    /api/users/:id` - Get user by ID
- `PUT    /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

### Products
- `GET    /api/products` - Get all products
- `GET    /api/products/:id` - Get product by ID
- `POST   /api/products` - Create product (admin/vendor)
- `PUT    /api/products/:id` - Update product
- `DELETE /api/products/:id` - Delete product

### Orders
- `GET    /api/orders` - Get orders
- `GET    /api/orders/:id` - Get order by ID
- `POST   /api/orders` - Create order
- `PATCH  /api/orders/:id/status` - Update order status

### Payments
- `POST /api/payments/create-intent` - Create payment intent
- `POST /api/payments/webhook` - Stripe webhook handler

### Analytics
- `GET /api/analytics/overview` - Get analytics overview
- `GET /api/analytics/revenue` - Get revenue data
- `GET /api/analytics/users` - Get user analytics

### File Upload
- `POST /api/uploads/single` - Upload single file
- `POST /api/uploads/multiple` - Upload multiple files

### Search
- `GET /api/search/products?q=query` - Search products
- `GET /api/search/suggestions?q=query` - Get search suggestions

### Notifications
- `GET    /api/notifications` - Get user notifications
- `PUT    /api/notifications/:id/read` - Mark as read
- `DELETE /api/notifications/:id` - Delete notification

## Performance Optimization

1. **Redis Caching**: Cache frequently accessed data
2. **Database Indexing**: Index frequently queried fields
3. **Compression**: Gzip compression enabled
4. **Image Optimization**: Sharp library for image processing
5. **Pagination**: Implement pagination on list endpoints
6. **Lazy Loading**: Load models and services on demand

## Monitoring

- Winston logger for application logs
- Morgan for HTTP request logging
- Health check endpoint for uptime monitoring
- Error tracking integration ready (Sentry)

## Support

For issues or questions:
- Email: support@lumicorepro.com
- GitHub Issues: https://github.com/lumicorepro/core/issues
