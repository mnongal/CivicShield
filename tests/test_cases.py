import json
from app.database import ROOT

def test_plan_requires_confirmation_and_recomputes_rules(client):
    profile=json.loads((ROOT/'data/demo-profile.json').read_text())
    body={'objective':'Find support','profile':profile,'confirmed':False}
    assert client.post('/api/cases/plan',json=body).status_code==422
    result=client.post('/api/cases/plan',json=body|{'confirmed':True}).json()
    assert len(result['results'])==7
    assert result['tasks']
    assert all(t['status']=='todo' for t in result['tasks'])
    assert result['outcome']=='in_progress'
    assert 'user-reported' in result['notice']


def test_interview_removed(client):
    assert client.get('/api/agent/config').status_code == 404
    assert client.post('/api/agent/turn', json={}).status_code == 404
    page = client.get('/guide')
    assert 'chat-form' not in page.text
    assert 'Local AI setup' not in page.text
    assert "script-src 'self'" in page.headers['content-security-policy']
