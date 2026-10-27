"""The realtime gate: every generated product ships an SSE change feed, and a
generated product that cannot prove "write -> push -> client refetches" is not
called live.

These probes run the GENERATED JavaScript under real Node with a stub express
that captures route handlers, so what is asserted is the code a client receives,
not a Python-side description of it.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from agent.production_spec_kit import apply_production_spec

ZERO_UUID = "00000000-0000-0000-0000-000000000000"

# A stub express that records handlers so a test can drive them with fake req/res.
_EXPRESS_STUB = """\
const routes = [];
function router() {
  const r = { use() {}, _all: [] };
  for (const verb of ['get', 'post', 'put', 'delete']) {
    r[verb] = (path, ...handlers) => { const h = { verb, path, handlers }; r._all.push(h); routes.push(h); return r; };
  }
  return r;
}
module.exports = () => {
  const app = { use() { return app; }, listen() { return app; }, get() { return app; } };
  app.json = () => (req, res, next) => next();
  app.Router = router;
  return app;
};
module.exports.Router = router;
module.exports.json = () => (req, res, next) => next();
module.exports.routes = routes;
"""

_JSONwebtoken_STUB = """\
module.exports = {
  verify: (token) => {
    if (token === 'expired' || token === 'bad') throw new Error('jwt expired');
    if (token === 'subjectless') return { email: 'x@y.z' };
    return { id: 'user-1', email: 'owner@acme.test' };
  },
  sign: () => 't',
};
"""

# sequelize.query records every statement + bind it is handed, and answers from a
# script the test writes to REALTIME_ROWS_FILE (JSON: {"records": [...], ...}).
_SEQUELIZE_STUB = """\
function rowsFor(sql) {
  const script = process.env.REALTIME_ROWS_FILE || '';
  let table = 'records';
  if (sql.includes('contact_messages')) table = 'contact';
  if (!script) return [];
  const data = JSON.parse(require('fs').readFileSync(script, 'utf8'));
  return data[table] || [];
}
const sequelize = {
  __calls: [],
  define: (name) => ({ _name: name, findAll: async () => [], findOne: async () => null,
                       create: async (x) => ({ id: 'row-new', ...x }), destroy: async () => 1 }),
  query: async (sql, options) => {
    sequelize.__calls.push({ sql, bind: (options && options.bind) || [] });
    if (process.env.REALTIME_FAIL_QUERIES === '1') throw new Error('connection terminated');
    return rowsFor(sql);
  },
};
module.exports = {
  DataTypes: { STRING: (n) => ({ _s: 'string', n }), TEXT: 'TEXT', ENUM: (v) => ({ _s: 'enum', v }),
               UUID: 'UUID', UUIDV4: 'UUIDV4', DATE: 'DATE' },
  sequelize,
  QueryTypes: { SELECT: 'SELECT' },
};
"""

_REDIS_STUB = """\
const created = [];
function client(url) {
  const c = {
    url, isReady: false, status: 'connecting', published: [],
    on() { return c; },
    async connect() { c.isReady = true; c.status = 'ready'; return {}; },
    async publish(channel, message) { c.published.push([channel, message]); return 1; },
    async subscribe(channel, handler) { c.handler = handler; return {}; },
  };
  created.push(c);
  return c;
}
module.exports = { createClient: client, clients: created };
"""


@pytest.fixture()
def project(tmp_path):
    backend = tmp_path / "backend"
    (backend / "migrations").mkdir(parents=True)
    (backend / "routes").mkdir()
    (backend / "models").mkdir()
    (backend / "utils").mkdir()
    (backend / "services").mkdir()
    (backend / "package.json").write_text(json.dumps(
        {"name": "realtime-app", "scripts": {}, "dependencies": {"express": "^4.19.0"}}),
        encoding="utf-8")
    (backend / "server.js").write_text(
        "const app = express();\n"
        "app.use('/api/v1/auth', authRoutes);\n"
        "app.use('/api/v1/health', healthRoutes);\n"
        "module.exports = app;\n", encoding="utf-8")
    (backend / "models" / "index.js").write_text(
        "module.exports = require('./_stub.js');\n", encoding="utf-8")
    (backend / "utils" / "jwtSecret.js").write_text(
        "module.exports = { jwtSecret: 'probe-secret-'.padEnd(40, 'x') };\n", encoding="utf-8")

    nm = backend / "node_modules"
    for name, source in {"express": _EXPRESS_STUB, "jsonwebtoken": _JSONwebtoken_STUB,
                         "sequelize": _SEQUELIZE_STUB}.items():
        d = nm / name
        d.mkdir(parents=True)
        (d / "package.json").write_text(json.dumps({"name": name, "main": "index.js"}), encoding="utf-8")
        (d / "index.js").write_text(source, encoding="utf-8")
    (backend / "models" / "_stub.js").write_text(_SEQUELIZE_STUB, encoding="utf-8")

    frontend = tmp_path / "frontend"
    (frontend / "src" / "pages").mkdir(parents=True)
    (frontend / "src" / "pages" / "Dashboard.jsx").write_text(
        "<div>Control Console static</div>", encoding="utf-8")
    # Generate first: these probes must run the code a client would receive, so
    # the fixture produces it and only then inspects it.
    apply_production_spec(str(tmp_path), brand="RealtimeApp")
    return tmp_path


def _env_for(project: Path, rows: dict, *, fail: bool = False, extra: dict = None) -> dict:
    """Node's environment for one probe: which rows the stubbed driver returns
    and how long the stream is allowed to live, so no test waits on a default."""
    path = project / "_rows.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    env = dict(os.environ)
    env["REALTIME_ROWS_FILE"] = str(path)
    if fail:
        env["REALTIME_FAIL_QUERIES"] = "1"
    env.update(extra or {})
    return env


def _probe(project: Path, snippet: str, env: dict = None) -> subprocess.CompletedProcess:
    """Probe bodies are written as if top-level await existed: they run inside an
    async main() so a rejection is reported instead of silently exiting 0."""
    entry = project / "backend" / "_probe.cjs"
    entry.write_text(
        _HARNESS + "\n(async () => {\n" + snippet
        + "\n})().catch((e) => { console.error('PROBE_ERROR: ' + ((e && e.stack) || e)); "
        "process.exit(1); });\n",
        encoding="utf-8")
    try:
        return subprocess.run(["node", str(entry)], cwd=str(project / "backend"),
                              capture_output=True, text=True, timeout=90,
                              env=env or dict(os.environ))
    finally:
        entry.unlink(missing_ok=True)


# --- harness injected into every probe: fake req/res that speak HTTP ---------

_HARNESS = """\
const express = require('express');
const { EventEmitter } = require('events');

