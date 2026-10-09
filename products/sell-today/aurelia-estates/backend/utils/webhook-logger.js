"use strict";

const pino = require("pino");

let logger = null;

function getLogger() {
  if (logger) return logger;
  logger = pino({
    level: process.env.LOG_LEVEL || "info",
    base: {
      provider: "payments-webhook",
    },
  });
  return logger;
}

module.exports = { getLogger };
