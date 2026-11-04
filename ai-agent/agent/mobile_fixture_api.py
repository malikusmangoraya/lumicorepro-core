"""Loopback-only in-memory API fixtures for native app verification."""

import json
import re
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


_MAX_BODY_BYTES = 64 * 1024
_MAX_RECORDS = 100
_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')


class _FixtureServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler):
        super().__init__(address, handler)
        self.lock = threading.RLock()
        self.users = {}
        self.tokens = {}
        self.records = {}


class _FixtureHandler(BaseHTTPRequestHandler):
    server_version = 'LumicoreMobileFixture/1.0'
    sys_version = ''

    def log_message(self, _format, *args):
        return

    def _respond(self, status, payload=None, *, content_type='application/json; charset=utf-8'):
        body = b'' if payload is None else json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _error(self, status, message):
        self._respond(status, {'success': False, 'message': message, 'data': None})

    def _read_json(self):
        raw_length = self.headers.get('Content-Length', '0')
        try:
            length = int(raw_length)
        except ValueError:
            self._error(400, 'Invalid content length.')
            return None
        if length < 0 or length > _MAX_BODY_BYTES:
            self._error(413, 'Request body is too large.')
            return None
        try:
            payload = json.loads(self.rfile.read(length) or b'{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._error(400, 'Request body must be valid JSON.')
            return None
        if not isinstance(payload, dict):
            self._error(400, 'Request body must be a JSON object.')
            return None
        return payload

    def _user_id(self):
        authorization = self.headers.get('Authorization', '')
        scheme, _, token = authorization.partition(' ')
        if scheme.lower() != 'bearer' or not token:
            return None
        with self.server.lock:
            return self.server.tokens.get(token)

    def _record_path(self):
        path = urlsplit(self.path).path
        prefix = '/api/v1/records/'
        if path.startswith(prefix):
            record_id = path[len(prefix):]
            return record_id if record_id and '/' not in record_id else None
        return None

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/v1/health':
            return self._respond(200, {
                'success': True,
                'data': {'status': 'ok', 'fixture': True},
            })
        if path == '/api/v1/events':
            return self._write_sse_ready()

        user_id = self._user_id()
        if user_id is None:
            return self._error(401, 'Authentication required.')
        if path == '/api/v1/records':
            with self.server.lock:
                records = list(self.server.records.get(user_id, {}).values())
            return self._respond(200, {'success': True, 'data': records})
        record_id = self._record_path()
        if record_id:
            with self.server.lock:
                record = self.server.records.get(user_id, {}).get(record_id)
            if record is None:
                return self._error(404, 'Record not found.')
            return self._respond(200, {'success': True, 'data': record})
        return self._error(404, 'Route not found.')

    def _write_sse_ready(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(b'event: ready\ndata: {"ok":true}\n\n')
        self.wfile.flush()
        return True

    def do_POST(self):
        path = urlsplit(self.path).path
        if path in {'/api/v1/auth/register', '/api/v1/auth/login'}:
            payload = self._read_json()
            if payload is None:
                return
            email = payload.get('email')
            password = payload.get('password')
            if (
                not isinstance(email, str)
                or len(email) > 254
                or not _EMAIL_RE.fullmatch(email)
                or not isinstance(password, str)
                or len(password) < 8
                or len(password) > 256
            ):
                return self._error(422, 'A valid email and password are required.')
            email = email.lower()
            with self.server.lock:
                user = self.server.users.get(email)
                if path.endswith('/register'):
                    if user is not None:
                        return self._error(409, 'Account already exists.')
                    user = {
                        'id': str(uuid.uuid4()),
                        'email': email,
                        'name': str(payload.get('name') or '')[:120],
                        'password': password,
                    }
                    self.server.users[email] = user
                    status = 201
                else:
                    if user is None or not secrets.compare_digest(
                        user['password'], password
                    ):
                        return self._error(401, 'Email or password is incorrect.')
                    status = 200
                token = secrets.token_urlsafe(32)
                self.server.tokens[token] = user['id']
                public_user = {key: value for key, value in user.items() if key != 'password'}
            return self._respond(status, {
                'success': True,
                'data': {'token': token, 'user': public_user},
            })

        user_id = self._user_id()
        if user_id is None:
            return self._error(401, 'Authentication required.')
        if path != '/api/v1/records':
            return self._error(404, 'Route not found.')
        payload = self._read_json()
        if payload is None:
            return
        title = payload.get('title')
        description = payload.get('description', '')
        if (
            not isinstance(title, str)
            or not title.strip()
            or len(title) > 160
            or not isinstance(description, str)
            or len(description) > 5000
        ):
            return self._error(422, 'A valid record title is required.')
        requested_id = payload.get('id')
        if requested_id is None:
            record_id = str(uuid.uuid4())
        else:
            try:
                record_id = str(uuid.UUID(str(requested_id)))
            except (ValueError, AttributeError):
                return self._error(422, 'Record id must be a UUID.')
        with self.server.lock:
            owner_records = self.server.records.setdefault(user_id, {})
            existing = owner_records.get(record_id)
            if existing is not None:
                if existing['title'] != title.strip() or existing['description'] != description:
                    return self._error(409, 'Record id was already used with different content.')
                return self._respond(200, {'success': True, 'data': existing})
            if sum(len(records) for records in self.server.records.values()) >= _MAX_RECORDS:
                return self._error(429, 'Fixture record capacity reached.')
            record = {
                'id': record_id,
                'title': title.strip(),
                'description': description,
                'createdAt': '',
                'updatedAt': '',
            }
            owner_records[record_id] = record
        return self._respond(201, {'success': True, 'data': record})

    def do_PUT(self):
        user_id = self._user_id()
        if user_id is None:
            return self._error(401, 'Authentication required.')
        record_id = self._record_path()
        if not record_id:
            return self._error(404, 'Route not found.')
        payload = self._read_json()
        if payload is None:
            return
        title = payload.get('title')
        if title is not None and (
            not isinstance(title, str) or not title.strip() or len(title) > 160
        ):
            return self._error(422, 'A valid record title is required.')
        with self.server.lock:
            record = self.server.records.get(user_id, {}).get(record_id)
            if record is None:
                return self._error(404, 'Record not found.')
            if title is not None:
                record['title'] = title.strip()
            if 'description' in payload:
                description = payload['description']
                if not isinstance(description, str) or len(description) > 5000:
                    return self._error(422, 'Invalid record description.')
                record['description'] = description
            updated = dict(record)
        return self._respond(200, {'success': True, 'data': updated})

    def do_DELETE(self):
        user_id = self._user_id()
        if user_id is None:
            return self._error(401, 'Authentication required.')
        record_id = self._record_path()
        if not record_id:
            return self._error(404, 'Route not found.')
        with self.server.lock:
            owner_records = self.server.records.get(user_id, {})
            record = owner_records.pop(record_id, None)
        if record is None:
            return self._error(404, 'Record not found.')
        return self._respond(200, {'success': True, 'data': {'id': record_id}})


def start_fixture_api(port=0):
    """Run a bounded ephemeral API on loopback only; it never touches real data."""
    server = _FixtureServer(('127.0.0.1', int(port)), _FixtureHandler)
    thread = threading.Thread(
        target=server.serve_forever,
        name='lumicore-mobile-fixture-api',
        daemon=True,
    )
    thread.start()
    server.fixture_thread = thread
    base_url = f'http://127.0.0.1:{server.server_address[1]}'
    return server, base_url
