# API Reference

Base URL: `http://localhost:5000/api` (Dev) / `https://api.lumicorepro.com/api` (Prod)
Interactive Swagger UI: `http://localhost:5000/api-docs`

## Authentication Header

Protected endpoints require a JWT Bearer token:

```http
Authorization: Bearer <JWT_TOKEN>
```

Standard response envelope:

```
{ success, status, message, data, timestamp }
```

---

## 1. Authentication Endpoints (`/api/auth`)

### Register User

- **POST** `/auth/register`
- **Body**:
  ```json
  {
    "name": "Alex Johnson",
    "email": "alex@example.com",
    "password": "Password123!",
    "role": "user"
  }
  ```
- **Response** `(201 Created)`:
  ```json
  {
    "success": true,
    "token": "eyJhbGciOi...",
    "user": { "id": "60d...", "name": "Alex Johnson", "email": "alex@example.com" }
  }
  ```

### Login User

- **POST** `/auth/login`
- **Body**:
  ```json
  { "email": "alex@example.com", "password": "Password123!" }
  ```

### 2FA OTP Request & Verification

- **POST** `/auth/2fa/send-otp` (Protected) — Sends 6-digit code to email
- **POST** `/auth/2fa/verify-otp` (Protected)
  ```json
  { "otp": "492817" }
  ```

---

## 2. Products (`/api/products`)

### List Products with Filtering & Pagination

- **GET** `/products?page=1&limit=12&category=Audio&sort=price-asc&minPrice=50&maxPrice=300`
- **Response** `(200 OK)`:
  ```json
  {
    "success": true,
    "count": 12,
    "total": 45,
    "pagination": { "page": 1, "limit": 12, "pages": 4 },
    "data": [
      {
        "_id": "60d...",
        "title": "LumiCore SoundPro ANC Headphones",
        "price": 249.99,
        "stock": 45,
        "rating": 4.8
      }
    ]
  }
  ```

### Get Single Product

- **GET** `/products/:id` (Supports MongoDB ObjectId or slug)

### Create Product (Vendor / Admin)

- **POST** `/products` (Protected)

---

## 3. Orders (`/api/orders`)

### Create Order (Checkout)

- **POST** `/orders` (Protected)
- **Body**:
  ```json
  {
    "items": [
      { "product": "60d...", "quantity": 1, "selectedColor": "Midnight Black" }
    ],
    "shippingAddress": {
      "fullName": "Alex Johnson",
      "street": "100 Silicon Way",
      "city": "San Francisco",
      "state": "CA",
      "zipCode": "94105",
      "country": "USA"
    },
    "paymentMethod": "stripe"
  }
  ```

---

## 4. Payments (`/api/payments`)

### Create Stripe PaymentIntent

- **POST** `/payments/create-intent` (Protected)
  ```json
  { "orderId": "60d...", "amount": 249.99, "currency": "usd" }
  ```

### Confirm Payment

- **POST** `/payments/confirm` (Protected)
  ```json
  { "paymentIntentId": "pi_3P...", "orderId": "60d..." }
  ```

### Download Order Invoice

- **GET** `/payments/invoice/:orderId` (Protected) → Returns printable HTML/PDF invoice

---

## 5. Analytics (`/api/analytics`)

- **GET** `/analytics/dashboard` — KPIs (revenue, total orders, conversion rate)
- **GET** `/analytics/sales?days=30` — Sales timeline aggregation
- **GET** `/analytics/top-products` — Bestselling products

---

## 6. Health & System Metrics (`/api/health`)

- **GET** `/health` — Basic uptime check
- **GET** `/health/detailed` — Detailed database status, heap memory, CPU load, and system health