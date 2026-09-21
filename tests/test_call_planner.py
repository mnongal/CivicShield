from datetime import date

import pytest
from fastapi import HTTPException

from app.call_planner import Reminder, make_calendar, next_weekday, fold, escape_ics


def reminder(**changes):
    return Reminder(**({'contact_id':'unemployment','call_date':'2026-09-21','hours_checked':True}|changes))


def test_calendar_opening_and_alarm():
    result=make_calendar(reminder(),today=date(2026,9,19))
    assert 'DTSTART;TZID=America/New_York:20260921T080000' in result
    assert 'TRIGGER:-PT0M' in result
    assert 'LOCATION:+18882098124' in result
    assert 'CLASS:PRIVATE' in result
    assert 'BEGIN:VTIMEZONE' in result
    assert result.endswith('END:VCALENDAR\r\n')


def test_calendar_handles_dst_change_with_timezone_observances():
    result=make_calendar(reminder(call_date='2026-11-02'),today=date(2026,9,19))
    assert '20261102T080000' in result
    assert 'TZOFFSETTO:-0500' in result and 'TZOFFSETTO:-0400' in result
    assert 'BYMONTH=11;BYDAY=1SU' in result


@pytest.mark.parametrize('day',['2026-09-19','2026-09-20','2026-09-18','2026-12-21'])
def test_reject_past_weekend_or_distant_date(day):
    with pytest.raises(HTTPException):
        make_calendar(reminder(call_date=day),today=date(2026,9,19))


def test_stale_contact_blocks_calendar():
    with pytest.raises(HTTPException) as exc:
        make_calendar(reminder(call_date='2027-01-04'),today=date(2027,1,1))
    assert exc.value.status_code==409


def test_contact_and_calendar_api(client):
    data=client.get('/api/calls/contacts').json()
    assert len(data['contacts'])==2
    response=client.post('/api/calls/reminder',json={'contact_id':'hra','call_date':data['suggested_date'],'hours_checked':True,'minutes_before':10})
    assert response.status_code==200
    assert response.headers['content-type'].startswith('text/calendar')
    assert 'TRIGGER:-PT10M' in response.text
    assert 'LOCATION:+17185571399' in response.text


@pytest.mark.parametrize('changes',[{'hours_checked':False},{'contact_id':'unknown'},{'minutes_before':12},{'secret_pin':'1234'}])
def test_no_unreviewed_hours_or_sensitive_payload(client,changes):
    body={'contact_id':'unemployment','call_date':'2026-09-21','hours_checked':True}|changes
    assert client.post('/api/calls/reminder',json=body).status_code==422


def test_utf8_calendar_line_folding():
    folded=fold('DESCRIPTION:'+'é'*100)
    assert all(len(line.encode())<=75 for line in folded.split('\r\n'))
    assert folded.replace('\r\n ','')=='DESCRIPTION:'+'é'*100
    assert escape_ics('a,b;c\nd')=='a\\,b\\;c\\nd'


def test_next_weekday_skips_weekend():
    assert next_weekday(date(2026,9,18))==date(2026,9,21)
