/**
 * User Controller (thin HTTP-layer)
 * ---------------------------------
 * Parses the request, delegates to the service, returns standardized responses.
 * No DB access here — services own business logic.
 */
import resp from '../utils/response.js';
import userService from '../services/userService.js';

export const getProfile = async (req, res, next) => {
  try {
    const user = await userService.getProfile(req.user.id);
    if (!user) return resp.sendNotFound(res, 'User');
    return resp.sendSuccess(res, user);
  } catch (err) {
    next(err);
  }
};

export const updateProfile = async (req, res, next) => {
  try {
    const updates = {};
    for (const field of ['name', 'phone', 'avatar', 'address', 'preferences']) {
      if (req.body[field] !== undefined) updates[field] = req.body[field];
    }
    const user = await userService.updateProfile(req.user.id, updates);
    if (!user) return resp.sendNotFound(res, 'User');
    return resp.sendSuccess(res, user);
  } catch (err) {
    next(err);
  }
};

export default { getProfile, updateProfile };
