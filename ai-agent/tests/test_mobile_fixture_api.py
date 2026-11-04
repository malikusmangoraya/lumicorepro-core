import http.client
import json
import sys
import uuid
from pathlib import Path

import pytest

AGENT_ROOT = Path(__file__).resolve().parent.parent
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.mobile_fixture_api import start_fixture_api


def _request(base_url, method, path, *, token='', payload=None):
    from urllib.parse import urlsplit

    url = urlsplit(base_url)
    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=5)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = json.dumps(payload) if payload is not None else None
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    data = response.read()
    result = json.loads(data) if data else {}
    connection.close()
    return response.status, response.getheader('Content-Type'), result


def test_fixture_api_registers_and_authenticates_users_and_records():
    server, base_url = start_fixture_api(port=0)
    try:
        email = f'{uuid.uuid4().hex}@example.test'
        status, _, registered = _request(
            base_url, 'POST', '/api/v1/auth/register',
            payload={'email': email, 'password': 'fixture-only-password'},
        )
        assert status == 201
        token = registered['data']['token']

        status, _, unauthorized = _request(base_url, 'GET', '/api/v1/records')
        assert status == 401
        assert unauthorized['success'] is False

        record_id = str(uuid.uuid4())
        status, _, created = _request(
            base_url, 'POST', '/api/v1/records', token=token,
            payload={'id': record_id, 'title': 'Offline record'},
        )
        assert status == 201
        assert created['data']['id'] == record_id

        status, _, records = _request(base_url, 'GET', '/api/v1/records', token=token)
        assert status == 200
        assert [record['id'] for record in records['data']] == [record_id]
    finally:
        server.shutdown()
        server.server_close()


def test_fixture_api_is_idempotent_and_user_scoped():
    server, base_url = start_fixture_api(port=0)
    try:
        emails = [f'{uuid.uuid4().hex}@example.test' for _ in range(2)]
        tokens = []
        for email in emails:
            status, _, result = _request(
                base_url, 'POST', '/api/v1/auth/register',
                payload={'email': email, 'password': 'fixture-only-password'},
            )
            assert status == 201
            tokens.append(result['data']['token'])

        record_id = str(uuid.uuid4())
        payload = {'id': record_id, 'title': 'Queued once'}
        first = _request(
            base_url, 'POST', '/api/v1/records', token=tokens[0], payload=payload
        )
        retry = _request(
            base_url, 'POST', '/api/v1/records', token=tokens[0], payload=payload
        )
        assert first[0] == 201
        assert retry[0] == 200
        assert retry[2]['data']['id'] == record_id

        status, _, other_user = _request(
            base_url, 'GET', '/api/v1/records', token=tokens[1]
        )
        assert status == 200
        assert other_user['data'] == []
    finally:
        server.shutdown()
        server.server_close()


def test_fixture_api_login_and_record_detail_update_delete():
    server, base_url = start_fixture_api(port=0)
    try:
        email = f'{uuid.uuid4().hex}@example.test'
        password = 'fixture-only-password'
        status, _, _ = _request(
            base_url, 'POST', '/api/v1/auth/register',
            payload={'email': email, 'password': password},
        )
        assert status == 201

        status, _, logged_in = _request(
            base_url, 'POST', '/api/v1/auth/login',
            payload={'email': email, 'password': password},
        )
        assert status == 200
        token = logged_in['data']['token']

        status, _, created = _request(
            base_url, 'POST', '/api/v1/records', token=token,
            payload={'title': 'First title', 'description': 'First description'},
        )
        assert status == 201
        record_id = created['data']['id']

        status, _, detail = _request(
            base_url, 'GET', f'/api/v1/records/{record_id}', token=token
        )
        assert status == 200
        assert detail['data']['title'] == 'First title'

        status, _, updated = _request(
            base_url, 'PUT', f'/api/v1/records/{record_id}', token=token,
            payload={'title': 'Updated title'},
        )
        assert status == 200
        assert updated['data']['title'] == 'Updated title'
        assert updated['data']['description'] == 'First description'

        status, _, deleted = _request(
            base_url, 'DELETE', f'/api/v1/records/{record_id}', token=token
        )
        assert status == 200
        assert deleted['data']['id'] == record_id

        status, _, missing = _request(
            base_url, 'GET', f'/api/v1/records/{record_id}', token=token
        )
        assert status == 404
        assert missing['success'] is False
    finally:
        server.shutdown()
        server.server_close()


def test_fixture_api_emits_sse_ready_frame():
    server, base_url = start_fixture_api(port=0)
    try:
        from urllib.parse import urlsplit

        url = urlsplit(base_url)
        connection = http.client.HTTPConnection(url.hostname, url.port, timeout=5)
        connection.request('GET', '/api/v1/events')
        response = connection.getresponse()
        first_frame = response.readline() + response.readline() + response.readline()
        assert response.status == 200
        assert response.getheader('Content-Type').startswith('text/event-stream')
        assert b'event: ready' in first_frame
        connection.close()
    finally:
        server.shutdown()
        server.server_close()


def test_fixture_api_health_uses_ephemeral_loopback_origin():
    server, base_url = start_fixture_api(port=0)
    try:
        assert base_url.startswith('http://127.0.0.1:')
        status, content_type, health = _request(
            base_url, 'GET', '/api/v1/health'
        )
        assert status == 200
        assert content_type.startswith('application/json')
        assert health['data'] == {'status': 'ok', 'fixture': True}
    finally:
        server.shutdown()
        server.server_close()
