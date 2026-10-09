// LUMICORE_REPAIR: role-based access gate (requirePermission).
const requirePermission = (permission) => (req, res, next) => {
  const perms = (req.user && req.user.permissions) || [];
  if (!perms.includes(permission))
    return res.status(403).json({ success: false, message: 'Forbidden' });
  return next();
};

module.exports = { requirePermission };
