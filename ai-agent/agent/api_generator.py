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

    BASELINE_FEATURES = ("jwt_auth", "users", "contact")

    def generate_full_backend(self, target_dir: Path, plan: Dict[str, Any]) -> None:
        """Generate complete backend with all necessary APIs."""
        spec = dict(plan.get("spec") or {})
        if plan.get("layout_mode") == "client-static" or spec.get("layout_mode") == "client-static":
            agent_logger.info("Skipping API generation for explicit client-static project.")
            return
        website_type = spec.get("website_type", "business")
        industry = spec.get("industry", "general")
        requested_features = plan.get("features") or spec.get("features") or []
        if isinstance(requested_features, str):
            requested_features = [requested_features]
        if not isinstance(requested_features, (list, tuple, set)):
            requested_features = []
        features = list(dict.fromkeys(
            list(self.BASELINE_FEATURES) +
            [str(feature).strip() for feature in requested_features if str(feature).strip()]
        ))
        spec["features"] = features
        plan["features"] = features
        plan["spec"] = spec
        
        agent_logger.info(f"Generating full backend for {website_type} ({industry}) with {len(features)} features")
        
        # 1. Generate package.json with all dependencies
        self._generate_package_json(target_dir, features)
        
        # 2. Generate config files
        self._generate_config_files(target_dir)
        
        # 3. Generate middleware
        self._generate_middleware(target_dir, features)
        
        # 4. Generate controllers based on features
        controllers = self._generate_controllers(target_dir, features, website_type, industry)
        
        # 5. Generate routes
        self._generate_routes(target_dir, controllers)

        # 6. Mount only route modules that were actually generated.
        self._generate_server_js(target_dir, features, controllers)
        
        # 7. Generate PostgreSQL models
        self._generate_models(target_dir, features, website_type)

        # 8. Generate versioned migrations and backend tests.
        self._generate_migrations(target_dir)
        self._generate_test_suite(target_dir)
        
        # 9. Generate services layer
        self._generate_services(target_dir, features)
        
        # 10. Generate utils
        self._generate_utils(target_dir)
        
        # 11. Generate environment files
        self._generate_env_files(
            target_dir, features, spec.get("project_name") or plan.get("project_name") or "app"
        )
        
        # 12. Generate API documentation
        self._generate_api_docs(target_dir, spec, controllers)

        if "stripe_payments" in features:
            from .extensions.checkout_stripe import CheckoutScaffolder

            outcome = CheckoutScaffolder(str(target_dir.parent)).scaffold(features=features)
            if outcome.get("status") != "ok":
                raise RuntimeError(
                    f"Explicit Stripe checkout generation failed: {outcome.get('message', 'unknown error')}"
                )
        
        agent_logger.info(f"Backend generation complete: {len(controllers)} controllers, {len(controllers)} routes")

    def _generate_package_json(self, target_dir: Path, features: List[str]) -> None:
        """Generate package.json with all required dependencies."""
        # Base dependencies
        dependencies = {
            "express": "^4.19.2",
            "cors": "^2.8.5",
            "dotenv": "^16.4.5",
            "sequelize": "^6.37.0",
            "pg": "^8.11.5",
            "pg-hstore": "^2.3.4",
            "helmet": "^7.1.0",
            "express-rate-limit": "^7.1.5",
            "jsonwebtoken": "^9.0.2",
            "bcryptjs": "^2.4.3",
            "cookie-parser": "^1.4.6",
            "express-validator": "^7.0.1",
            "validator": "^13.12.0",
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
                "db:migrate": "node migrations/run.js",
                "docs": "node generate-docs.js",
            },
            "dependencies": dependencies,
            "devDependencies": dev_dependencies,
        }
        
        FileManager.write_json(str(target_dir / "package.json"), package_json)

    def _generate_server_js(
        self, target_dir: Path, features: List[str], controllers: List[str]
    ) -> None:
        """Generate main server.js file."""
        has_socket_io = any(f in features for f in ["chat", "real_time", "notifications"])
        has_swagger = True  # Always include API docs
        
        route_names = {
            "auth": ("authRoutes", "/api/auth"),
            "products": ("productRoutes", "/api/products"),
            "orders": ("orderRoutes", "/api/orders"),
            "contact": ("contactRoutes", "/api/contact"),
        }
        routes_imports = []
        routes_mounts = []
        for controller in controllers:
            route_spec = route_names.get(controller)
            if route_spec:
                route_name, route_path = route_spec
                routes_imports.append(
                    f"const {route_name} = require('./routes/{route_name}');"
                )
                routes_mounts.append(f"app.use('{route_path}', {route_name});")
        
        routes_imports_str = "\n".join(routes_imports) if routes_imports else "// Routes will be mounted here"
        routes_mounts_str = "\n".join(routes_mounts) if routes_mounts else "// Routes will be mounted here"
        
        socket_io_import = (
            "const http = require('http');\nconst { Server } = require('socket.io');"
            if has_socket_io else "const http = require('http');"
        )
        swagger_import = "const swaggerUi = require('swagger-ui-express');\nconst swaggerSpec = require('./config/swagger');" if has_swagger else ""
        socket_io_setup = """
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
        server_listen_block = """const startServer = async () => {
  await connectDB();
  return server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  });
};

