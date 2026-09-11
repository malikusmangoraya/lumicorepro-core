/**
 * User Service (business logic over repositories)
 * -----------------------------------------------
 * Controllers call services, services call repositories. Keeps SQL/Schema out
 * of controllers and provides a seam for DI injectable mocks in tests.
 */
import { UserRepository } from '../repositories/user.repository.js';

const userRepo = new UserRepository();

/** Eager-loads user relations in one query. */
export async function getProfile(userId, { includeRelations = false } = {}) {
  if (includeRelations) {
    const user = await userRepo.findByIdWithRelations(userId);
    if (!user) return null;
    const plain = user.toJSON ? user.toJSON() : { ...user };
    delete plain.password;
    return plain;
  }
  const user = await userRepo.findById(userId);
  if (!user) return null;
  const plain = user.toJSON ? user.toJSON() : { ...user };
  delete plain.password;
  return plain;
}

export async function updateProfile(userId, updates) {
  const updated = await userRepo.update(userId, updates);
  if (!updated) return null;
  const plain = updated.toJSON ? updated.toJSON() : { ...updated };
  delete plain.password;
  return plain;
}

export default {
  getProfile,
  updateProfile,
};