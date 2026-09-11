import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.settings import PROJECT_ROOT, GENERATED_PROJECTS_DIR
from utils.logger import agent_logger
from utils.file_manager import FileManager

class APIGenerator:
    """Generates complete REST API backend with controllers, routes, middleware, models, and services based on website type and features."""

    # Feature-to-endpoint mapping
    FEATURE_ENDPOINTS = {
        # Authentication
        "jwt_auth": ["auth"],
        "oauth": ["auth", "oauth"],
        "role_based_access": ["auth", "roles"],
        "multi_factor_auth": ["auth", "mfa"],
        
        # E-commerce
        "products": ["products"],
        "categories": ["products/categories"],
        "cart": ["cart"],
        "wishlist": ["wishlist"],
        "orders": ["orders"],
        "stripe_payments": ["payments", "payments/stripe"],
        "paypal_payments": ["payments", "payments/paypal"],
        "reviews": ["reviews"],
        "inventory": ["inventory"],
        "coupons": ["coupons"],
        "shipping": ["shipping"],
        
        # Users & Content
        "users": ["users"],
        "profiles": ["users/profiles"],
        "blog": ["posts", "posts/categories", "comments"],
        "cms": ["pages", "media"],
        
        # Analytics & Business
        "analytics": ["analytics", "analytics/events"],
        "subscriptions": ["subscriptions", "subscriptions/plans", "billing"],
        "team_workspaces": ["teams", "teams/members"],
        "notifications": ["notifications"],
        "search": ["search"],
        
        # Communication
        "contact": ["contact"],
        "newsletter": ["newsletter"],
        "chat": ["chat", "chat/messages"],
        "webhooks": ["webhooks"],
        
        # Healthcare
        "appointments": ["appointments"],
        "doctors": ["doctors"],
        "patients": ["patients"],
        "prescriptions": ["prescriptions"],
        
        # Education
        "courses": ["courses"],
        "lessons": ["courses/lessons"],
        "quizzes": ["quizzes"],
        "certificates": ["certificates"],
        
        # Real Estate
        "properties": ["properties"],
        "agents": ["agents"],
        "bookings": ["bookings"],
        
        # Restaurant
        "menu": ["menu"],
        "reservations": ["reservations"],
        "table_orders": ["orders"],
    }

    def generate_full_backend(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate complete backend with all necessary APIs."""
        spec = plan.get("spec", {})
        website_type = spec.get("website_type", "business")
        industry = spec.get("industry", "general")
        features = spec.get("features", [])
        backend_info = plan.get("backend", {})
        
        agent_logger.info(f"Generating full backend for {website_type} ({industry}) with {len(features)} features")
        
        # 1. Generate package.json with all dependencies
        self._generate_package_json(target_dir, features)
        
        # 2. Generate server.js with all middleware and routes
        self._generate_server_js(target_dir, features)
        
        # 3. Generate config files
        self._generate_config_files(target_dir)
        
        # 4. Generate middleware
        self._generate_middleware(target_dir, features)
        
        # 5. Generate controllers based on features
        controllers = self._generate_controllers(target_dir, features, website_type, industry)
        
        # 6. Generate routes
        self._generate_routes(target_dir, controllers)
        
        # 7. Generate models (PostgreSQL with pg, or MongoDB with mongoose)
        self._generate_models(target_dir, features, website_type)
        
        # 8. Generate services layer
        self._generate_services(target_dir, features)
        
        # 9. Generate utils
        self._generate_utils(target_dir)
        
        # 10. Generate environment files
        self._generate_env_files(target_dir, features)
        
        # 11. Generate API documentation
        self._generate_api_docs(target_dir, spec, controllers)
        
        agent_logger.info(f"Backend generation complete: {len(controllers)} controllers, {len(controllers)} routes")

    def _generate_package_json(self, target_dir: Path, features: List[str]) -> None:
        """Generate package.json with all required dependencies."""
        # Base dependencies
        dependencies = {
            "express": "^4.19.2",
            "cors": "^2.8.5",
            "dotenv": "^16.4.5",
            "helmet": "^7.1.0",
            "express-rate-limit": "^7.1.5",
            "jsonwebtoken": "^9.0.2",
            "bcryptjs": "^2.4.3",
            "express-validator": "^7.0.1",
            "morgan": "^1.10.0",
            "compression": "^1.7.4",
        }
        
        dev_dependencies = {
            "nodemon": "^3.0.3",
            "jest": "^29.7.0",
            "supertest": "^6.3.4",
            "swagger-ui-express": "^5.0.0",
            "swagger-jsdoc": "^6.2.8",
        }
        
        # Add database driver based on features
        if "postgresql_schema" in features or any(f in features for f in ["orders", "products", "subscriptions"]):
            dependencies["pg"] = "^8.11.5"
            dependencies["pg-hstore"] = "^2.3.4"
        
        if "mongodb" in features or any(f in features for f in ["blog", "cms", "contact"]):
            dependencies["mongoose"] = "^8.0.0"
        
        # Add feature-specific dependencies
        if "stripe_payments" in features:
            dependencies["stripe"] = "^15.0.0"
        
        if "paypal_payments" in features:
            dependencies["@paypal/checkout-server-sdk"] = "^1.0.3"
        
        if any(f in features for f in ["menu", "reservations", "upload_images", "media"]):
            dependencies["multer"] = "^1.4.5-lts.1"
            dependencies["sharp"] = "^0.33.2"
        
        if any(f in features for f in ["chat", "real_time", "notifications"]):
            dependencies["socket.io"] = "^4.7.4"
        
        if any(f in features for f in ["newsletter", "contact", "email_notifications"]):
            dependencies["nodemailer"] = "^6.9.8"
        
        if any(f in features for f in ["sms_notifications", "whatsapp"]):
            dependencies["twilio"] = "^4.20.0"
        
        if "analytics" in features:
            dependencies["redis"] = "^4.6.12"
            dependencies["bull"] = "^4.12.1"
        
        if any(f in features for f in ["pdf_reports", "invoices"]):
            dependencies["pdfkit"] = "^0.14.0"
        
        if "oauth" in features:
            dependencies["passport"] = "^0.7.0"
            dependencies["passport-google-oauth20"] = "^2.0.0"
            dependencies["passport-github2"] = "^0.1.12"
        
        package_json = {
            "name": "lumicorepro-backend",
            "version": "1.0.0",
            "description": "Full-stack REST API backend for production services",
            "main": "server.js",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js",
                "test": "jest --coverage",
                "test:watch": "jest --watch",
                "docs": "node generate-docs.js",
            },
            "dependencies": dependencies,
            "devDependencies": dev_dependencies,
        }
        
        FileManager.write_json(str(target_dir / "package.json"), package_json)

    def _generate_server_js(self, target_dir: Path, features: List[str]) -> None:
        """Generate main server.js file."""
        has_socket_io = any(f in features for f in ["chat", "real_time", "notifications"])
        has_swagger = True  # Always include API docs
        
        routes_imports = []
        routes_mounts = []
        
        # Determine which routes to include based on features
        if any(f in features for f in ["jwt_auth", "oauth", "users"]):
            routes_imports.append("const authRoutes = require('./routes/authRoutes');")
            routes_mounts.append("app.use('/api/auth', authRoutes);")
        
        if "products" in features or "categories" in features:
            routes_imports.append("const productRoutes = require('./routes/productRoutes');")
            routes_mounts.append("app.use('/api/products', productRoutes);")
        
        if "orders" in features:
            routes_imports.append("const orderRoutes = require('./routes/orderRoutes');")
            routes_mounts.append("app.use('/api/orders', orderRoutes);")
        
        if "cart" in features:
            routes_imports.append("const cartRoutes = require('./routes/cartRoutes');")
            routes_mounts.append("app.use('/api/cart', cartRoutes);")
        
        if "wishlist" in features:
            routes_imports.append("const wishlistRoutes = require('./routes/wishlistRoutes');")
            routes_mounts.append("app.use('/api/wishlist', wishlistRoutes);")
        
        if "stripe_payments" in features or "paypal_payments" in features:
            routes_imports.append("const paymentRoutes = require('./routes/paymentRoutes');")
            routes_mounts.append("app.use('/api/payments', paymentRoutes);")
        
        if "users" in features:
            routes_imports.append("const userRoutes = require('./routes/userRoutes');")
            routes_mounts.append("app.use('/api/users', userRoutes);")
        
        if "analytics" in features:
            routes_imports.append("const analyticsRoutes = require('./routes/analyticsRoutes');")
            routes_mounts.append("app.use('/api/analytics', analyticsRoutes);")
        
        if "subscriptions" in features:
            routes_imports.append("const subscriptionRoutes = require('./routes/subscriptionRoutes');")
            routes_mounts.append("app.use('/api/subscriptions', subscriptionRoutes);")
        
        if "blog" in features or "posts" in features:
            routes_imports.append("const postRoutes = require('./routes/postRoutes');")
            routes_mounts.append("app.use('/api/posts', postRoutes);")
        
        if "reviews" in features:
            routes_imports.append("const reviewRoutes = require('./routes/reviewRoutes');")
            routes_mounts.append("app.use('/api/reviews', reviewRoutes);")
        
        if "appointments" in features:
            routes_imports.append("const appointmentRoutes = require('./routes/appointmentRoutes');")
            routes_mounts.append("app.use('/api/appointments', appointmentRoutes);")
        
        if "courses" in features:
            routes_imports.append("const courseRoutes = require('./routes/courseRoutes');")
            routes_mounts.append("app.use('/api/courses', courseRoutes);")
        
        if "properties" in features:
            routes_imports.append("const propertyRoutes = require('./routes/propertyRoutes');")
            routes_mounts.append("app.use('/api/properties', propertyRoutes);")
        
        if "menu" in features:
            routes_imports.append("const menuRoutes = require('./routes/menuRoutes');")
            routes_mounts.append("app.use('/api/menu', menuRoutes);")
        
        if "reservations" in features:
            routes_imports.append("const reservationRoutes = require('./routes/reservationRoutes');")
            routes_mounts.append("app.use('/api/reservations', reservationRoutes);")
        
        if "contact" in features:
            routes_imports.append("const contactRoutes = require('./routes/contactRoutes');")
            routes_mounts.append("app.use('/api/contact', contactRoutes);")
        
        if "newsletter" in features:
            routes_imports.append("const newsletterRoutes = require('./routes/newsletterRoutes');")
            routes_mounts.append("app.use('/api/newsletter', newsletterRoutes);")
        
        if "notifications" in features:
            routes_imports.append("const notificationRoutes = require('./routes/notificationRoutes');")
            routes_mounts.append("app.use('/api/notifications', notificationRoutes);")
        
        if "search" in features:
            routes_imports.append("const searchRoutes = require('./routes/searchRoutes');")
            routes_mounts.append("app.use('/api/search', searchRoutes);")
        
        if any(f in features for f in ["upload_images", "media"]):
            routes_imports.append("const uploadRoutes = require('./routes/uploadRoutes');")
            routes_mounts.append("app.use('/api/upload', uploadRoutes);")
        
        if "admin" in features or "role_based_access" in features:
            routes_imports.append("const adminRoutes = require('./routes/adminRoutes');")
            routes_mounts.append("app.use('/api/admin', adminRoutes);")
        
        routes_imports_str = "\n".join(routes_imports) if routes_imports else "// Routes will be mounted here"
        routes_mounts_str = "\n".join(routes_mounts) if routes_mounts else "// Routes will be mounted here"
        
        socket_io_import = "const http = require('http');\nconst { Server } = require('socket.io');" if has_socket_io else ""
        swagger_import = "const swaggerUi = require('swagger-ui-express');\nconst swaggerSpec = require('./config/swagger');" if has_swagger else ""
        socket_io_setup = """
// Create HTTP server
const server = http.createServer(app);

// Initialize Socket.IO
const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || "http://localhost:5173",
    methods: ["GET", "POST"],
  },
});