function makeRes() {
  const res = new EventEmitter();
  const frames = [];
  const headers = {};
  res.statusCode = 200;
  res.headersSent = false;
  res.writableEnded = false;
  res.status = (code) => { res.statusCode = code; return res; };
  res.set = (entries) => { Object.entries(entries).forEach(([k, v]) => { headers[k.toLowerCase()] = v; }); return res; };
  res.setHeader = (k, v) => { headers[k.toLowerCase()] = v; };
  res.getHeader = (k) => headers[k.toLowerCase()];
  res.flushHeaders = () => { res.headersSent = true; };
  res.write = (chunk) => { res.headersSent = true; frames.push(String(chunk)); return true; };
  res.end = () => { res.writableEnded = true; };
  res.json = (body) => { frames.push(JSON.stringify(body)); res.end(); };
  res.headers = headers;
  res.frames = frames;
  res.text = () => frames.join('');
  return res;
}

function makeReq({ token = null, query = {}, headers = {} } = {}) {
  const req = new EventEmitter();
  req.headers = { ...headers };
  if (token) req.headers.authorization = `Bearer ${token}`;
  req.query = query;
  req.method = 'GET';
  req.path = '/api/v1/events';
  req.socket = { remoteAddress: '127.0.0.1' };
  return req;
}

