/**
 * Model registry + associations.
 *
 * Most model files are ES modules (`export default`) while this registry is
 * CommonJS, so `require()` hands back the module namespace rather than the
 * model class. Unwrapping `default` here is what lets the associations below
 * receive real Sequelize models instead of plain namespace objects.
 *
 * The check is `typeof mod !== 'function'` on purpose: a Sequelize model class
 * is a function that also carries a `.default` object property, so testing for
 * `default` alone would replace the model with an unrelated value.
 */
const unwrap = (mod) =>
  typeof mod === 'function' ? mod : mod && mod.default ? mod.default : mod;

const Address = unwrap(require('./Address'));
const AnalyticsEvent = unwrap(require('./AnalyticsEvent'));
const AuditLog = unwrap(require('./AuditLog'));
const Booking = unwrap(require('./Booking'));
const Cart = unwrap(require('./Cart'));
const CartItem = unwrap(require('./CartItem'));
const Category = unwrap(require('./Category'));
const Coupon = unwrap(require('./Coupon'));
const Doctor = unwrap(require('./Doctor'));
const Inquiry = unwrap(require('./Inquiry'));
const Membership = unwrap(require('./Membership'));
const Notification = unwrap(require('./Notification'));
const Order = unwrap(require('./Order'));
const Organization = unwrap(require('./Organization'));
const Payment = unwrap(require('./Payment'));
const Permission = unwrap(require('./Permission'));
const Plan = unwrap(require('./Plan'));
const Product = unwrap(require('./Product'));
const Review = unwrap(require('./Review'));
const Role = unwrap(require('./Role'));
const Service = unwrap(require('./Service'));
const Subscription = unwrap(require('./Subscription'));
const SystemConfig = unwrap(require('./SystemConfig'));
const User = unwrap(require('./User'));
const Vehicle = unwrap(require('./Vehicle'));
const WebhookEvent = unwrap(require('./WebhookEvent'));
const WebhookLog = unwrap(require('./WebhookLog'));
const Wishlist = unwrap(require('./Wishlist'));

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

// ── Apex dealership inventory ───────────────────────────────────────────────
// A vehicle is owned by the dealership, not by a user, so it has no owner
// association. Reservation associations are added with that model.
Vehicle.hasMany(Inquiry, { foreignKey: 'vehicle_id', as: 'inquiries' });
Inquiry.belongsTo(Vehicle, { foreignKey: 'vehicle_id', as: 'vehicle' });
// `user_id` is null for anonymous enquiries, so this is a nullable relation.
User.hasMany(Inquiry, { foreignKey: 'user_id', as: 'inquiries' });
Inquiry.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

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
  Inquiry,
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
  Vehicle,
  WebhookEvent,
  WebhookLog,
  Wishlist,
};
