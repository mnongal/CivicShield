from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .database import Program
from .schemas import Situation

RULE_VERSION = 'nyc-2026-09-18.v1'


@dataclass(frozen=True)
class Decision:
    """A frozen dataclass holds a decision that the explanation layer cannot edit."""

    status: str
    reasons: tuple[str, ...]
    missing: tuple[str, ...] = ()


def evaluate(s: Situation, p: Program, today: date | None = None) -> Decision:
    """Pure, deterministic screening. Never return an official eligibility award."""
    today = today or date.today()
    if s.borough == 'Outside NYC':
        return Decision('out_of_scope', ('This MVP screens NYC residents only. This is not a denial of assistance.',))
    relevant = p.category in s.needs or (p.id == 'one-shot' and 'cash' in s.needs)
    if not relevant:
        return Decision('not_requested', ('This program is outside your selected needs. You can still read its official guide.',))
    if (today - p.verified_at).days > 90 or today < p.verified_at:
        return Decision('needs_review', ('The source review is outside its 90-day freshness window. Check the official page before screening.',))
    if p.id == 'fair-fares':
        missing = tuple(k for k in ('age', 'annual_income') if getattr(s, k) is None)
        if missing:
            return Decision('needs_review', ('Age and annual household income are needed for the published checks.',), missing)
        limit = Decimal(p.details['annual_limit_one_person']) + Decimal(p.details['annual_limit_additional_person']) * (s.household_size - 1)
        reasons = (f'The cited annual income limit for a household of {s.household_size} is ${limit:,.0f}.',)
        if not p.details['min_age'] <= s.age <= p.details['max_age']:
            return Decision('criteria_not_met', reasons + ('The published age range is 18–64; your age falls outside it.',))
        if s.annual_income > limit:
            return Decision('criteria_not_met', reasons + ('Your annual household income exceeds that published limit.',))
        return Decision('preliminary_match', reasons + ('You meet the NYC residence, age and income checks implemented here. Agency review is still required.',))
    if p.id == 'food':
        return Decision('resource', ('You requested food support. A local pantry or community kitchen may help.',))
    if p.id == 'homebase':
        if s.housing_risk is None:
            return Decision('needs_review', ('Homebase focuses on people at risk of entering shelter.',), ('housing_risk',))
        if not s.housing_risk:
            return Decision('criteria_not_met', ('You did not report a risk of losing housing. Homebase may still help identify other resources.',))
        return Decision('preliminary_match', ('You live in NYC and reported housing risk. Contact Homebase for a full assessment.',))
    if p.id == 'unemployment':
        fields = ('job_loss', 'worked_in_ny', 'able_and_seeking_work')
        missing = tuple(k for k in fields if getattr(s, k) is None)
        if missing or not all(getattr(s, k) for k in fields):
            return Decision('needs_review', ('Job separation, NY work history and availability for work require clarification; DOL can assess exceptions and interstate claims.',), missing)
        return Decision('preliminary_match', ('Your answers match initial job-loss and work-availability indicators. DOL must review wages and separation details.',))
    return Decision('needs_review', ('Your selected needs make this program worth reviewing. The agency must evaluate the financial and household rules.',))