function eventsRoute() {
  const before = (express.routes || []).length;
  const mod = require('./routes/events.routes.js');
  const added = (express.routes || []).slice(before);
  const route = mod._all.filter((h) => h.path === '/')[0] || added.filter((h) => h.verb === 'get')[0];
  if (!route) throw new Error('the events router registers no GET /');
  return { mod, route };
}

async function collect(route, req, res, ms) {
  await route.handlers[route.handlers.length - 1](req, res, (e) => { throw e; });
  await new Promise((resolve) => setTimeout(resolve, ms));
}
"""


def _run_stream_probe(project, body: str, rows: dict, *, env: dict = None, fail: bool = False) -> str:
    """Boot the generated SSE route under Node and return the probe's stdout."""
    res = _probe(project, body, _env_for(project, rows, fail=fail, extra=env))
    assert res.returncode == 0, f"node probe failed:\n{res.stdout}\n{res.stderr}"
    assert "PROBE_ERROR" not in res.stderr, res.stderr
    return res.stdout


# --------------------------------------------------------------------------
# 1. the files exist, are mounted, and the frontend can actually subscribe
# --------------------------------------------------------------------------

def test_every_generated_project_gets_the_change_feed(project):
    apply_production_spec(str(project), brand="RealtimeApp")
    for rel in ("backend/routes/events.routes.js", "backend/services/changeBus.js",
                "frontend/src/hooks/useRealtime.js"):
        assert (project / rel).exists(), rel
    server = (project / "backend" / "server.js").read_text(encoding="utf-8")
    assert "require('./routes/events.routes')" in server


def test_the_dashboard_subscribes_instead_of_sitting_still(project):
    apply_production_spec(str(project), brand="RealtimeApp")
    dashboard = (project / "frontend" / "src" / "pages" / "Dashboard.jsx").read_text(encoding="utf-8")
    assert "useRealtime" in dashboard, "the dashboard must open the feed, not just render once"
    hook = (project / "frontend" / "src" / "hooks" / "useRealtime.js").read_text(encoding="utf-8")
    for necessity in ("EventSource", "close()", "clearInterval"):
        assert necessity in hook, necessity
    assert "setInterval" in hook, "a dead stream must fall back to polling, not go silent"


def test_the_feed_mount_is_idempotent(project):
    apply_production_spec(str(project), brand="RealtimeApp")
    first = (project / "backend" / "server.js").read_text(encoding="utf-8")
    apply_production_spec(str(project), brand="RealtimeApp")
    second = (project / "backend" / "server.js").read_text(encoding="utf-8")
    assert second.count("require('./routes/events.routes')") == 1
    assert first == second


# --------------------------------------------------------------------------
# 2. authentication — an anonymous visitor must never receive a live feed
# --------------------------------------------------------------------------

def test_anonymous_streaming_is_refused(project):
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
const res = makeRes();
await route.handlers[route.handlers.length - 1](makeReq(), res, (e) => { throw e; });
console.log(JSON.stringify({ code: res.statusCode, ctype: res.headers['content-type'] || '', body: res.text() }));
""", {"records": []})
    evidence = json.loads(out.strip().splitlines()[-1])
    assert evidence["code"] == 401, evidence
    assert "text/event-stream" not in evidence["ctype"], "a 401 must not have opened a stream"


def test_a_forged_token_is_refused(project):
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
const res = makeRes();
await route.handlers[route.handlers.length - 1](makeReq({ token: 'expired' }), res, (e) => { throw e; });
console.log(JSON.stringify({ code: res.statusCode }));
""", {"records": []})
    assert json.loads(out.strip().splitlines()[-1])["code"] == 401