if (require.main === module) {
  startServer().catch(async (error) => {
    console.error('Server startup failed:', error.message);
    await sequelize.close();
    process.exitCode = 1;
  });
}"""
        module_exports_str = "module.exports = { app, server, startServer, io };" if has_socket_io else "module.exports = { app, server, startServer };"

        server_js = f"""const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const compression = require('compression');
const cookieParser = require('cookie-parser');
require('dotenv').config();

{socket_io_import}

const {{ connectDB, sequelize }} = require('./config/database');
const {{ errorHandler, notFound }} = require('./middleware/errorHandler');
const usageLimiter = require('./middleware/usageLimiter');
const {{ auditRequest }} = require('./middleware/auditLogger');
{swagger_import}
{routes_imports_str}

const app = express();
const PORT = process.env.PORT || 5000;
const server = http.createServer(app);
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
app.use(cookieParser());

// Compression
app.use(compression());

// Logging
if (process.env.NODE_ENV !== 'test') {{
  app.use(morgan('combined'));
}}

// Audit logging (opt-in via AUDIT_LOG env, defaults on)
if (process.env.AUDIT_LOG !== 'false') {{
  app.use(auditRequest);
}}

// Plan usage limits
app.get('/api/usage/limits', (req, res) => {{
  res.json({{ success: true, data: usageLimiter.defaultLimits }});
}});

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
app.get('/ready', async (req, res) => {{
  try {{
    await sequelize.authenticate();
    res.json({{ status: 'ready', database: 'connected' }});
  }} catch (error) {{
    console.error('Readiness check failed:', error.message);
    res.status(503).json({{ status: 'not_ready', database: 'unavailable' }});
  }}
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

let sequelize;
if (process.env.DATABASE_URL) {
  sequelize = new Sequelize(process.env.DATABASE_URL, {
    dialect: 'postgres',
    logging: process.env.NODE_ENV === 'development' ? console.log : false,
    dialectOptions: process.env.NODE_ENV === 'production'
      ? { ssl: { require: true, rejectUnauthorized: true } }
      : {},
    pool: { max: 10, min: 0, acquire: 30000, idle: 10000 },
  });
} else if (process.env.DB_HOST && process.env.DB_NAME && process.env.DB_USER) {
  sequelize = new Sequelize(
    process.env.DB_NAME,
    process.env.DB_USER,
    process.env.DB_PASSWORD || '',
    {
      host: process.env.DB_HOST,
      port: Number(process.env.DB_PORT || 5432),
      dialect: 'postgres',
      logging: process.env.NODE_ENV === 'development' ? console.log : false,
      dialectOptions: process.env.NODE_ENV === 'production'
        ? { ssl: { require: true, rejectUnauthorized: true } }
        : {},
      pool: { max: 10, min: 0, acquire: 30000, idle: 10000 },
    }
  );
} else {
  throw new Error('DATABASE_URL or DB_HOST/DB_NAME/DB_USER is required.');
}

const connectDB = async () => {
  await sequelize.authenticate();
  const { runMigrations } = require('../migrations/run');
  await runMigrations();
  console.log('Database connected and migrations are current.');
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
  error.statusCode = 404;
  res.status(404);
  next(error);
};

const errorHandler = (err, req, res, next) => {
  const statusCode = Number.isInteger(err.statusCode) && err.statusCode >= 400 && err.statusCode < 500
    ? err.statusCode
    : 500;
  res.status(statusCode).json({
    success: false,
    message: statusCode < 500 ? err.message : 'An unexpected server error occurred.',
  });
};

module.exports = { notFound, errorHandler };
"""
        FileManager.write_file(str(mw_dir / "errorHandler.js"), err_js)

        auth_js = """const jwt = require('jsonwebtoken');
const { jwtSecret } = require('../utils/jwtSecret');

const protect = (req, res, next) => {
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    try {
      const token = req.headers.authorization.split(' ')[1];
      if (!token) throw new Error('Missing bearer token');
      const decoded = jwt.verify(token, jwtSecret, { algorithms: ['HS256'] });
      req.user = decoded;
      return next();
    } catch (_) {
      return res.status(401).json({ success: false, message: 'Not authorized, token failed' });
    }
  }
  return res.status(401).json({ success: false, message: 'Not authorized, no token provided' });
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

        usage_limiter_js = """/**
 * Usage Limiter — per-plan monthly metering and enforcement (fail-open).
 * Attach per route: router.get('/', enforceLimit('api', { limit: 1000 }), handler);
 * Individual metrics are configurable via the USAGE_LIMITS env (JSON).
 */
let limitConfig = {};
try {
  limitConfig = process.env.USAGE_LIMITS ? JSON.parse(process.env.USAGE_LIMITS) : {};
} catch (_) { /* invalid env, use defaults */ }

const defaultLimits = Object.assign(
  {
    api: 1000,
    ai_generation: 50,
    ai_chat: 200,
    uploads: 100,
    exports: 50,
  },
  limitConfig && typeof limitConfig === 'object' ? limitConfig : {}
);

const monthKey = () => {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
};

const counters = new Map();

const usageOf = (metric) => counters.get(`${monthKey()}:${metric}`) || 0;

const bump = (metric, n = 1) => {
  const key = `${monthKey()}:${metric}`;
  const next = usageOf(metric) + n;
  counters.set(key, next);
  return next;
};

const planMultiplier = (user) => {
  const map = { free: 1, starter: 1, pro: 5, growth: 20, scale: 100, enterprise: 1000 };
  return map[(user && (user.plan || user.role)) || 'free'] || 1;
};

const enforceLimit = (metric, options = {}) => (req, res, next) => {
  try {
    const limit = (options.limit || defaultLimits[metric] || 1000) * planMultiplier(req.user);
    if (usageOf(metric) >= limit) {
      return res.status(429).json({
        success: false,
        code: 'PLAN_LIMIT_EXCEEDED',
        message: `Monthly ${metric} limit of ${limit} reached. Upgrade your plan to continue.`,
      });
    }
    res.setHeader('X-Plan-Limit', limit);
    res.setHeader('X-Plan-Usage', usageOf(metric));
    res.once('finish', () => {
      if (res.statusCode < 500) bump(metric, 1);
    });
    next();
  } catch (err) {
    next();
  }
};

const meter = (metric) => (req, res, next) => {
  res.once('finish', () => {
    if (res.statusCode < 500) {
      try { bump(metric, 1); } catch (_) { /* noop */ }
    }
  });
  next();
};

module.exports = { enforceLimit, meter, defaultLimits, counters };
"""
        FileManager.write_file(str(mw_dir / "usageLimiter.js"), usage_limiter_js)

        audit_logger_js = """/**
 * Audit Logger — request audit trail, opt-in and fail-open.
 * Enable with AUDIT_LOG=true (default) or configure AUDIT_LOG_FILE.
 */
const fs = require('fs');
const path = require('path');

const enabled = process.env.AUDIT_LOG !== 'false';
const logFile = path.resolve(process.env.AUDIT_LOG_FILE || './audit.log');

const persist = (entry) => {
  try {
    fs.appendFileSync(logFile, entry + '\\n');
    if (process.env.AUDIT_LOG_STDOUT !== 'false') {
      console.log(`[AUDIT] ${entry}`);
    }
  } catch (_) { /* noop */ }
};

const auditRequest = (req, res, next) => {
  if (!enabled) return next();
  const startedAt = Date.now();
  res.once('finish', () => {
    try {
      persist(JSON.stringify({
        ts: new Date().toISOString(),
        method: req.method,
        url: req.originalUrl,
        status: res.statusCode,
        durationMs: Date.now() - startedAt,
        user: (req.user && (req.user.id || req.user.sub || req.user.email)) || null,
        ip: req.ip || (req.socket && req.socket.remoteAddress) || null,
        ua: req.headers['user-agent'] || null,
      }));
    } catch (_) { /* noop */ }
  });
  next();
};

module.exports = { auditRequest, persist };
"""
        FileManager.write_file(str(mw_dir / "auditLogger.js"), audit_logger_js)

    def _generate_controllers(self, target_dir: Path, features: List[str], website_type: str, industry: str) -> List[str]:
        """Generate controllers based on detected features."""
        ctrl_dir = target_dir / "controllers"
        ctrl_dir.mkdir(parents=True, exist_ok=True)
        controllers = []

        # Auth Controller
        auth_ctrl = """const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const validator = require('validator');
const { jwtSecret } = require('../utils/jwtSecret');
const { sequelize } = require('../config/database');
const { User, RefreshSession } = require('../models');

const REFRESH_TTL_MS = 7 * 24 * 60 * 60 * 1000;
const dummyPasswordHash = bcrypt.hashSync(crypto.randomBytes(32).toString('hex'), 12);
const cookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  path: '/api/auth',
  maxAge: REFRESH_TTL_MS,
};

const publicUser = (user) => ({
  id: user.id,
  email: user.email,
  name: user.name,
  role: user.role,
});

const createAccessToken = (user) => jwt.sign(
  { sub: user.id, role: user.role },
  jwtSecret,
  { expiresIn: '15m', algorithm: 'HS256' }
);

const createRefreshSession = async (userId, transaction) => {
  const token = crypto.randomBytes(48).toString('base64url');
  await RefreshSession.create({
    user_id: userId,
    token_hash: crypto.createHash('sha256').update(token).digest('hex'),
    expires_at: new Date(Date.now() + REFRESH_TTL_MS),
  }, { transaction });
  return token;
};

const setRefreshCookie = (res, token) => res.cookie('refreshToken', token, cookieOptions);
const clearRefreshCookie = (res) => res.clearCookie('refreshToken', {
  httpOnly: cookieOptions.httpOnly,
  secure: cookieOptions.secure,
  sameSite: cookieOptions.sameSite,
  path: cookieOptions.path,
});

const invalidInput = (res, message) => res.status(422).json({
  success: false,
  code: 'VALIDATION_ERROR',
  message,
});

exports.register = async (req, res, next) => {
  try {
    const { email, password, name } = req.body || {};
    if (
      typeof email !== 'string' ||
      !validator.isEmail(email, { allow_utf8_local_part: false }) ||
      typeof name !== 'string' ||
      name.trim().length < 2 ||
      name.trim().length > 100 ||
      typeof password !== 'string' ||
      password.length < 10 ||
      password.length > 128 ||
      Buffer.byteLength(password, 'utf8') > 72
    ) {
      return invalidInput(res, 'Provide a valid email, a name of 2-100 characters, and a password of 10-72 bytes.');
    }

    const normalizedEmail = validator.normalizeEmail(email, { gmail_remove_dots: false });
    if (!normalizedEmail) return invalidInput(res, 'Provide a valid email address.');
    if (await User.findOne({ where: { email: normalizedEmail } })) {
      return res.status(409).json({ success: false, code: 'EMAIL_IN_USE', message: 'An account already exists for this email.' });
    }

    const passwordHash = await bcrypt.hash(password, 12);
    let user;
    let refreshToken;
    await sequelize.transaction(async (transaction) => {
      user = await User.create({
        email: normalizedEmail,
        password_hash: passwordHash,
        name: name.trim(),
      }, { transaction });
      refreshToken = await createRefreshSession(user.id, transaction);
    });

    setRefreshCookie(res, refreshToken);
    return res.status(201).json({
      success: true,
      message: 'Account created.',
      data: { user: publicUser(user), accessToken: createAccessToken(user) },
    });
  } catch (error) {
    if (error.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ success: false, code: 'EMAIL_IN_USE', message: 'An account already exists for this email.' });
    }
    return next(error);
  }
};

exports.login = async (req, res, next) => {
  try {
    const { email, password } = req.body || {};
    if (typeof email !== 'string' || typeof password !== 'string' || !validator.isEmail(email)) {
      return res.status(401).json({ success: false, code: 'INVALID_CREDENTIALS', message: 'Email or password is incorrect.' });
    }

    const normalizedEmail = validator.normalizeEmail(email, { gmail_remove_dots: false });
    const user = normalizedEmail ? await User.findOne({ where: { email: normalizedEmail } }) : null;
    const passwordMatches = await bcrypt.compare(password, user ? user.password_hash : dummyPasswordHash);
    if (!user || !passwordMatches) {
      return res.status(401).json({ success: false, code: 'INVALID_CREDENTIALS', message: 'Email or password is incorrect.' });
    }

    const refreshToken = await createRefreshSession(user.id);
    setRefreshCookie(res, refreshToken);
    return res.json({
      success: true,
      message: 'Login successful.',
      data: { user: publicUser(user), accessToken: createAccessToken(user) },
    });
  } catch (error) {
    return next(error);
  }
};

exports.refresh = async (req, res, next) => {
  try {
    const rawToken = req.cookies && req.cookies.refreshToken;
    if (typeof rawToken !== 'string' || rawToken.length > 256) {
      clearRefreshCookie(res);
      return res.status(401).json({ success: false, code: 'INVALID_SESSION', message: 'Session is invalid or expired.' });
    }

    const tokenHash = crypto.createHash('sha256').update(rawToken).digest('hex');
    const rotated = await sequelize.transaction(async (transaction) => {
      const session = await RefreshSession.findOne({
        where: { token_hash: tokenHash, revoked_at: null },
        transaction,
        lock: transaction.LOCK.UPDATE,
      });
      if (!session || session.expires_at <= new Date()) return null;

      const user = await User.findByPk(session.user_id, { transaction });
      if (!user) return null;

      session.revoked_at = new Date();
      await session.save({ transaction });
      const refreshToken = await createRefreshSession(user.id, transaction);
      return { user, refreshToken };
    });

    if (!rotated) {
      clearRefreshCookie(res);
      return res.status(401).json({ success: false, code: 'INVALID_SESSION', message: 'Session is invalid or expired.' });
    }
    setRefreshCookie(res, rotated.refreshToken);
    return res.json({
      success: true,
      data: { user: publicUser(rotated.user), accessToken: createAccessToken(rotated.user) },
    });
  } catch (error) {
    return next(error);
  }
};

exports.logout = async (req, res, next) => {
  try {
    const rawToken = req.cookies && req.cookies.refreshToken;
    if (typeof rawToken === 'string' && rawToken.length <= 256) {
      const tokenHash = crypto.createHash('sha256').update(rawToken).digest('hex');
      await RefreshSession.update(
        { revoked_at: new Date() },
        { where: { token_hash: tokenHash, revoked_at: null } }
      );
    }
    clearRefreshCookie(res);
    return res.json({ success: true, message: 'Logged out.' });
  } catch (error) {
    return next(error);
  }
};

exports.getProfile = async (req, res, next) => {
  try {
    const user = await User.findByPk(req.user.sub);
    if (!user) return res.status(404).json({ success: false, code: 'USER_NOT_FOUND', message: 'Account not found.' });
    return res.json({ success: true, data: { user: publicUser(user) } });
  } catch (error) {
    return next(error);
  }
};
"""
        FileManager.write_file(str(ctrl_dir / "authController.js"), auth_ctrl)
        controllers.append("auth")

        if "contact" in features:
            contact_ctrl = """const { ContactSubmission } = require('../models');

exports.submitContact = async (req, res, next) => {
  try {
    const submission = await ContactSubmission.create({
      name: req.body.name.trim(),
      email: req.body.email.trim().toLowerCase(),
      message: req.body.message.trim(),
    });
    return res.status(201).json({
      success: true,
      message: 'Your message has been received.',
      data: { id: submission.id, createdAt: submission.createdAt },
    });
  } catch (error) {
    return next(error);
  }
};
"""
            FileManager.write_file(str(ctrl_dir / "contactController.js"), contact_ctrl)
            controllers.append("contact")

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

        return controllers

    def _generate_routes(self, target_dir: Path, controllers: List[str]) -> None:
        """Generate Express route files."""
        routes_dir = target_dir / "routes"
        routes_dir.mkdir(parents=True, exist_ok=True)

        for ctrl in controllers:
            if ctrl == "auth":
                route_code = """const express = require('express');
const rateLimit = require('express-rate-limit');
const router = express.Router();
const authController = require('../controllers/authController');
const { protect } = require('../middleware/auth');

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, code: 'AUTH_RATE_LIMIT', message: 'Too many authentication attempts. Try again later.' },
});

router.post('/register', authLimiter, authController.register);
router.post('/login', authLimiter, authController.login);
router.post('/refresh', authLimiter, authController.refresh);
router.post('/logout', authController.logout);
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
            elif ctrl == "contact":
                route_code = """const express = require('express');
const { body, validationResult } = require('express-validator');
const contactController = require('../controllers/contactController');
const router = express.Router();

const validateContact = [
  body('name').isString().trim().isLength({ min: 2, max: 100 }),
  body('email').isEmail().normalizeEmail(),
  body('message').isString().trim().isLength({ min: 10, max: 5000 }),
  (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(422).json({
        success: false,
        code: 'VALIDATION_ERROR',
        message: 'Please provide a valid name, email, and message.',
        errors: errors.array().map(({ path, msg }) => ({ field: path, message: msg })),
      });
    }
    return next();
  },
];

router.post('/', validateContact, contactController.submitContact);

module.exports = router;
"""
                FileManager.write_file(str(routes_dir / "contactRoutes.js"), route_code)
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
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  email: { type: DataTypes.STRING(254), allowNull: false, unique: true },
  password_hash: { type: DataTypes.STRING(255), allowNull: false },
  name: { type: DataTypes.STRING(100), allowNull: false },
  role: { type: DataTypes.STRING(32), allowNull: false, defaultValue: 'user' },
}, {
  tableName: 'users',
  underscored: true,
});

module.exports = User;
"""
        FileManager.write_file(str(models_dir / "User.js"), user_model)

        refresh_session_model = """const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const RefreshSession = sequelize.define('RefreshSession', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  user_id: { type: DataTypes.UUID, allowNull: false },
  token_hash: { type: DataTypes.STRING(64), allowNull: false, unique: true },
  expires_at: { type: DataTypes.DATE, allowNull: false },
  revoked_at: { type: DataTypes.DATE, allowNull: true },
}, {
  tableName: 'refresh_sessions',
  underscored: true,
});

module.exports = RefreshSession;
"""
        FileManager.write_file(str(models_dir / "RefreshSession.js"), refresh_session_model)

        contact_model = """const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const ContactSubmission = sequelize.define('ContactSubmission', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING(100), allowNull: false },
  email: { type: DataTypes.STRING(254), allowNull: false },
  message: { type: DataTypes.TEXT, allowNull: false },
}, {
  tableName: 'contact_submissions',
  underscored: true,
});

module.exports = ContactSubmission;
"""
        FileManager.write_file(str(models_dir / "ContactSubmission.js"), contact_model)

        index_model = """const User = require('./User');
const RefreshSession = require('./RefreshSession');
const ContactSubmission = require('./ContactSubmission');

User.hasMany(RefreshSession, { foreignKey: 'user_id', onDelete: 'CASCADE' });
RefreshSession.belongsTo(User, { foreignKey: 'user_id' });

module.exports = { User, RefreshSession, ContactSubmission };
"""
        FileManager.write_file(str(models_dir / "index.js"), index_model)

    def _generate_migrations(self, target_dir: Path) -> None:
        """Generate versioned, transactional PostgreSQL migrations."""
        migrations_dir = target_dir / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)

        core_migration = """module.exports = {
  up: async ({ queryInterface, Sequelize, transaction }) => {
    await queryInterface.createTable('users', {
      id: { type: Sequelize.UUID, defaultValue: Sequelize.UUIDV4, primaryKey: true, allowNull: false },
      email: { type: Sequelize.STRING(254), allowNull: false, unique: true },
      password_hash: { type: Sequelize.STRING(255), allowNull: false },
      name: { type: Sequelize.STRING(100), allowNull: false },
      role: { type: Sequelize.STRING(32), allowNull: false, defaultValue: 'user' },
      created_at: { type: Sequelize.DATE, allowNull: false },
      updated_at: { type: Sequelize.DATE, allowNull: false },
    }, { transaction });

    await queryInterface.createTable('refresh_sessions', {
      id: { type: Sequelize.UUID, defaultValue: Sequelize.UUIDV4, primaryKey: true, allowNull: false },
      user_id: {
        type: Sequelize.UUID,
        allowNull: false,
        references: { model: 'users', key: 'id' },
        onDelete: 'CASCADE',
      },
      token_hash: { type: Sequelize.STRING(64), allowNull: false, unique: true },
      expires_at: { type: Sequelize.DATE, allowNull: false },
      revoked_at: { type: Sequelize.DATE, allowNull: true },
      created_at: { type: Sequelize.DATE, allowNull: false },
      updated_at: { type: Sequelize.DATE, allowNull: false },
    }, { transaction });

    await queryInterface.createTable('contact_submissions', {
      id: { type: Sequelize.UUID, defaultValue: Sequelize.UUIDV4, primaryKey: true, allowNull: false },
      name: { type: Sequelize.STRING(100), allowNull: false },
      email: { type: Sequelize.STRING(254), allowNull: false },
      message: { type: Sequelize.TEXT, allowNull: false },
      created_at: { type: Sequelize.DATE, allowNull: false },
      updated_at: { type: Sequelize.DATE, allowNull: false },
    }, { transaction });
  },
  down: async ({ queryInterface, transaction }) => {
    await queryInterface.dropTable('contact_submissions', { transaction });
    await queryInterface.dropTable('refresh_sessions', { transaction });
    await queryInterface.dropTable('users', { transaction });
  },
};
"""
        FileManager.write_file(
            str(migrations_dir / "001_create_core_tables.js"),
            core_migration,
        )

        migration_runner = """const fs = require('fs');
const path = require('path');
const { Sequelize } = require('sequelize');
const { sequelize } = require('../config/database');

const runMigrations = async () => {
  const queryInterface = sequelize.getQueryInterface();
  const migrationDir = __dirname;
  const migrationFiles = fs.readdirSync(migrationDir)
    .filter((name) => /^\\d+_.*\\.js$/.test(name))
    .sort();

  await sequelize.transaction(async (transaction) => {
    await sequelize.query('SELECT pg_advisory_xact_lock(724941)', { transaction });
    await sequelize.query(
      'CREATE TABLE IF NOT EXISTS schema_migrations (name VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())',
      { transaction }
    );
    const [appliedRows] = await sequelize.query(
      'SELECT name FROM schema_migrations',
      { transaction }
    );
    const applied = new Set(appliedRows.map((row) => row.name));

    for (const name of migrationFiles) {
      if (applied.has(name)) continue;
      const migration = require(path.join(migrationDir, name));
      await migration.up({ queryInterface, Sequelize, transaction });
      await sequelize.query(
        'INSERT INTO schema_migrations (name) VALUES (?)',
        { replacements: [name], transaction }
      );
    }
  });
};

if (require.main === module) {
  runMigrations()
    .then(() => sequelize.close())
    .catch(async (error) => {
      console.error('Database migration failed:', error.message);
      await sequelize.close();
      process.exitCode = 1;
    });
}

module.exports = { runMigrations };
"""
        FileManager.write_file(str(migrations_dir / "run.js"), migration_runner)

    def _generate_test_suite(self, target_dir: Path) -> None:
        """Generate integration tests that require an explicitly named test database."""
        tests_dir = target_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        auth_test = """const crypto = require('crypto');
process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || process.env.DATABASE_URL;
if (!process.env.DATABASE_URL || !/test/i.test(new URL(process.env.DATABASE_URL).pathname)) {
  throw new Error('Set TEST_DATABASE_URL to a dedicated PostgreSQL database whose name includes \"test\".');
}
process.env.JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(48).toString('hex');

const request = require('supertest');
const { app } = require('../server');
const { connectDB, sequelize } = require('../config/database');
const { User, RefreshSession } = require('../models');

describe('account authentication', () => {
  const email = `auth-${crypto.randomUUID()}@example.test`;
  const password = 'Sufficiently-Strong-Password-2026';

  beforeAll(async () => {
    await connectDB();
  });

  afterAll(async () => {
    const user = await User.findOne({ where: { email } });
    if (user) {
      await RefreshSession.destroy({ where: { user_id: user.id } });
      await user.destroy();
    }
    await sequelize.close();
  });

  test('registers, rejects duplicate email, logs in, and rejects invalid credentials', async () => {
    const registration = await request(app)
      .post('/api/auth/register')
      .send({ email, password, name: 'Test User' });
    expect(registration.status).toBe(201);
    expect(registration.body.data.user.email).toBe(email);
    expect(registration.body.data.user.password_hash).toBeUndefined();
    expect(registration.headers['set-cookie'][0]).toContain('refreshToken=');

    const duplicate = await request(app)
      .post('/api/auth/register')
      .send({ email, password, name: 'Test User' });
    expect(duplicate.status).toBe(409);

    const initialCookie = registration.headers['set-cookie'][0].split(';')[0];
    const profile = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', `Bearer ${registration.body.data.accessToken}`);
    expect(profile.status).toBe(200);
    expect(profile.body.data.user.email).toBe(email);

    const rotated = await request(app)
      .post('/api/auth/refresh')
      .set('Cookie', initialCookie);
    expect(rotated.status).toBe(200);
    const rotatedCookie = rotated.headers['set-cookie'][0].split(';')[0];
    expect(rotatedCookie).not.toBe(initialCookie);
    expect((await request(app).post('/api/auth/refresh').set('Cookie', initialCookie)).status).toBe(401);

    const login = await request(app)
      .post('/api/auth/login')
      .send({ email, password });
    expect(login.status).toBe(200);
    expect(login.body.data.accessToken).toBeTruthy();
    const loginCookie = login.headers['set-cookie'][0].split(';')[0];

    const invalidLogin = await request(app)
      .post('/api/auth/login')
      .send({ email, password: 'incorrect-password-value' });
    expect(invalidLogin.status).toBe(401);

    expect((await request(app).post('/api/auth/logout').set('Cookie', loginCookie)).status).toBe(200);
    expect((await request(app).post('/api/auth/refresh').set('Cookie', loginCookie)).status).toBe(401);
  });
});
"""
        FileManager.write_file(str(tests_dir / "auth.test.js"), auth_test)

        contact_test = """const crypto = require('crypto');
process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || process.env.DATABASE_URL;
if (!process.env.DATABASE_URL || !/test/i.test(new URL(process.env.DATABASE_URL).pathname)) {
  throw new Error('Set TEST_DATABASE_URL to a dedicated PostgreSQL database whose name includes \"test\".');
}
process.env.JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(48).toString('hex');

const request = require('supertest');
const { app } = require('../server');
const { connectDB, sequelize } = require('../config/database');
const ContactSubmission = require('../models/ContactSubmission');

describe('persistent contact form', () => {
  const email = `contact-${crypto.randomUUID()}@example.test`;

  beforeAll(async () => {
    await connectDB();
  });

  afterAll(async () => {
    await ContactSubmission.destroy({ where: { email } });
    await sequelize.close();
  });

  test('validates and stores contact submissions', async () => {
    const invalid = await request(app).post('/api/contact').send({ name: '', email, message: 'short' });
    expect(invalid.status).toBe(422);

    const result = await request(app).post('/api/contact').send({
      name: 'Test Sender',
      email,
      message: 'Please contact me about the service.',
    });
    expect(result.status).toBe(201);
    expect(await ContactSubmission.count({ where: { email } })).toBe(1);
  });
});
"""
        FileManager.write_file(str(tests_dir / "contact.test.js"), contact_test)

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

        # Fail-closed JWT secret resolution. Plain (non-f) Python string literal:
        # JS braces/$, backticks and newlines are emitted verbatim, so no brace
        # doubling is needed here.
        jwt_secret_js = """/**
 * Fail-closed JWT secret resolution.
 *
 * Refuses to boot when JWT_SECRET is missing, shorter than MIN_LENGTH, or a
 * well-known placeholder, so a publicly known value can never be used to forge
 * tokens (including admin tokens).
 *
 * Generate a secret with:
 *   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
 *   # or: openssl rand -hex 32
 */
const DENIED_SECRETS = [
  'secret',
  'changeme',
  'change_me',
  'change-me-in-production',
  'change_this_secret_in_production',
  'change_this_to_a_random_64_char_string',
  'lumi_jwt_secret',
  'replace-me',
  'replace_with_a_random_64_character_secret',
  'replace_with_secure_random_key',
  'secret_jwt_key',
  'secret_jwt_key_2026',
  'super_secret_production_key_2026',
  'your_jwt_secret_key_here',
  'your_super_secret_key_here_change_this',
  'your-super-secret-jwt-key-change-this',
  'your_super_secret_jwt_key_change_this_minimum_32_characters',
];

const MIN_LENGTH = 32;

function fail(reason) {
  console.error(`[fatal] JWT_SECRET ${reason}. Refusing to start.
Generate a strong secret with one of:
  node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
  # or: openssl rand -hex 32
Then set JWT_SECRET in your .env file.`);
  process.exit(1);
}

function resolveJwtSecret(env) {
  const source = env || process.env;
  const raw = source.JWT_SECRET;
  if (typeof raw !== 'string' || raw.trim() === '') fail('is not set');
  const secret = raw.trim();
  if (secret.length < MIN_LENGTH) {
    fail(`must be at least ${MIN_LENGTH} characters (got ${secret.length})`);
  }
  if (DENIED_SECRETS.indexOf(secret.toLowerCase()) !== -1) {
    fail('is a well-known placeholder value');
  }
  return secret;
}

const jwtSecret = Object.freeze(resolveJwtSecret(process.env));

module.exports = { jwtSecret, MIN_LENGTH };
"""
        FileManager.write_file(str(utils_dir / "jwtSecret.js"), jwt_secret_js)

    def _generate_env_files(
        self, target_dir: Path, features: List[str], project_name: str = "app"
    ) -> None:
        """Generate environment example file."""
        database_name = "".join(
            character.lower() if character.isalnum() else "_"
            for character in str(project_name or "app")
        ).strip("_") or "app"
        env_content = """PORT=5000
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
# REQUIRED, minimum 32 chars. Generate one with:
#   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
#   # or: openssl rand -hex 32
# The backend refuses to start if this is missing, short, or a known placeholder.
JWT_SECRET=
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_db
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100
"""
        env_content = "\n".join(
            f"DATABASE_URL=postgresql://postgres:replace-me@localhost:5432/{database_name}_db"
            if line.startswith("DATABASE_URL=")
            else line
            for line in env_content.splitlines()
        ) + "\n"
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
- `POST /api/auth/login` — Verify credentials and receive a short-lived access token
- `POST /api/auth/refresh` — Rotate the HttpOnly refresh-token cookie
- `POST /api/auth/logout` — Revoke the refresh session
- `GET /api/auth/profile` — Get authenticated user details
"""
        if "contact" in spec.get("features", []):
            md_content += "- `POST /api/contact` — Validate and persist a contact submission\n"
        if "stripe_payments" in spec.get("features", []):
            md_content += (
                "- `POST /api/payments/checkout-session` — Create an authenticated Stripe Checkout session\n"
                "- `GET /api/payments/orders/:orderId` — Read the authenticated order status\n"
                "- `POST /api/payments/webhook` — Verify and idempotently apply Stripe events\n"
            )
        for c in controllers:
            if c not in ("auth", "contact"):
                md_content += f"- `GET /api/{c}` — Retrieve {c} resources\n"

        md_content += """
## Local setup
1. Copy `.env.example` to `.env` and set a strong `JWT_SECRET`.
2. Set `DATABASE_URL` to a PostgreSQL database.
3. Run `npm install`, then `npm run db:migrate`.
4. Start the API with `npm run dev`.

The API also applies pending migrations before it begins listening. Never point
the integration tests at a production database; set `TEST_DATABASE_URL` to a
dedicated PostgreSQL database whose name contains `test`, then run `npm test`.
"""
        FileManager.write_file(str(docs_dir / "API_DOCUMENTATION.md"), md_content)