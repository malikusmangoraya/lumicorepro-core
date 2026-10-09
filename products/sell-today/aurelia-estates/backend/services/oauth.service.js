/**
 * OAuth (Passport) Strategies — Google & GitHub
 * ---------------------------------------------
 * JWT-based sessionless OAuth. After a successful provider callback we issue
 * our own signed JWT (same format as auth routes) instead of a passport session.
 * Configure with GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET and
 * GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET in .env.
 */
import passport from 'passport';
import { Strategy as GoogleStrategy } from 'passport-google-oauth20';
import { Strategy as GitHubStrategy } from 'passport-github2';
import User from '../models/User.js';
import logger from '../utils/logger.js';

function buildJwtPayload(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    avatar: user.avatar || '',
    preferences: user.preferences || {},
    oauthProvider: user.oauthProvider,
  };
}

async function upsertOAuthUser(profile) {
  const email = (
    (profile.emails && profile.emails[0] && profile.emails[0].value) ||
    ''
  ).toLowerCase();
  const provider = profile.provider === 'google' ? 'google' : 'github';
  const oauthId = String(profile.id);

  let user = null;
  try {
    user = await User.findOne({ where: { email } });
  } catch (err) {
    logger.warn(`OAuth DB lookup failed for ${email}: ${err.message}`);
  }

  if (user) {
    // Link the OAuth identity if not already linked
    if (user.oauthProvider !== provider) {
      try {
        await user.update({ oauthProvider: provider, oauthId });
      } catch {
        /* ignore on offline fallback models */
      }
    }
    return user;
  }

  try {
    user = await User.create({
      name: profile.displayName || email.split('@')[0],
      email,
      password: require('crypto').randomBytes(24).toString('hex'),
      avatar: (profile.photos && profile.photos[0] && profile.photos[0].value) || '',
      isVerified: true,
      isActive: true,
      oauthProvider: provider,
      oauthId,
      preferences: { theme: 'dark', language: 'en', notifications: { email: true, push: true } },
    });
  } catch (err) {
    logger.warn(`OAuth user creation failed, using in-memory user: ${err.message}`);
    const bcrypt = require('bcryptjs');
    user = {
      id: Date.now(),
      name: profile.displayName || email.split('@')[0],
      email,
      password: await bcrypt.hash(require('crypto').randomBytes(24).toString('hex'), 12),
      role: 'user',
      avatar: (profile.photos && profile.photos[0] && profile.photos[0].value) || '',
      isActive: true,
      twoFactorEnabled: false,
      oauthProvider: provider,
      oauthId,
      preferences: { theme: 'dark', language: 'en' },
      save: async function () {
        return this;
      },
    };
  }
  return user;
}

export function configureOAuth() {
  const googleId = process.env.GOOGLE_CLIENT_ID;
  const googleSecret = process.env.GOOGLE_CLIENT_SECRET;
  const githubId = process.env.GITHUB_CLIENT_ID;
  const githubSecret = process.env.GITHUB_CLIENT_SECRET;
  const baseUrl = process.env.BACKEND_URL || `http://localhost:${process.env.PORT || 5000}`;

  if (googleId && googleSecret) {
    passport.use(
      new GoogleStrategy(
        {
          clientID: googleId,
          clientSecret: googleSecret,
          callbackURL: `${baseUrl}/api/auth/oauth/google/callback`,
        },
        async (accessToken, refreshToken, profile, done) => {
          try {
            const user = await upsertOAuthUser(profile);
            done(null, buildJwtPayload(user));
          } catch (err) {
            done(err, null);
          }
        }
      )
    );
  }

  if (githubId && githubSecret) {
    passport.use(
      new GitHubStrategy(
        {
          clientID: githubId,
          clientSecret: githubSecret,
          callbackURL: `${baseUrl}/api/auth/oauth/github/callback`,
          scope: ['user:email'],
        },
        async (accessToken, refreshToken, profile, done) => {
          try {
            const user = await upsertOAuthUser(profile);
            done(null, buildJwtPayload(user));
          } catch (err) {
            done(err, null);
          }
        }
      )
    );
  }

  return passport;
}

export default configureOAuth;
