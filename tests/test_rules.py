import json
from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from app.database import ROOT, Program
from app.explanations import explain
from app.rules import evaluate
from app.schemas import Situation

TODAY = date(2026, 9, 18)
SEEDS = json.loads((ROOT / 'data/programs.json').read_text())


def program(key):
    row = next(dict(row) for row in SEEDS if row['id'] == key)
    row['verified_at'] = date.fromisoformat(row['verified_at'])
    row['last_updated'] = date.fromisoformat(row['last_updated']) if row['last_updated'] else None
    return Program(**row)


def profile(**changes):
    return Situation(**({'borough': 'Brooklyn', 'household_size': 1, 'age': 28,
                         'annual_income': 18000, 'needs': ['transport']} | changes))


@pytest.mark.parametrize('income,status', [(23475, 'preliminary_match'), ('23475.01', 'criteria_not_met'), (None, 'needs_review'), (0, 'preliminary_match')])
def test_income_boundary(income, status):
    assert evaluate(profile(annual_income=income), program('fair-fares'), TODAY).status == status


@pytest.mark.parametrize('age,status', [(17,'criteria_not_met'), (18,'preliminary_match'), (64,'preliminary_match'), (65,'criteria_not_met'), (None,'needs_review')])
def test_age_boundary(age, status):
    assert evaluate(profile(age=age), program('fair-fares'), TODAY).status == status


def test_larger_household_threshold():
    assert evaluate(profile(household_size=9, annual_income=89475), program('fair-fares'), TODAY).status == 'preliminary_match'
    assert evaluate(profile(household_size=9, annual_income='89475.01'), program('fair-fares'), TODAY).status == 'criteria_not_met'


def test_monthly_income_is_not_silently_annualized():
    result = evaluate(profile(annual_income=None, monthly_income=0), program('fair-fares'), TODAY)
    assert result.status == 'needs_review'
    assert result.missing == ('annual_income',)


@pytest.mark.parametrize('days,status', [(90,'preliminary_match'), (91,'needs_review'), (-1,'needs_review')])
def test_freshness_gate(days, status):
    assert evaluate(profile(), program('fair-fares'), TODAY + timedelta(days=days)).status == status


@pytest.mark.parametrize('key', [row['id'] for row in SEEDS])
def test_outside_nyc_is_not_a_denial(key):
    assert evaluate(profile(borough='Outside NYC'), program(key), TODAY).status == 'out_of_scope'


@pytest.mark.parametrize('key', ['snap','cash','one-shot'])
def test_complex_programs_never_claim_eligibility(key):
    assert evaluate(profile(needs=['food','cash','housing'], monthly_income=0), program(key), TODAY).status == 'needs_review'


@pytest.mark.parametrize('risk,status', [(True,'preliminary_match'), (False,'criteria_not_met'), (None,'needs_review')])
def test_housing_unknown_is_not_false(risk,status):
    assert evaluate(profile(needs=['housing'], housing_risk=risk), program('homebase'), TODAY).status == status


def test_ui_exceptions_require_review():
    s = profile(needs=['work'], job_loss=True, worked_in_ny=True, able_and_seeking_work=True)
    assert evaluate(s, program('unemployment'), TODAY).status == 'preliminary_match'
    for field in ('job_loss','worked_in_ny','able_and_seeking_work'):
        assert evaluate(s.model_copy(update={field:False}), program('unemployment'), TODAY).status == 'needs_review'


def test_explanation_preserves_frozen_rule_decision():
    p = program('fair-fares')
    d = evaluate(profile(), p, TODAY)
    before = (d.status, d.reasons, d.missing)
    result = explain(p, d)
    assert (result['status'], result['reasons'], result['missing']) == before
    assert result['context']['source_url'] == p.source_url
    with pytest.raises(FrozenInstanceError):
        d.status = 'approved'


def test_unrequested_and_resource():
    assert evaluate(profile(), program('food'), TODAY).status == 'not_requested'
    assert evaluate(profile(needs=['food']), program('food'), TODAY).status == 'resource'
