# OutdoorCamp Backend API

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /app/backend
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file with your credentials:
```env
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=7200
```

### 3. Run Server

**Development:**
```bash
python server.py
```

**Production (with Uvicorn):**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001
```

**With Supervisor (recommended):**
```bash
sudo supervisorctl restart backend
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### Products (Requires Auth)
- `GET /api/products` - Get all products
- `GET /api/products/{id}` - Get product by ID
- `POST /api/products` - Create product (Admin only)
- `PUT /api/products/{id}` - Update product (Admin only)
- `DELETE /api/products/{id}` - Delete product (Admin only)

### Bookings (Requires Auth)
- `GET /api/bookings` - Get bookings (All for admin, own for users)
- `GET /api/bookings/{id}` - Get booking by ID
- `POST /api/bookings` - Create booking
- `PUT /api/bookings/{id}` - Update booking
- `DELETE /api/bookings/{id}` - Cancel booking

### Payments (Requires Auth)
- `GET /api/payments` - Get payments (All for admin, own for users)
- `GET /api/payments/{id}` - Get payment by ID
- `POST /api/payments` - Create payment
- `PUT /api/payments/{id}` - Update payment status (Admin only)
- `DELETE /api/payments/{id}` - Delete payment (Admin only)

### Users (Admin Only)
- `GET /api/users` - Get all users
- `GET /api/users/{id}` - Get user by ID
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### Reports (Admin Only)
- `GET /api/reports/stats` - Get statistics
- `GET /api/reports/revenue` - Get revenue data
- `GET /api/reports/bookings-trend` - Get bookings trend
- `GET /api/reports/popular-products` - Get popular products

## 🔐 Authentication

All protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## 👤 Default Admin Account

```
Email: admin@outdoorcamp.id
Password: password123
```

## 🗄️ Database Collections

### users
- email (unique)
- name
- password (hashed)
- role (admin/user)
- created_at

### products
- name
- description
- category
- price
- stock
- image
- status
- created_at

### bookings
- user_id
- product_id
- start_date
- end_date
- quantity
- total_price
- status
- notes
- created_at

### payments
- booking_id
- amount
- method
- status
- transaction_id
- notes
- created_at

## 🚢 Railway Deployment

1. **Connect Repository to Railway**
2. **Set Environment Variables in Railway:**
   - `MONGO_URI`
   - `JWT_SECRET`
   - `JWT_ALGORITHM`
   - `JWT_EXPIRATION`

3. **Configure Railway Start Command:**
   ```
   cd backend && pip install -r requirements.txt && uvicorn server:app --host 0.0.0.0 --port $PORT
   ```

4. **Configure Railway Build Command:**
   ```
   pip install -r backend/requirements.txt
   ```

## 📝 Notes

- MongoDB ObjectID is not used for primary keys to avoid JSON serialization issues
- All passwords are hashed using bcrypt
- JWT tokens expire after 2 hours (configurable)
- CORS is enabled for all origins (adjust for production)
- Automatic indexes are created on startup
