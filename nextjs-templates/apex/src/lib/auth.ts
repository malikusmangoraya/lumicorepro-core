import { cookies } from 'next/headers';
import { SignJWT, jwtVerify, type JWTPayload } from 'jose';
import bcrypt from 'bcryptjs';

const ACCESS_COOKIE = 'apex_access';
const REFRESH_COOKIE = 'apex_refresh';

export type SessionUser = {
  id: string;
  email: string;
  name: string;
  role: 'customer' | 'admin';
};

function secret(name: 'JWT_SECRET' | 'JWT_REFRESH_SECRET'): Uint8Array {
  const value = process.env[name] ?? (name === 'JWT_REFRESH_SECRET' ? process.env.JWT_SECRET : '');
  if (!value || value.length < 32) {
    throw new Error(
      `${name} must be set to at least 32 characters. Copy .env.example and fill it in.`,
    );
  }
  return new TextEncoder().encode(value);
}

const accessTtl = () => process.env.JWT_EXPIRES_IN || '15m';
const refreshTtl = () => process.env.JWT_REFRESH_EXPIRES_IN || '30d';

export async function signAccessToken(user: SessionUser) {
  return new SignJWT({ email: user.email, name: user.name, role: user.role })
    .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
    .setSubject(user.id)
    .setIssuedAt()
    .setExpirationTime(accessTtl())
    .sign(secret('JWT_SECRET'));
}

export async function signRefreshToken(userId: string) {
  return new SignJWT({ type: 'refresh' })
    .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
    .setSubject(userId)
    .setIssuedAt()
    .setExpirationTime(refreshTtl())
    .sign(secret('JWT_REFRESH_SECRET'));
}

export async function verifyToken(token: string, kind: 'access' | 'refresh' = 'access') {
  try {
    const { payload } = await jwtVerify(
      token,
      secret(kind === 'access' ? 'JWT_SECRET' : 'JWT_REFRESH_SECRET'),
    );
    if (kind === 'refresh' && payload.type !== 'refresh') return null;
    return payload as JWTPayload & Partial<SessionUser>;
  } catch {
    return null;
  }
}

export async function hashPassword(password: string) {
  return bcrypt.hash(password, 12);
}

export async function verifyPassword(password: string, hash: string) {
  return bcrypt.compare(password, hash);
}

export async function setSessionCookies(user: SessionUser) {
  const [access, refresh] = await Promise.all([
    signAccessToken(user),
    signRefreshToken(user.id),
  ]);
  const jar = await cookies();
  const secure = process.env.NODE_ENV === 'production';
  jar.set(ACCESS_COOKIE, access, {
    httpOnly: true,
    sameSite: 'lax',
    secure,
    path: '/',
    maxAge: 60 * 15,
  });
  jar.set(REFRESH_COOKIE, refresh, {
    httpOnly: true,
    sameSite: 'lax',
    secure,
    path: '/',
    maxAge: 60 * 60 * 24 * 30,
  });
  return { access, refresh };
}

export async function clearSessionCookies() {
  const jar = await cookies();
  jar.delete(ACCESS_COOKIE);
  jar.delete(REFRESH_COOKIE);
}

/** Read the signed-in user from the HttpOnly access cookie, or null. */
export async function getSession(): Promise<SessionUser | null> {
  const jar = await cookies();
  const token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) return null;
  const payload = await verifyToken(token, 'access');
  if (!payload?.sub) return null;
  return {
    id: String(payload.sub),
    email: String(payload.email ?? ''),
    name: String(payload.name ?? ''),
    role: (payload.role === 'admin' ? 'admin' : 'customer') as SessionUser['role'],
  };
}

export async function requireUser(): Promise<SessionUser> {
  const user = await getSession();
  if (!user) throw new Error('UNAUTHORIZED');
  return user;
}

export async function requireAdmin(): Promise<SessionUser> {
  const user = await requireUser();
  if (user.role !== 'admin') throw new Error('FORBIDDEN');
  return user;
}

export { ACCESS_COOKIE, REFRESH_COOKIE };
