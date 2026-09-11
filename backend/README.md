# LumiCorePro Backend API

Complete full-stack backend API server with authentication, e-commerce, payments, analytics, real-time notifications, and more.

## Features

- ✅ **Authentication & Authorization** - JWT-based auth with refresh tokens
- ✅ **User Management** - Complete CRUD operations with roles (user, admin, vendor)
- ✅ **E-commerce** - Products, orders, cart management
- ✅ **Payment Processing** - Stripe integration with webhooks
- ✅ **File Upload** - Multer with image optimization (Sharp)
- ✅ **Real-time Notifications** - WebSocket (Socket.io)
- ✅ **Search** - Elasticsearch integration
- ✅ **Analytics** - Business intelligence & reporting
- ✅ **Email Service** - Nodemailer for transactional emails
- ✅ **Caching** - Redis for performance optimization
- ✅ **API Documentation** - Swagger/OpenAPI 3.0
- ✅ **Security** - Helmet, CORS, rate limiting, input validation
- ✅ **Logging** - Winston with Morgan
- ✅ **Testing** - Jest & Supertest setup

## Tech Stack

- **Runtime:** Node.js with ES Modules
- **Framework:** Express.js
- **Database:** MongoDB with Mongoose ODM
- **Cache:** Redis
- **Search:** Elasticsearch
- **Payments:** Stripe
- **WebSocket:** Socket.io
- **Documentation:** Swagger UI
- **Testing:** Jest, Supertest

## Prerequisites

- Node.js >= 18.x
- MongoDB >= 5.x
- Redis >= 6.x (optional for caching)
- Elasticsearch >= 7.x (optional for search)

## Installation

1. **Clone and navigate to backend directory:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start MongoDB and Redis:**
```bash
# MongoDB (if using local instance)
mongod

# Redis (if using local instance)
redis-server
```

## Running the Server

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

### Seed Database (Optional)
```bash
npm run seed
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Users
- `GET /api/users` - Get all users (admin only)
- `GET /api/users/:id` - Get user by ID
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user (admin only)

### Products
- `GET /api/products` - Get all products
- `GET /api/products/:id` - Get product by ID
- `POST /api/products` - Create product (vendor/admin)
- `PUT /api/products/:id` - Update product (vendor/admin)
- `DELETE /api/products/:id` - Delete product (vendor/admin)
- `GET /api/products/search` - Search products
- `GET /api/products/categories` - Get all categories

### Orders
- `GET /api/orders` - Get user orders
- `GET /api/orders/:id` - Get order by ID
- `POST /api/orders` - Create new order
- `PATCH /api/orders/:id/status` - Update order status (admin/vendor)

### Payments
- `POST /api/payments/create-intent` - Create payment intent
- `POST /api/payments/webhook` - Stripe webhook handler
- `GET /api/payments/history` - Get payment history

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard stats
- `GET /api/analytics/reports` - Generate reports
- `GET /api/analytics/charts/:type` - Get chart data

### Uploads
- `POST /api/uploads/single` - Upload single file
- `POST /api/uploads/multiple` - Upload multiple files
- `DELETE /api/uploads/:filename` - Delete uploaded file

### Search
- `GET /api/search` - Global search across products, users, etc.
- `POST /api/search/index` - Reindex search data (admin)

### Notifications
- `GET /api/notifications` - Get user notifications
- `POST /api/notifications/mark-read` - Mark notifications as read
- `DELETE /api/notifications/:id` - Delete notification

## API Documentation

Access interactive API documentation at:
```
http://localhost:5000/api-docs
```

## Testing

Run all tests:
```bash
npm test
```

Run tests with coverage:
```bash
npm test -- --coverage
```

## Project Structure

```
backend/
├── config/           # Configuration files
│   ├── database.js   # MongoDB connection
│   ├── swagger.js    # Swagger configuration
│   └── redis.js      # Redis configuration
├── models/           # Mongoose models
│   ├── User.js
│   ├── Product.js
│   ├── Order.js
│   ├── Payment.js
│   ├── Notification.js
│   └── Analytics.js
├── routes/           # API routes
│   ├── auth.routes.js
│   ├── user.routes.js
│   ├── product.routes.js
│   ├── order.routes.js
│   ├── payment.routes.js
│   ├── analytics.routes.js
│   ├── upload.routes.js
│   ├── search.routes.js
│   └── notification.routes.js
├── controllers/      # Route controllers
│   ├── auth.controller.js
│   ├── user.controller.js
│   ├── product.controller.js
│   ├── order.controller.js
│   ├── payment.controller.js
│   ├── analytics.controller.js
│   ├── upload.controller.js
│   ├── search.controller.js
│   └── notification.controller.js
├── services/         # Business logic
│   ├── email.service.js
│   ├── payment.service.js
│   ├── upload.service.js
│   ├── search.service.js
│   └── analytics.service.js
├── middleware/       # Custom middleware
│   ├── errorHandler.js
│   ├── auth.js
│   ├── validation.js
│   └── upload.js
├── utils/            # Utility functions
│   ├── logger.js
│   ├── helpers.js
│   └── validators.js
├── tests/            # Test files
├── scripts/          # Utility scripts
│   └── seed.js
├── uploads/          # Uploaded files (gitignored)
├── logs/             # Log files (gitignored)
├── server.js         # Main server file
├── package.json
├── .env.example
└── README.md
```

## Environment Variables

See `.env.example` for all required environment variables.

Key variables:
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `STRIPE_SECRET_KEY` - Stripe secret key for payments
- `EMAIL_*` - Email service configuration
- `REDIS_URL` - Redis connection URL (optional)
- `ELASTICSEARCH_HOST` - Elasticsearch host (optional)

## Security Features

- **Helmet** - HTTP security headers
- **CORS** - Cross-Origin Resource Sharing
- **Rate Limiting** - Prevent abuse
- **Input Validation** - express-validator
- **Password Hashing** - bcryptjs
- **JWT Authentication** - Secure token-based auth
- **XSS Protection** - Content Security Policy
- **SQL Injection Prevention** - Mongoose ODM

## Deployment

### Docker (Recommended)
```bash
docker-compose up -d
```

### Manual Deployment
1. Set `NODE_ENV=production`
2. Configure production database
3. Set up SSL/TLS certificates
4. Configure reverse proxy (Nginx)
5. Set up process manager (PM2)

```bash
pm2 start server.js --name lumicorepro-backend
```

## Monitoring & Logging

- Logs are stored in `logs/` directory
- Use Winston for structured logging
- Morgan for HTTP request logging
- Monitor with tools like PM2, New Relic, or Datadog

## Contributing

1. Follow existing code patterns
2. Write tests for new features
3. Update API documentation
4. Ensure ESLint passes

## License

MIT

## Support

For issues and questions:
- Email: support@lumicorepro.com
- Documentation: http://localhost:5000/api-docs
