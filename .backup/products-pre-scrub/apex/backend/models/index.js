const Address = require('./Address');
const AnalyticsEvent = require('./AnalyticsEvent');
const AuditLog = require('./AuditLog');
const Booking = require('./Booking');
const Cart = require('./Cart');
const CartItem = require('./CartItem');
const Category = require('./Category');
const Coupon = require('./Coupon');
const Doctor = require('./Doctor');
const Membership = require('./Membership');
const Notification = require('./Notification');
const Order = require('./Order');
const Organization = require('./Organization');
const Payment = require('./Payment');
const Permission = require('./Permission');
const Plan = require('./Plan');
const Product = require('./Product');
const Review = require('./Review');
const Role = require('./Role');
const Service = require('./Service');
const Subscription = require('./Subscription');
const SystemConfig = require('./SystemConfig');
const User = require('./User');
const WebhookEvent = require('./WebhookEvent');
const WebhookLog = require('./WebhookLog');
const Wishlist = require('./Wishlist');

User.hasMany(Order, { foreignKey: 'user_id', as: 'orders' });
User.hasMany(Payment, { foreignKey: 'user_id', as: 'payments' });
User.hasMany(Review, { foreignKey: 'user_id', as: 'reviews' });
User.hasMany(Notification, { foreignKey: 'recipient_id', as: 'notifications' });
User.hasOne(Cart, { foreignKey: 'user_id', as: 'cart' });
User.hasMany(Wishlist, { foreignKey: 'user_id', as: 'wishlists' });
User.hasMany(Subscription, { foreignKey: 'user_id', as: 'subscriptions' });
User.hasMany(AnalyticsEvent, { foreignKey: 'user_id', as: 'analyticsEvents' });
User.hasMany(Address, { foreignKey: 'user_id', as: 'addresses' });
User.hasMany(Coupon, { foreignKey: 'user_id', as: 'coupons' });
Product.belongsTo(Category, { foreignKey: 'category_id', as: 'categoryDetail' });
Product.belongsTo(User, { foreignKey: 'vendor_id', as: 'vendor' });
Product.hasMany(Review, { foreignKey: 'product_id', as: 'reviews' });
Product.hasMany(CartItem, { foreignKey: 'product_id', as: 'cartItems' });
Product.hasMany(Wishlist, { foreignKey: 'product_id', as: 'wishlists' });
Category.hasMany(Product, { foreignKey: 'category_id', as: 'products' });
Order.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Order.belongsTo(Coupon, { foreignKey: 'coupon_id', as: 'coupon' });
Order.hasMany(Payment, { foreignKey: 'order_id', as: 'payments' });
Payment.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Payment.belongsTo(Order, { foreignKey: 'order_id', as: 'order' });
Review.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Review.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });
Notification.belongsTo(User, { foreignKey: 'recipient_id', as: 'recipientUser' });
Cart.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Cart.hasMany(CartItem, { foreignKey: 'cart_id', as: 'items' });
CartItem.belongsTo(Cart, { foreignKey: 'cart_id', as: 'cart' });
CartItem.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });
Wishlist.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Wishlist.belongsTo(Product, { foreignKey: 'product_id', as: 'product' });
Subscription.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Subscription.belongsTo(Plan, { foreignKey: 'plan_id', as: 'plan' });
Plan.hasMany(Subscription, { foreignKey: 'plan_id', as: 'subscriptions' });
AnalyticsEvent.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Address.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Coupon.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Booking.belongsTo(User, { foreignKey: 'user_id', as: 'user' });
Booking.belongsTo(Doctor, { foreignKey: 'doctor_id', as: 'doctor' });
Booking.belongsTo(Service, { foreignKey: 'service_id', as: 'service' });
Doctor.hasMany(Booking, { foreignKey: 'doctor_id', as: 'bookings' });
Service.hasMany(Booking, { foreignKey: 'service_id', as: 'bookings' });
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
Product.belongsTo(Organization, { foreignKey: 'org_id', as: 'organization' });
Order.belongsTo(Organization, { foreignKey: 'org_id', as: 'organization' });
Organization.hasMany(Product, { foreignKey: 'org_id', as: 'products' });
Organization.hasMany(Order, { foreignKey: 'org_id', as: 'orders' });
Organization.hasMany(Invoice, { foreignKey: 'org_id', as: 'invoices' });
Organization.hasMany(Transaction, { foreignKey: 'org_id', as: 'transactions' });

module.exports = {
  Address,
  AnalyticsEvent,
  AuditLog,
  Booking,
  Cart,
  CartItem,
  Category,
  Coupon,
  Doctor,
  Membership,
  Notification,
  Order,
  Organization,
  Payment,
  Permission,
  Plan,
  Product,
  Review,
  Role,
  Service,
  Subscription,
  SystemConfig,
  User,
  WebhookEvent,
  WebhookLog,
  Wishlist,
};
