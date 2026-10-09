/**
 * Dependency Injection Container (Awilix)
 * ---------------------------------------
 * Centrally registers services, repositories and controllers instead of manual
 * require() chains. Tests can register mock objects in place of real services
 * (container.register({ paymentGateway: asValue(fake) })).
 */
import { createContainer, asValue, asFunction, asClass, Lifetime } from 'awilix';
import logger from '../utils/logger.js';
import cache from '../services/cache/cache.service.js';
import queue from '../services/queue/queue.service.js';
import refreshToken from '../services/refreshToken.service.js';
import response from '../utils/response.js';
import validateRequest from '../middleware/validateRequest.js';
import * as auth from '../middleware/auth.js';
import * as ratelimit from '../middleware/rateLimit.js';

const container = createContainer();

// Core infrastructure (always available)
container.register({
  logger: asValue(logger),
  cache: asValue(cache),
  queue: asValue(queue),
  refreshToken: asValue(refreshToken),
  response: asValue(response),
  validateRequest: asValue(validateRequest),
  authMiddleware: asValue(auth),
  rateLimit: asValue(ratelimit),
});

// Models & repositories — registered as classes (registered lazily, resolved on demand)
import User from '../models/User.js';
container.register({
  User: asClass(User).singleton(),
});

/** Loose DI lookup with lazy import of services to keep startup fast. */
export async function resolve(name) {
  if (!container.hasRegistration(name)) {
    // try to lazy-load from the services dir by convention
    try {
      const mod = await import(`../services/${name}.service.js`);
      const value = mod.default || mod[name];
      if (value) container.register({ [name]: asValue(value) });
    } catch {
      /* not a service */
    }
  }
  if (container.hasRegistration(name)) {
    return container.resolve(name);
  }
  return null;
}

export function register(name, value) {
  container.register({ [name]: asValue(value) });
}

export default {
  container,
  resolve,
  register,
  asClass,
  asFunction,
  asValue,
  Lifetime,
};
