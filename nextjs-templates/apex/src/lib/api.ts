import { NextResponse } from 'next/server';

/**
 * One response shape for every route handler, matching the convention the
 * Express backend used: { success, status, message, data, timestamp }.
 * Errors add a machine-readable `code` and keep `data: null`.
 */
export type ApiSuccess<T> = {
  success: true;
  status: number;
  message: string;
  data: T;
  timestamp: string;
};

export type ApiFailure = {
  success: false;
  status: number;
  message: string;
  code: string;
  data: null;
  details?: unknown;
  timestamp: string;
};

export function ok<T>(data: T, message = 'OK', status = 200) {
  return NextResponse.json<ApiSuccess<T>>(
    { success: true, status, message, data, timestamp: new Date().toISOString() },
    { status },
  );
}

export function created<T>(data: T, message = 'Created') {
  return ok(data, message, 201);
}

export function fail(code: string, message: string, status = 400, details?: unknown) {
  return NextResponse.json<ApiFailure>(
    {
      success: false,
      status,
      message,
      code,
      data: null,
      ...(details === undefined ? {} : { details }),
      timestamp: new Date().toISOString(),
    },
    { status },
  );
}

export const unauthorized = (message = 'Authentication required') =>
  fail('UNAUTHORIZED', message, 401);
export const forbidden = (message = 'Forbidden') => fail('FORBIDDEN', message, 403);
export const notFound = (resource = 'Resource') =>
  fail('NOT_FOUND', `${resource} not found`, 404);
export const validate = (details: unknown) =>
  fail('VALIDATION_ERROR', 'Validation failed', 422, details);
export const tooMany = (message = 'Too many requests') =>
  fail('RATE_LIMITED', message, 429);
export const serverError = (message = 'Internal server error') =>
  fail('INTERNAL_ERROR', message, 500);
