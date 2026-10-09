// LUMICORE_REPAIR: multi-tenant scope gate (requireOrg).
const requireOrg = (req, res, next) => {
  const orgId = req.headers['x-org-id'] || (req.user && req.user.current_org_id);
  if (!orgId) return res.status(403).json({ success: false, message: 'Org scope required' });
  req.orgId = orgId;
  return next();
};

module.exports = { requireOrg };
