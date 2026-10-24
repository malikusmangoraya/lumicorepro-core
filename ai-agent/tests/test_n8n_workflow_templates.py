import json
from pathlib import Path


WORKFLOW_DIR = Path(__file__).resolve().parents[1] / 'integrations' / 'n8n'
WORKFLOW_PATH = WORKFLOW_DIR / 'generate-and-monitor.json'


def _workflow():
    return json.loads(WORKFLOW_PATH.read_text(encoding='utf-8'))


def test_template_is_valid_json_without_embedded_credentials():
    workflow = _workflow()

    assert workflow['name'] == 'LumicorePro Generate and Monitor'
    serialized = json.dumps(workflow)
    assert 'api_key' not in serialized.lower()
    assert 'secret' not in serialized.lower()
    assert 'Bearer ' not in serialized
    assert 'LUMICORE_API_BASE_URL' in serialized
    assert 'LumicorePro API Key' in serialized


def test_http_nodes_use_existing_routes_and_auth_placeholders():
    workflow = _workflow()
    http_nodes = [node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.httpRequest']
    urls = [node['parameters']['url'] for node in http_nodes]

    assert any('/api/generate' in url for url in urls)
    assert any('/api/runs/' in url for url in urls)
    assert all('LUMICORE_API_BASE_URL' in url for url in urls)
    assert all(node['credentials']['httpHeaderAuth']['name'] == 'LumicorePro API Key' for node in http_nodes)


def test_polling_is_bounded_and_handles_terminal_states():
    workflow = _workflow()
    code = '\n'.join(
        node['parameters'].get('jsCode', '')
        for node in workflow['nodes']
        if node['type'] == 'n8n-nodes-base.code'
    )

    assert 'MAX_POLL_ATTEMPTS' in code
    assert 'queued' in code and 'running' in code
    assert 'done' in code and 'error' in code and 'cancelled' in code
    assert 'missing_run_id' in code
    assert 'request_failed' in code
    assert 'poll_timeout' in code
    connections = workflow['connections']
    run_id_branch = connections['Run id present?']['main']
    assert run_id_branch[0][0]['node'] == 'Get run status'
    assert run_id_branch[1][0]['node'] == 'Build notification metadata'
    assert 'request_failed' in code
    assert all(node.get('onError') == 'continueRegularOutput' for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.httpRequest')


def test_connections_reference_existing_nodes_once():
    workflow = _workflow()
    node_names = {node['name'] for node in workflow['nodes']}

    for source, connection_groups in workflow['connections'].items():
        assert source in node_names
        for branch in connection_groups['main']:
            for connection in branch:
                assert connection['node'] in node_names


def test_notifications_exclude_prompt_and_generated_output_by_default():
    workflow = _workflow()
    notification_code = next(
        node['parameters']['jsCode']
        for node in workflow['nodes']
        if node['name'] == 'Build notification metadata'
    )

    assert 'run_id' in notification_code
    assert 'status' in notification_code
    assert 'prompt' not in notification_code
    assert 'result' not in notification_code
