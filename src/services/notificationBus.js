/**
 * notificationBus — module-level bridge from non-React code to the toast surface.
 *
 * React Query cache callbacks are created once, outside the React tree, so they
 * cannot call `useNotifications()`. `ToastRegion` registers the live handler on
 * mount; anything that runs before a handler exists is dropped instead of
 * throwing (SSR, unit tests that render no shell).
 */

let handler = null;

/**
 * Register the toast producer.
 * @param {(message: string, type: string) => void} fn
 * @returns {() => void} unregister
 */
export function registerNotificationHandler(fn) {
  handler = fn;
  return () => {
    if (handler === fn) handler = null;
  };
}

/**
 * Surface a notification if a toast region is mounted.
 * @param {string} message
 * @param {'info'|'success'|'warning'|'error'} [type]
 */
export function notify(message, type = 'info') {
  if (!message || !handler) return;
  handler(message, type);
}

/** Human-readable text for an axios/fetch/Error failure. */
export function describeError(error, fallback = 'Request failed. Please try again.') {
  return (
    error?.response?.data?.message ||
    error?.response?.data?.error ||
    error?.message ||
    fallback
  );
}

/**
 * Report a failed query/mutation through the toast surface.
 * @param {unknown} error
 * @param {string} [fallback]
 */
export function notifyError(error, fallback) {
  notify(describeError(error, fallback), 'error');
}

export default { notify, notifyError, describeError, registerNotificationHandler };
