import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as server_mod
from database.accounts_store import AccountStore
from database.pipeline_store import PipelineStore


@pytest.fixture
def tenant_client(tmp_path, monkeypatch):
    accounts = AccountStore(path=str(tmp_path / 'accounts.db'))
    owner = accounts.create_user('owner@example.com')
    other = accounts.create_user('other@example.com')
    pipeline = PipelineStore(db_path=str(tmp_path / 'pipeline.db'))
    pipeline.create_run('owned-run', status='done', prompt='private prompt', owner_id=owner['id'])

    monkeypatch.setattr(server_mod, '_accounts', accounts)
    monkeypatch.setattr(server_mod, '_pipeline_store', pipeline)
    monkeypatch.setattr(server_mod, '_AGENT_API_KEY', '')
    monkeypatch.setattr(server_mod, '_runs', {})
    yield TestClient(server_mod.app), owner['api_key'], other['api_key'], owner['id']
    pipeline.close()
    accounts.close()


def test_persisted_run_owner_can_only_be_seen_by_same_api_key(tenant_client):
    client, owner_key, other_key, _ = tenant_client

    own = client.get('/api/runs/owned-run', headers={'X-API-KEY': owner_key})
    foreign = client.get('/api/runs/owned-run', headers={'X-API-KEY': other_key})
    own_list = client.get('/api/runs', headers={'X-API-KEY': owner_key})
    other_list = client.get('/api/runs', headers={'X-API-KEY': other_key})

    assert own.status_code == 200
    assert foreign.status_code == 404
    assert own_list.status_code == 200
    assert [run['run_id'] for run in own_list.json()['runs']] == ['owned-run']
    assert other_list.json()['runs'] == []


def test_foreign_in_memory_run_cannot_be_cancelled(tenant_client, monkeypatch):
    client, _, other_key, owner_id = tenant_client
    server_mod._runs['memory-run'] = {
        'status': 'running', 'owner_id': owner_id, 'events': [], 'result': {},
        'cancel_requested': False,
    }
    monkeypatch.setattr(server_mod, '_request_cancel', lambda run_id: pytest.fail('must not cancel'))

    response = client.post('/api/cancel/memory-run', headers={'X-API-KEY': other_key})

    assert response.status_code == 404