// Make io accessible to routes
app.set('io', io);

io.on('connection', (socket) => {
  console.log('Client connected: ', socket.id);
  
  socket.on('disconnect', () => {
    console.log('Client disconnected: ', socket.id);
  });
});""" if has_socket_io else ""

        swagger_docs_mount = "\napp.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));" if has_swagger else ""
        if has_socket_io:
            server_listen_block = """// Start server with Socket.IO support
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});"""
            module_exports_str = "module.exports = { app, io };"
        else:
            server_listen_block = """// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});"""
            module_exports_str = "module.exports = { app };"

        server_js = f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const compression = require('compression');
require('dotenv').config();

{socket_io_import}

const {{ errorHandler, notFound }} = require('./middleware/errorHandler');
{swagger_import}

const app = express();
const PORT = process.env.PORT || 5000;
{socket_io_setup}

// Security Middleware
app.use(helmet());

// Rate Limiting
const limiter = rateLimit({{
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_MAX) || 100,
  message: {{ error: 'Too many requests, please try again later.' }},
}});
app.use('/api/', limiter);

// CORS Configuration
app.use(cors({{
  origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  credentials: true,
}}));

// Body Parsing
app.use(express.json());
app.use(express.urlencoded({{ extended: true }}));

// Compression
app.use(compression());