def test_the_token_is_accepted_from_a_query_param_because_eventsource_has_no_headers(project):
    """EventSource cannot set Authorization, so ?token= is the only way a browser
    can authenticate a stream. Both spellings must work or the feature is dead."""
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
const handler = route.handlers[route.handlers.length - 1];
process.env.SSE_MAX_MS = '60'; process.env.SSE_POLL_MS = '20';
const byHeader = makeRes();
await handler(makeReq({ token: 'good' }), byHeader, (e) => { throw e; });
const byQuery = makeRes();
await handler(makeReq({ query: { token: 'good' } }), byQuery, (e) => { throw e; });
const subjectless = makeRes();
await handler(makeReq({ token: 'subjectless' }), subjectless, (e) => { throw e; });
console.log(JSON.stringify({
  header: byHeader.statusCode, headerType: byHeader.headers['content-type'] || '',
  query: byQuery.statusCode, queryType: byQuery.headers['content-type'] || '',
  subjectless: subjectless.statusCode,
}));
""", {"records": []})
    evidence = json.loads(out.strip().splitlines()[-1])
    assert evidence["header"] == 200 and evidence["query"] == 200, evidence
    assert "text/event-stream" in evidence["headerType"] and "text/event-stream" in evidence["queryType"]
    assert evidence["subjectless"] == 401, "a token with no subject owns no records"


def test_the_stream_is_not_compressed_or_buffered(project):
    """A gzipped or proxy-buffered SSE response arrives in one lump at close,
    which looks live in the dashboard and is not."""
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '60'; process.env.SSE_POLL_MS = '20';
const res = makeRes();
await route.handlers[route.handlers.length - 1](makeReq({ token: 'good' }), res, (e) => { throw e; });
console.log(JSON.stringify(res.headers));
""", {"records": []})
    headers = json.loads(out.strip().splitlines()[-1])
    assert "no-transform" in headers["cache-control"], headers
    assert headers["x-accel-buffering"] == "no", headers


# --------------------------------------------------------------------------
# 3. the actual claim: a row written after connect is pushed to the client
# --------------------------------------------------------------------------

def test_a_row_written_after_connect_arrives_without_a_refresh(project):
    stamp = "2026-10-27T10:00:05.000Z"
    out = _run_stream_probe(
        project,
        """
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '400'; process.env.SSE_POLL_MS = '30';
const res = makeRes();
await collect(route, makeReq({ token: 'good' }), res, 200);
console.log(JSON.stringify({ frames: res.frames, ended: res.writableEnded }));
""",
        {"records": [{"rowId": "rec-1", "at": stamp}]},
        env={"TZ": "UTC"},
    )
    evidence = json.loads(out.strip().splitlines()[-1])
    text = "".join(evidence["frames"])
    assert "event: record:changed" in text, text
    assert '"rec-1"' in text, "the pushed frame must name the row that changed"
    assert "id:" in text, "a frame without an id cannot be resumed after a reconnect"
    assert "retry:" in text, "the client must be told how fast to reconnect"


def test_the_contact_feed_pushes_a_signal_and_no_personal_data(project):
    """The inquiry feed proves the form works in real time, but an authenticated
    owner of records must not be handed another visitor's name, email or message."""
    stamp = "2026-10-27T10:00:06.000Z"
    out = _run_stream_probe(
        project,
        """
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '400'; process.env.SSE_POLL_MS = '30';
const res = makeRes();
await collect(route, makeReq({ token: 'good' }), res, 200);
console.log(JSON.stringify(res.frames));
""",
        {"contact": [{"rowId": "inq-9", "at": stamp,
                      "name": "Someone Else", "email": "other@corp.test", "message": "secret quote"}]},
        env={"TZ": "UTC"},
    )
    frames = json.loads(out.strip().splitlines()[-1])
    text = "".join(frames)
    assert "event: contact:created" in text, text
    assert "other@corp.test" not in text and "secret quote" not in text, \
        "the feed leaked the submitter's details"


def test_records_are_read_only_for_the_authenticated_user(project):
    """Tenant scope belongs in the statement. A feed that selects every row and
    filters in JavaScript would have already leaked before the first frame."""
    out = _run_stream_probe(project, """
const { sequelize } = require('./models');
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '300'; process.env.SSE_POLL_MS = '25';
const res = makeRes();
await collect(route, makeReq({ token: 'good' }), res, 120);
const calls = (sequelize.__calls || []).filter((c) => c.sql.includes('records'));
console.log(JSON.stringify(calls.map((c) => ({ sql: c.sql, bind: c.bind }))));
""", {"records": []})
    calls = json.loads(out.strip().splitlines()[-1])
    assert calls, "the feed never queried the records table"
    sql = calls[0]["sql"]
    assert "userId" in sql and "$1" in sql, sql
    assert "user-1" not in sql, "the user id was interpolated into the SQL text"
    assert any("user-1" in json.dumps(c["bind"]) for c in calls), \
        f"the tenant id never reached the bind parameters: {calls}"


