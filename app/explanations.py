"""Retrieval seam: only curated program records become explanation context.

No external model is called in v1. A later LLM can paraphrase this context in a
separate display field; it must never create or replace a Decision.
"""
from dataclasses import asdict

from .database import Program, public_program
from .rules import Decision, RULE_VERSION


def retrieve_context(program: Program) -> dict:
    return {'program_id': program.id, 'summary': program.summary,
            'source_url': program.source_url, 'verified_at': program.verified_at,
            'limitations': program.details['limitations']}


def explain(program: Program, decision: Decision) -> dict:
    context = retrieve_context(program)
    return {**public_program(program), **asdict(decision), 'rule_version': RULE_VERSION,
            'explanation': ' '.join(decision.reasons), 'context': context,
            'explanation_mode': 'source-grounded template',
            'next_step': program.details['action']}
