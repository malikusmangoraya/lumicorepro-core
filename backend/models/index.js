import { sequelize } from '../config/database.js';
import User from './User.js';
import Product from './Product.js';
import Order from './Order.js';
import Payment from './Payment.js';
import Review from './Review.js';
import Notification from './Notification.js';
import Category from './Category.js';
import Cart from './Cart.js';
import CartItem from './CartItem.js';
import Wishlist from './Wishlist.js';
import Subscription from './Subscription.js';
import Plan from './Plan.js';
import AnalyticsEvent from './AnalyticsEvent.js';
import Coupon from './Coupon.js';
import Address from './Address.js';
import WebhookEvent from './WebhookEvent.js';
import AuditLog from './AuditLog.js';
import Organization from './Organization.js';
import Role from './Role.js';
import Permission from './Permission.js';
import Membership from './Membership.js';
import Booking from './Booking.js';
import Doctor from './Doctor.js';
import Service from './Service.js';

/* ── User relationships ── */
User.hasMany(Order, { foreignKey: 'user_id', as: 'orders' });
User.hasMany(Payment, { foreignKey: 'user_id', as: 'payments' });
User.hasMany(Review, { foreignKey: 'user_id', as: 'reviews' });
User.hasMany(Notification, { foreignKey: 'recipient_id', as: 'notifications' });
User.hasOne(Cart, { foreignKey: 'user_id', as: 'cart' });
User.hasMany(Wishlist, { foreignKey: 'user_id', as: 'wishlists' });
User.hasMany(Subscription, { foreignKey: 'user_id', as: 'subscriptions' });
User.hasMany(AnalyticsEvent, { foreignKey: 'user_id', as: 'analyticsEvents' });
User.hasMany(Address, { foreignKey: 'user_id', as: 'addresses' });

/* ── Product relationships ── */
Product.belongsTo(Category, { foreignKey: 'category_id', as: 'categoryDetail' });
Product.belongsTo(User, { foreignKey: 'vendor_id', as: 'vendor' });
Product.hasMany(Review, { foreignKey: 'product_id', as: 'reviews' });
Product.hasMany(CartItem, { foreignKey: 'product_id', as: 'cartItems' });
Product.hasMany(Wishlist, { foreignKey: 'product_id', as: 'wishlists' });

/* ── Category relationships ── */
Category.hasMany(Product, { foreignKey: 'category_id', as: 'products' });

/* ── Order relationships ── */
Order.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Order.hasMany(Payment, { foreignKey: 'order_id', as: 'payments' });

/* ── Payment relationships ── */
Payment.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Payment.belongsTo(Order, { foreignKey: 'order_id', as: 'order' });

/* ── Review relationships ── */
Review.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Review.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });

/* ── Notification relationships ── */
Notification.belongsTo(User, { foreignKey: 'recipient_id', as: 'recipientUser' });

/* ── Cart relationships ── */
Cart.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Cart.hasMany(CartItem, { foreignKey: 'cart_id', as: 'items' });

/* ── CartItem relationships ── */
CartItem.belongsTo(Cart, { foreignKey: 'cart_id', as: 'cart' });
CartItem.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });

/* ── Wishlist relationships ── */
Wishlist.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Wishlist.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });

/* ── Subscription relationships ── */
Subscription.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Subscription.belongsTo(Plan, { foreignKey: 'plan_id', as: 'plan' });
Plan.hasMany(Subscription, { foreignKey: 'plan_id', as: 'subscriptions' });

/* ── AnalyticsEvent relationships ── */
AnalyticsEvent.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

/* ── Address relationships ── */
Address.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

/* ── Booking / Doctor / Service relationships ── */
Booking.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Booking.belongsTo(Doctor, { foreignKey: 'doctor_id', as: 'doctor' });
Booking.belongsTo(Service, { foreignKey: 'service_id', as: 'service' });
Doctor.hasMany(Booking, { foreignKey: 'doctor_id', as: 'bookings' });
Service.hasMany(Booking, { foreignKey: 'service_id', as: 'bookings' });

/* ── AuditLog (no direct associations — queried via user_id) ── */

/* ── Multi-tenancy: Organization ↔ Role ↔ Permission ↔ Membership ── */
Organization.belongsTo(User, { foreignKey: 'owner_id', as: 'owner' });
Organization.hasMany(Role, { foreignKey: 'org_id', as: 'roles' });
Organization.hasMany(Membership, { foreignKey: 'org_id', as: 'memberships' });

User.belongsTo(Organization, { foreignKey: 'current_org_id', as: 'activeOrg' });
User.hasMany(Membership, { foreignKey: 'user_id', as: 'memberships' });

Role.belongsTo(Organization, { foreignKey: 'org_id', as: 'organization' });
Role.belongsToMany(Permission, { through: 'role_permissions', foreignKey: 'role_id' });
Permission.belongsToMany(Role, { through: 'role_permissions', foreignKey: 'permission_id' });

Membership.belongsTo(Organization, { foreignKey: 'org_id', as: 'organization' });
Membership.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Membership.belongsTo(Role, { foreignKey: 'role_id', as: 'role' });

/* ── Tenant-scoped resources (nullable org_id = legacy single-tenant) ── */
Product.belongsTo(Organization, { foreignKey: 'org_id', as: 'organization' });
Order.belongsTo(Organization, { foreignKey: 'org_id', as: 'organization' });
Organization.hasMany(Product, { foreignKey: 'org_id', as: 'products' });
Organization.hasMany(Order, { foreignKey: 'org_id', as: 'orders' });

/* ── Sync ── */
export async function syncModels() {
  await sequelize.sync({ alter: process.env.NODE_ENV === 'development' });
}

export {
  sequelize,
  User,
  Product,
  Order,
  Payment,
  Review,
  Notification,
  Category,
  Cart,
  CartItem,
  Wishlist,
  Subscription,
  Plan,
  AnalyticsEvent,
  Coupon,
  Address,
  WebhookEvent,
  AuditLog,
  Organization,
  Role,
  Permission,
  Membership,
  Booking,
  Doctor,
  Service,
};