# --------------------------------------------------------------------------
# 4. reconnects, resource limits and failure honesty
# --------------------------------------------------------------------------

def test_a_reconnect_resumes_from_the_last_event_id(project):
    cursor = "2026-10-27T09:30:00.000Z"
    out = _run_stream_probe(project, """
const { sequelize } = require('./models');
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '300'; process.env.SSE_POLL_MS = '25';
const res = makeRes();
await collect(route, makeReq({ token: 'good',
  headers: { 'last-event-id': process.env.PROBE_CURSOR } }), res, 120);
const calls = (sequelize.__calls || []).filter((c) => c.sql.includes('records'));
console.log(JSON.stringify(calls.map((c) => c.bind)));
""", {"records": []}, env={"PROBE_CURSOR": cursor, "TZ": "UTC"})
    binds = json.loads(out.strip().splitlines()[-1])
    assert binds, "no query was issued"
    resumed = [b for b in binds if any(str(v).startswith("2026-10-27T09:30") for v in b)]
    assert resumed, f"a reconnect must resume at Last-Event-ID, not at now: {binds}"


def test_a_fresh_visitor_never_receives_the_whole_history(project):
    out = _run_stream_probe(project, """
const { sequelize } = require('./models');
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '300'; process.env.SSE_POLL_MS = '25';
const res = makeRes();
await collect(route, makeReq({ token: 'good' }), res, 120);
const calls = (sequelize.__calls || []).filter((c) => c.sql.includes('records'));
console.log(JSON.stringify(calls.map((c) => c.bind)));
""", {"records": []})
    binds = json.loads(out.strip().splitlines()[-1])
    assert binds
    assert not any(str(v).startswith("1970") for b in binds for v in b), \
        "the cursor was left at the epoch — a new client would be replayed the tenant's history"


def test_the_stream_ends_itself_before_the_platform_timeout(project):
    """Vercel kills a function at maxDuration mid-stream. Closing cleanly a few
    seconds earlier makes the client reconnect instead of seeing a broken pipe."""
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '120'; process.env.SSE_POLL_MS = '25';
const res = makeRes();
await collect(route, makeReq({ token: 'good' }), res, 400);
console.log(JSON.stringify({ ended: res.writableEnded }));
""", {"records": []})
    assert json.loads(out.strip().splitlines()[-1])["ended"] is True


def test_a_disconnected_client_does_not_leak_a_timer(project):
    out = _run_stream_probe(project, """
const timers = [];
const realInterval = global.setInterval, realClear = global.clearInterval;
global.setInterval = (fn, ms) => { const t = realInterval(fn, ms); timers.push({ t, ms, open: true }); return t; };
global.clearInterval = (t) => { const found = timers.find((x) => x.t === t); if (found) found.open = false; return realClear(t); };
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '3000'; process.env.SSE_POLL_MS = '25';
const res = makeRes();
const req = makeReq({ token: 'good' });
await route.handlers[route.handlers.length - 1](req, res, (e) => { throw e; });
await new Promise((r) => setTimeout(r, 80));
req.emit('close');
await new Promise((r) => setTimeout(r, 40));
global.setInterval = realInterval; global.clearInterval = realClear;
console.log(JSON.stringify({ open: timers.filter((x) => x.open).length, made: timers.length }));
""", {"records": []})
    evidence = json.loads(out.strip().splitlines()[-1])
    assert evidence["made"] > 0, evidence
    assert evidence["open"] == 0, f"a closed connection kept {evidence['open']} timer(s) running"


def test_a_dead_database_is_announced_not_silenced(project):
    """If the feed cannot read, the client must be told so it can fall back to
    polling. A stream that goes quiet looks like an idle dashboard."""
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
process.env.SSE_MAX_MS = '2000'; process.env.SSE_POLL_MS = '20';
const res = makeRes();
await collect(route, makeReq({ token: 'good' }), res, 500);
console.log(JSON.stringify({ text: res.text(), ended: res.writableEnded }));
""", {"records": []}, fail=True)
    evidence = json.loads(out.strip().splitlines()[-1])
    assert "event: feed-error" in evidence["text"], evidence
    assert evidence["ended"] is True, "the stream must close so the client can switch to polling"


