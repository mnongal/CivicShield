import json
from unittest.mock import patch
import pytest
from app import intake_ai as ai

@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','test-key')
    ai._calls.clear()

def test_consent_and_token(client):
    with patch.object(ai,'extract') as mock:
        assert client.post('/api/intake-ai/suggest',json={'text':'I need groceries','consent':True}).status_code==403
        assert client.post('/api/intake-ai/suggest',json={'text':'I need groceries','consent':False},headers={'X-Civic-Token':ai.TOKEN}).status_code==400
        mock.assert_not_called()

def test_no_key_keeps_manual_form(client,monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY')
    assert not client.get('/api/intake-ai/config').json()['configured']
    assert 'id="intake"' in client.get('/').text

def test_suggestions_are_not_decisions(client):
    with patch.object(ai,'extract',return_value={'borough':'Queens','needs':['food','housing','work']}):
        response=client.post('/api/intake-ai/suggest',json={'text':'I live in Queens and need groceries.','consent':True},headers={'X-Civic-Token':ai.TOKEN})
    assert response.status_code==200
    assert set(response.json())=={'borough','needs'}

def test_invalid_model_answer_rejected():
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'borough':'Queens','needs':['food'],'eligible':True})}}]}).encode()
    with patch.object(ai,'urlopen',return_value=Response()):
        with pytest.raises(ValueError):ai.extract('I need groceries in Queens.')

def test_error_never_leaks_key(client):
    with patch.object(ai,'extract',side_effect=RuntimeError('test-key')):
        response=client.post('/api/intake-ai/suggest',json={'text':'I need groceries','consent':True},headers={'X-Civic-Token':ai.TOKEN})
    assert response.status_code==502
    assert 'test-key' not in response.text
