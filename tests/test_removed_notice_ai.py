def test_cloud_notice_feature_removed(client):
    assert client.get('/api/notices/ai/config').status_code == 404
    assert client.post('/api/notices/ai/explain', json={}).status_code == 404
    page = client.get('/').text
    assert 'notice-ai.js' not in page
    assert 'ai-explain' not in page
    assert client.post('/api/documents/explain', json={}).status_code == 404
    assert client.post('/api/documents/pdf', content=b'pdf').status_code == 404
    assert 'Understand a notice' not in page