def test_too_many_streams_on_one_process_is_refused_not_queued(project):
    out = _run_stream_probe(project, """
const { route } = eventsRoute();
process.env.SSE_MAX_CLIENTS = '2'; process.env.SSE_MAX_MS = '5000'; process.env.SSE_POLL_MS = '50';
const handler = route.handlers[route.handlers.length - 1];
const held = [];
for (let i = 0; i < 3; i += 1) { const res = makeRes(); held.push(res); await handler(makeReq({ token: 'good' }), res, (e) => { throw e; }); }
console.log(JSON.stringify(held.map((r) => r.statusCode)));
""", {"records": []})
    codes = json.loads(out.strip().splitlines()[-1])
    assert codes[:2] == [200, 200] and codes[2] == 503, codes


# --------------------------------------------------------------------------
# 5. Redis is an accelerator, never a dependency
# --------------------------------------------------------------------------

def test_a_write_publishes_a_change_signal(project):
    out = _run_stream_probe(project, """
const published = [];
const bus = require('./services/changeBus.js');
const off = bus.subscribe((table) => published.push(table));
bus.notify('records');
off();
bus.notify('records');
console.log(JSON.stringify(published));
""", {"records": []})
    assert json.loads(out.strip().splitlines()[-1]) == ["records"], "the write must wake every open stream"


def test_the_generated_write_paths_notify_the_bus(project):
    """A dashboard that only learns about its own writes once per second is fine;
    a dashboard that never learns is the bug these routes keep regressing into."""
    apply_production_spec(str(project), brand="RealtimeApp")
    records = (project / "backend" / "routes" / "records.routes.js").read_text(encoding="utf-8")
    assert "notify('records')" in records or 'notify("records")' in records, records[:400]
    assert records.count("notify") >= 3, "create, update and delete must all announce themselves"


def test_redis_is_optional_and_never_breaks_a_write(project):
    """REDIS_URL set but the optional package missing is a normal deployment
    state. The write path must succeed anyway."""
    out = _run_stream_probe(project, """
process.env.REDIS_URL = 'redis://127.0.0.1:1/0';
delete require.cache[require.resolve('./services/changeBus.js')];
const bus = require('./services/changeBus.js');
const seen = [];
const off = bus.subscribe((table) => seen.push(table));
bus.notify('records');
off();
console.log(JSON.stringify({ seen, survived: true }));
""", {"records": []}, env={"REDIS_URL": "redis://127.0.0.1:1/0"})
    assert json.loads(out.strip().splitlines()[-1]) == {"seen": ["records"], "survived": True}


def test_redis_fan_out_crosses_instances_when_it_is_installed(project):
    redis_dir = project / "backend" / "node_modules" / "redis"
    redis_dir.mkdir(parents=True)
    (redis_dir / "package.json").write_text(json.dumps({"name": "redis", "main": "index.js"}),
                                            encoding="utf-8")
    (redis_dir / "index.js").write_text(_REDIS_STUB, encoding="utf-8")
    out = _run_stream_probe(project, """
const express = require('express');
process.env.REDIS_URL = 'redis://127.0.0.1:6379/0';
const bus = require('./services/changeBus.js');
const redis = require('redis');
const got = [];
bus.subscribe((table) => got.push(table));
bus.notify('records');
console.log(JSON.stringify({ got, published: redis.clients.map((c) => c.published).flat() }));
""", {"records": []}, env={"REDIS_URL": "redis://127.0.0.1:6379/0"})
    evidence = json.loads(out.strip().splitlines()[-1])
    assert evidence["got"] == ["records"], evidence
    assert ["lumicore:changes", "records"] in [list(p) for p in evidence["published"]], \
        f"notify() did not publish to Redis: {evidence}"