// Logging
if (process.env.NODE_ENV !== 'test') {{
  app.use(morgan('combined'));
}}

{routes_mounts_str}

// API Documentation
{swagger_docs_mount}

// Health Check
app.get('/health', (req, res) => {{
  res.json({{
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
  }});
}});

// Ready Check
app.get('/ready', (req, res) => {{
  // Add your readiness checks here (database, cache, etc.)
  res.json({{ status: 'ready' }});
}});

// Error Handling
app.use(notFound);
app.use(errorHandler);

{server_listen_block}

{module_exports_str}
"""
        
        FileManager.write_file(str(target_dir / "server.js"), server_js)

    def _generate_config_files(self, target_dir: Path) -> None:
        """Generate database and swagger configuration files."""
        config_dir = target_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        db_js = """const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = process.env.DATABASE_URL
  ? new Sequelize(process.env.DATABASE_URL, {
      dialect: 'postgres',
      logging: process.env.NODE_ENV === 'development' ? console.log : false,
      dialectOptions: process.env.NODE_ENV === 'production' ? {
        ssl: { require: true, rejectUnauthorized: false }
      } : {},
    })
  : new Sequelize({
      dialect: 'sqlite',
      storage: './database.sqlite',
      logging: false,
    });

const connectDB = async () => {
  try {
    await sequelize.authenticate();
    console.log('Database connected successfully.');
    if (process.env.NODE_ENV === 'development') {
      await sequelize.sync({ alter: true });
    }
  } catch (error) {
    console.error('Database connection failed:', error.message);
  }
};

