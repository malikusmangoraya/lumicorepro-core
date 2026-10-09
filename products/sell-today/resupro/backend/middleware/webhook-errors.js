"use strict";

/**
 * webhookErrors middleware
 * Wraps webhook route handlers to convert thrown errors into non-user-facing
 * responses and log structured context.
 */
function webhookErrors(logger) {
  return (req, res, next) => {
    try {
      next();
    } catch (err) {
      logger.error("webhook handler error", {
        eventId: req.headers["x-event-id"] || "unknown",
        eventType: req.headers["x-event-name"] || "unknown",
        error: err.message,
      });
      res.status(500).json({ success: false, error: "webhook processing failed" });
    }
  };
}

module.exports = webhookErrors;
