"use strict";

const http = require("http");

function startHealthServer(port) {
  const srv = http.createServer((req, res) => {
    if (req.url === "/health" && req.method === "GET") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        success: true,
        status: "ok",
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
      }));
    } else {
      res.writeHead(404);
      res.end();
    }
  });

  srv.listen(port, () => {
    console.log(`healthcheck listening on :${port}`);
  });

  return srv;
}

module.exports = { startHealthServer };