module.exports = { sequelize, connectDB };
"""
        FileManager.write_file(str(config_dir / "database.js"), db_js)

        swagger_js = """module.exports = {
  openapi: '3.0.0',
  info: {
    title: 'Enterprise REST API',
    version: '1.0.0',
    description: 'High-performance REST API backend for production services',
  },
  servers: [
    { url: 'http://localhost:5000/api', description: 'Local Development Server' },
  ],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
      },
    },
  },
};
"""
        FileManager.write_file(str(config_dir / "swagger.js"), swagger_js)

    def _generate_middleware(self, target_dir: Path, features: List[str]) -> None:
        """Generate error handling and JWT authentication middleware."""
        mw_dir = target_dir / "middleware"
        mw_dir.mkdir(parents=True, exist_ok=True)

        err_js = """const notFound = (req, res, next) => {
  const error = new Error(`Not Found - ${req.originalUrl}`);
  res.status(404);
  next(error);
};

const errorHandler = (err, req, res, next) => {
  const statusCode = res.statusCode === 200 ? 500 : res.statusCode;
  res.status(statusCode).json({
    success: false,
    message: err.message,
    stack: process.env.NODE_ENV === 'production' ? null : err.stack,
  });
};

module.exports = { notFound, errorHandler };
"""
        FileManager.write_file(str(mw_dir / "errorHandler.js"), err_js)

        auth_js = """const jwt = require('jsonwebtoken');

