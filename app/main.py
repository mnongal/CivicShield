from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .database import ROOT, get_programs, initialize, public_program
from .explanations import explain
from .rules import RULE_VERSION, evaluate
from .schemas import Situation
from .intake_ai import router as intake_ai_router
from .hosting import allowed_hosts
from .cases import router as case_router
from .call_planner import router as call_router
from starlette.middleware.trustedhost import TrustedHostMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    yield


app = FastAPI(title='CivicShield', version='0.1.0', lifespan=lifespan,
              description='NYC preliminary assistance screening. Official agencies decide eligibility.')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts())
app.include_router(case_router)
app.include_router(call_router)
app.include_router(intake_ai_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Avoid echoing sensitive notice text or financial inputs in validation errors.
    return JSONResponse(status_code=422, content={'detail': [
        {'loc': list(e['loc']), 'msg': e['msg'], 'type': e['type']} for e in exc.errors()]})


@app.middleware('http')
async def headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    if request.url.path in ('/', '/guide'):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response


@app.get('/api/health')
def health():
    return {'status': 'ok', 'program_count': len(get_programs()), 'rule_version': RULE_VERSION}


@app.get('/api/programs')
def programs():
    return [public_program(p) for p in get_programs()]


@app.post('/api/screen')
def screen(situation: Situation):
    results = [explain(p, evaluate(situation, p)) for p in get_programs()]
    order = {'resource': 0, 'preliminary_match': 1, 'needs_review': 2, 'criteria_not_met': 3, 'not_requested': 4, 'out_of_scope': 5}
    results.sort(key=lambda r: (order[r['status']], r['name']))
    return {'results': results, 'generated_on': date.today(), 'rule_version': RULE_VERSION,
            'notice': 'Preliminary guidance only. Program agencies determine eligibility. Your intake is not stored.',
            'urgent': 'If you may lose your housing, contact 311 and ask about Homebase. Follow any court or agency deadlines.' if situation.housing_risk and situation.borough != 'Outside NYC' else None}


@app.get('/')
def index():
    return FileResponse(ROOT / 'static/index.html')


app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.get('/guide')
def guide():
    return RedirectResponse('/#reminders', status_code=307)


