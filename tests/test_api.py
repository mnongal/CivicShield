import json

import pytest
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.database import ROOT, Program, engine, initialize


def demo():
    return json.loads((ROOT / 'data/demo-profile.json').read_text())


def test_end_to_end(client):
    assert client.get('/api/health').json()['program_count'] == 7
    response = client.post('/api/screen', json=demo())
    assert response.status_code == 200
    body = response.json()
    assert len(body['results']) == 7
    assert body['urgent']
    for result in body['results']:
        assert result['source_url'].startswith('https://')
        assert result['verified_at'] == '2026-09-18'
        assert result['status'] not in ('eligible','approved')
        assert result['next_step']
    assert client.get('/').status_code == 200
    assert client.get('/static/app.js').status_code == 200
    assert client.get('/openapi.json').status_code == 200


@pytest.mark.parametrize('change', [{'household_size':0}, {'monthly_income':-1}, {'annual_income':'NaN'}, {'age':121}, {'borough':'NY'}, {'needs':[]}, {'needs':['invented']}, {'ssn':'private-test-value'}])
def test_bad_intake_rejected(client,change):
    response = client.post('/api/screen',json=demo() | change)
    assert response.status_code == 422
    assert 'private-test-value' not in response.text


def test_seed_idempotent_and_no_personal_data_tables(client):
    initialize()
    initialize()
    assert len(client.get('/api/programs').json()) == 7
    assert inspect(engine).get_table_names() == ['programs']


def test_postgres_schema_compiles():
    ddl=str(CreateTable(Program.__table__).compile(dialect=postgresql.dialect()))
    assert 'details JSON' in ddl
    assert 'verified_at DATE' in ddl


def test_privacy_and_csp_headers(client):
    response=client.get('/')
    assert response.headers['cache-control']=='no-store'
    assert "script-src 'self'" in response.headers['content-security-policy']
