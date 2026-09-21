"""User-confirmed case plans, generated solely from deterministic rules."""
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from .database import get_programs
from .explanations import explain
from .rules import evaluate
from .schemas import Situation
router = APIRouter(prefix='/api/cases', tags=['Case plans'])
class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class PlanRequest(StrictModel):
    profile: Situation
    objective: str = Field(min_length=1, max_length=500)
    confirmed: Literal[True]


@router.post('/plan')
def plan(body: PlanRequest):
    results = [explain(p, evaluate(body.profile, p)) for p in get_programs()]
    active = [r for r in results if r['status'] in ('resource','preliminary_match','needs_review')]
    tasks = []
    for result in active:
        pid = result['id']
        titles = [result['next_step'], 'Prepare the documents listed in the official guide.',
                  'Contact the program or submit your application through the official channel.',
                  'Record the agency response and any requested follow-up.']
        if result['status'] == 'resource':
            titles = [result['next_step'], 'Contact the location and record whether you received the help you needed.']
        for index, title in enumerate(titles):
            tasks.append({'id': f'{pid}-{index}', 'program_id': pid, 'program_name': result['name'],
                          'title': title, 'source_url': result['source_url'], 'status': 'todo', 'note': '',
                          'documents': result['details']['documents'] if index == 1 else []})
    return {'version': 1, 'objective': body.objective, 'profile': body.profile.model_dump(mode='json'),
            'results': results, 'tasks': tasks, 'outcome': 'in_progress',
            'notice': 'Progress is user-reported. No applications have been submitted or agency decisions verified by this app.'}
