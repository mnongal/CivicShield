"""User-initiated calls and portable calendar reminders; no dialer or background job."""
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix='/api/calls', tags=['Call preparation'])
CONTACTS = [
    {'id': 'unemployment', 'name': 'NY Unemployment Telephone Claims Center',
     'phone': '+18882098124', 'display_phone': '(888) 209-8124',
     'hours': 'Monday–Friday, 8 a.m.–5 p.m. New York time',
     'source_url': 'https://dol.ny.gov/unemployment-insurance-contact',
     'verified_at': '2026-09-19',
     'purpose': 'Unemployment claim questions. This line does not resolve NY.gov account login issues.',
     'prepare': ['Keep employment dates and wage records nearby.', 'Have the notice or application you want to discuss available.', 'Keep your PIN private; do not put it in this app or your calendar.'],
     'questions': ['What is the current status of my application?', 'Is any information or documentation missing?', 'What should I do next, and by what date?', 'How can I follow up if I do not receive a response?'],
     'alternative': 'DOL also lists secure messaging through your NY.gov account on its official contact page.'},
    {'id': 'hra', 'name': 'NYC HRA Infoline', 'phone': '+17185571399',
     'display_phone': '(718) 557-1399', 'hours': 'Monday–Friday, 8 a.m.–5 p.m. New York time',
     'source_url': 'https://access.nyc.gov/programs/one-shot-deal/',
     'verified_at': '2026-09-19', 'purpose': 'HRA assistance questions, including emergency assistance guidance.',
     'prepare': ['Have the relevant notice and your questions nearby.', 'Prepare income, rent and household documents relevant to your request.', 'Keep private identifiers out of reminder titles and notes.'],
     'questions': ['Which application or office should I use for my situation?', 'Which documents do I need to provide?', 'Is an interview needed, and how do I arrange it?', 'What is the next step and how can I follow up?'],
     'alternative': 'The official guide also links to ACCESS HRA and in-person Benefits Access Centers.'},
]


def next_weekday(today: date) -> date:
    candidate = today + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


@router.get('/contacts')
def contacts():
    today = datetime.now(timezone.utc).date()
    return {'contacts': CONTACTS, 'suggested_date': next_weekday(today),
            'min_date': today + timedelta(days=1), 'max_date': today + timedelta(days=60),
            'timezone': 'America/New_York', 'call_time': '08:00',
            'notice': 'Hours can change on holidays or special closures. Verify the official page before calling. Calendar reminders do not guarantee a connection.'}


class Reminder(BaseModel):
    model_config = ConfigDict(extra='forbid')
    contact_id: Literal['unemployment', 'hra']
    call_date: date
    minutes_before: Literal[0, 5, 10, 15] = 0
    hours_checked: Literal[True]


def escape_ics(value: str) -> str:
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line: str) -> str:
    """RFC 5545 folds long UTF-8 content lines at 75 octets, not 75 characters."""
    lines, current = [], ''
    for character in line:
        if len((current + character).encode('utf-8')) > 75:
            lines.append(current)
            current = ' '
        current += character
    return '\r\n'.join(lines + [current])


def make_calendar(body: Reminder, today: date | None = None) -> str:
    today = today or datetime.now(timezone.utc).date()
    if not today < body.call_date <= today + timedelta(days=60):
        raise HTTPException(422, 'Choose a date from tomorrow through the next 60 days.')
    if body.call_date.weekday() >= 5:
        raise HTTPException(422, 'The published hours are Monday through Friday. Choose a weekday.')
    contact = next(c for c in CONTACTS if c['id'] == body.contact_id)
    if (today - date.fromisoformat(contact['verified_at'])).days > 90:
        raise HTTPException(409, 'Contact information needs a fresh source review before reminders can be created.')
    day = body.call_date.strftime('%Y%m%d')
    description = f"Call {contact['display_phone']} yourself. Check the official page for closures.\n{contact['source_url']}\nHave your documents and questions ready. Do not include private identifiers in calendar notes."
    # Include timezone observances so calendars can resolve Eastern time without
    # relying on the importing device's local timezone. Current US DST rules.
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//CivicShield//Call reminders//EN',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'BEGIN:VTIMEZONE', 'TZID:America/New_York',
             'BEGIN:DAYLIGHT', 'DTSTART:20070311T020000', 'TZOFFSETFROM:-0500', 'TZOFFSETTO:-0400',
             'TZNAME:EDT', 'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU', 'END:DAYLIGHT',
             'BEGIN:STANDARD', 'DTSTART:20071104T020000', 'TZOFFSETFROM:-0400', 'TZOFFSETTO:-0500',
             'TZNAME:EST', 'RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU', 'END:STANDARD', 'END:VTIMEZONE',
             'BEGIN:VEVENT', f'UID:{uuid4()}@civicshield.local',
             'DTSTAMP:' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
             f'DTSTART;TZID=America/New_York:{day}T080000',
             f'DTEND;TZID=America/New_York:{day}T081500',
             'SUMMARY:' + escape_ics('Call ' + contact['name']),
             'DESCRIPTION:' + escape_ics(description), 'LOCATION:' + contact['phone'],
             'URL:' + contact['source_url'], 'CLASS:PRIVATE', 'BEGIN:VALARM',
             f'TRIGGER:-PT{body.minutes_before}M', 'ACTION:DISPLAY',
             'DESCRIPTION:Prepare for your agency call', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR']
    return '\r\n'.join(fold(line) for line in lines) + '\r\n'


@router.post('/reminder')
def reminder(body: Reminder):
    return Response(make_calendar(body), media_type='text/calendar',
                    headers={'Content-Disposition': 'attachment; filename="civicshield-call.ics"'})