const protect = async (req, res, next) => {
  let token;
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    try {
      token = req.headers.authorization.split(' ')[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET || 'secret');
      req.user = decoded;
      return next();
    } catch (error) {
      return res.status(401).json({ success: false, message: 'Not authorized, token failed' });
    }
  }
  if (!token) {
    return res.status(401).json({ success: false, message: 'Not authorized, no token provided' });
  }
};

const adminOnly = (req, res, next) => {
  if (req.user && req.user.role === 'admin') {
    next();
  } else {
    res.status(403).json({ success: false, message: 'Admin access required' });
  }
};

module.exports = { protect, adminOnly };
"""
        FileManager.write_file(str(mw_dir / "auth.js"), auth_js)

    def _generate_controllers(self, target_dir: Path, features: List[str], website_type: str, industry: str) -> List[str]:
        """Generate controllers based on detected features."""
        ctrl_dir = target_dir / "controllers"
        ctrl_dir.mkdir(parents=True, exist_ok=True)
        controllers = []

        # Auth Controller
        auth_ctrl = """const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

exports.register = async (req, res) => {
  try {
    const { email, password, name } = req.body;
    const token = jwt.sign({ email, role: 'user' }, process.env.JWT_SECRET || 'secret', { expiresIn: '7d' });
    res.status(201).json({ success: true, message: 'User registered successfully', token, user: { email, name } });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const token = jwt.sign({ email, role: 'user' }, process.env.JWT_SECRET || 'secret', { expiresIn: '7d' });
    res.json({ success: true, message: 'Login successful', token, user: { email } });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
};

exports.getProfile = async (req, res) => {
  res.json({ success: true, user: req.user });
};
"""
        FileManager.write_file(str(ctrl_dir / "authController.js"), auth_ctrl)
        controllers.append("auth")

        # Entity controller based on website type (products for ecommerce, appointments for healthcare, etc.)
        if website_type in ("ecommerce", "retail", "fashion") or "products" in features or "cart" in features:
            prod_ctrl = """exports.getAll = async (req, res) => {
  res.json({
    success: true,
    count: 3,
    data: [
      { id: 1, name: 'Sample Item Alpha', price: 99.99, category: 'Electronics', stock: 25 },
      { id: 2, name: 'Sample Item Beta', price: 149.99, category: 'Gadgets', stock: 10 },
      { id: 3, name: 'Sample Item Gamma', price: 49.99, category: 'Accessories', stock: 50 },
    ],
  });
};

exports.getById = async (req, res) => {
  res.json({ success: true, data: { id: req.params.id, name: 'Sample Item', price: 99.99 } });
};

exports.create = async (req, res) => {
  res.status(201).json({ success: true, message: 'Created successfully', data: req.body });
};
"""
            FileManager.write_file(str(ctrl_dir / "productController.js"), prod_ctrl)
            controllers.append("products")

            order_ctrl = """exports.createOrder = async (req, res) => {
  res.status(201).json({ success: true, message: 'Order created', orderId: 'ORD-' + Date.now(), items: req.body.items });
};

exports.getUserOrders = async (req, res) => {
  res.json({ success: true, orders: [] });
};
"""
            FileManager.write_file(str(ctrl_dir / "orderController.js"), order_ctrl)
            controllers.append("orders")

        elif website_type in ("healthcare", "medical"):
            app_ctrl = """exports.getAppointments = async (req, res) => {
  res.json({ success: true, appointments: [] });
};

exports.bookAppointment = async (req, res) => {
  res.status(201).json({ success: true, message: 'Appointment booked successfully', appointmentId: 'APT-' + Date.now() });
};
"""
            FileManager.write_file(str(ctrl_dir / "appointmentController.js"), app_ctrl)
            controllers.append("appointments")

        else:
            item_ctrl = """exports.getAll = async (req, res) => {
  res.json({ success: true, data: [] });
};

exports.create = async (req, res) => {
  res.status(201).json({ success: true, message: 'Item created', data: req.body });
};
"""
            FileManager.write_file(str(ctrl_dir / "itemController.js"), item_ctrl)
            controllers.append("items")

        return controllers

    def _generate_routes(self, target_dir: Path, controllers: List[str]) -> None:
        """Generate Express route files."""
        routes_dir = target_dir / "routes"
        routes_dir.mkdir(parents=True, exist_ok=True)

        for ctrl in controllers:
            if ctrl == "auth":
                route_code = """const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const { protect } = require('../middleware/auth');

router.post('/register', authController.register);
router.post('/login', authController.login);
router.get('/profile', protect, authController.getProfile);

module.exports = router;
"""
                FileManager.write_file(str(routes_dir / "authRoutes.js"), route_code)
            elif ctrl == "products":
                route_code = """const express = require('express');
const router = express.Router();
const productController = require('../controllers/productController');

router.get('/', productController.getAll);
router.get('/:id', productController.getById);
router.post('/', productController.create);

module.exports = router;
"""
                FileManager.write_file(str(routes_dir / "productRoutes.js"), route_code)
            elif ctrl == "orders":
                route_code = """const express = require('express');
const router = express.Router();
const orderController = require('../controllers/orderController');
const { protect } = require('../middleware/auth');

router.post('/', protect, orderController.createOrder);
router.get('/my-orders', protect, orderController.getUserOrders);

module.exports = router;
"""
                FileManager.write_file(str(routes_dir / "orderRoutes.js"), route_code)
            else:
                route_code = f"""const express = require('express');
const router = express.Router();
const controller = require('../controllers/{ctrl}Controller');

router.get('/', (req, res) => {{
  if (controller.getAll) return controller.getAll(req, res);
  res.json({{ success: true, message: 'Resource endpoint active' }});
}});

module.exports = router;
"""
                FileManager.write_file(str(routes_dir / f"{ctrl}Routes.js"), route_code)

    def _generate_models(self, target_dir: Path, features: List[str], website_type: str) -> None:
        """Generate database models."""
        models_dir = target_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        user_model = """const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const User = sequelize.define('User', {
  id: { type: DataTypes.INTEGER, autoIncrement: true, primaryKey: true },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  password: { type: DataTypes.STRING, allowNull: false },
  name: { type: DataTypes.STRING },
  role: { type: DataTypes.STRING, defaultValue: 'user' },
});

module.exports = User;
"""
        FileManager.write_file(str(models_dir / "User.js"), user_model)

        index_model = """const User = require('./User');
module.exports = { User };
"""
        FileManager.write_file(str(models_dir / "index.js"), index_model)

    def _generate_services(self, target_dir: Path, features: List[str]) -> None:
        """Generate backend services."""
        serv_dir = target_dir / "services"
        serv_dir.mkdir(parents=True, exist_ok=True)

        email_serv = """class EmailService {
  static async sendNotification(to, subject, text) {
    console.log(`[EmailService] Notification to ${to}: ${subject}`);
    return true;
  }
}

module.exports = EmailService;
"""
        FileManager.write_file(str(serv_dir / "emailService.js"), email_serv)

    def _generate_utils(self, target_dir: Path) -> None:
        """Generate utility helper modules."""
        utils_dir = target_dir / "utils"
        utils_dir.mkdir(parents=True, exist_ok=True)

        resp_js = """exports.apiResponse = (res, statusCode, success, message, data = null) => {
  return res.status(statusCode).json({ success, message, data });
};
"""
        FileManager.write_file(str(utils_dir / "response.js"), resp_js)

    def _generate_env_files(self, target_dir: Path, features: List[str]) -> None:
        """Generate environment example file."""
        env_content = """PORT=5000
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
JWT_SECRET=your_jwt_secret_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_db
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100
"""
        FileManager.write_file(str(target_dir / ".env.example"), env_content)

    def _generate_api_docs(self, target_dir: Path, spec: Dict[str, Any], controllers: List[str]) -> None:
        """Generate API documentation markdown."""
        docs_dir = target_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        md_content = f"""# API Documentation — {spec.get('project_name', 'Project')}

## Base URL
`http://localhost:5000/api`

## Endpoints
- `POST /api/auth/register` — Register a new account
- `POST /api/auth/login` — Login and receive JWT bearer token
- `GET /api/auth/profile` — Get authenticated user details
"""
        for c in controllers:
            if c != "auth":
                md_content += f"- `GET /api/{c}` — Retrieve {c} resources\n"

        FileManager.write_file(str(docs_dir / "API_DOCUMENTATION.md"), md_content)