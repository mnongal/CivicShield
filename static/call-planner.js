const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const callSelect = document.querySelector('#call-contact');
const callInfo = document.querySelector('#call-info');
let callContacts = [];
async function loadContacts(){
  try {
    const response=await fetch('/api/calls/contacts'); if(!response.ok)throw new Error();
    const data=await response.json();callContacts=data.contacts.filter(c=>c.id==='unemployment');
    callSelect.replaceChildren(...callContacts.map(c=>new Option(c.name,c.id)));
    const date=document.querySelector('#call-date');date.min=data.min_date;date.max=data.max_date;date.value=data.suggested_date;
    document.querySelector('#call-notice').textContent=data.notice;
    showContact();document.querySelector('#save-reminder').disabled=false;
  }catch{callInfo.textContent='Could not load contact information. Reload the page to retry.';}
}
function showContact(){
  const c=callContacts.find(x=>x.id===callSelect.value);if(!c)return;
  // Every URL and phone here comes from the server's reviewed catalog.
  callInfo.innerHTML=`<p>${esc(c.purpose)}</p><p><strong>${esc(c.hours)}</strong></p><a class="dial-link" href="tel:${esc(c.phone)}">Call ${esc(c.display_phone)} ↗</a><p><a href="${esc(c.source_url)}" target="_blank" rel="noopener noreferrer">Check official hours and closures ↗</a> · Reviewed ${esc(c.verified_at)}</p><h3>Before you call</h3><ul>${c.prepare.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Questions to ask</h3><ul>${c.questions.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p>${esc(c.alternative)}</p>`;
  document.querySelector('#hours-checked').checked=false;
  document.querySelector('#reminder-status').textContent='';
}
callSelect.addEventListener('change',showContact);
document.querySelector('#reminder-form').addEventListener('submit',async event=>{
  event.preventDefault();const status=document.querySelector('#reminder-status');const button=document.querySelector('#save-reminder');
  button.disabled=true;status.textContent='Creating your calendar file…';
  try{
    const response=await fetch('/api/calls/reminder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({contact_id:callSelect.value,call_date:document.querySelector('#call-date').value,minutes_before:Number(document.querySelector('#remind-before').value),hours_checked:document.querySelector('#hours-checked').checked})});
    if(!response.ok){const error=await response.json();throw new Error(typeof error.detail==='string'?error.detail:'Check the date and confirm you reviewed the hours.');}
    const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download='civicshield-call.ics';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    status.textContent='Calendar file downloaded. Open it and save the event in your calendar, then check that the alert is enabled. Downloading alone does not schedule a notification.';
  }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
});
loadContacts();

const issuePrompts={
  employment:['Which employer, work dates or earnings were reported?', 'Does the report match my records? What should I provide if it does not?', 'Does DOL need a response or documents by a particular date?'],
  social_security:['What exact payment or benefit does the notice refer to?', 'What information does DOL need to clarify this report?', 'How should I respond, and what supporting records should I provide?'],
  payment:['What is the status of the delayed or missing payment?', 'Is an unresolved issue or missing information holding it up?', 'What is my next step and how should I follow up?'],
  notice:['What does this notice ask me to do?', 'What is the response deadline and the accepted way to send documents?', 'How can I confirm DOL received my response?'],
  other:['What information do you need to understand my claim issue?', 'What should I do next?', 'Is there a deadline or reference number I should write down?']
};
function showIssue(){const list=issuePrompts[document.querySelector('#call-issue').value]||issuePrompts.other;document.querySelector('#issue-prep').innerHTML='<strong>QUESTIONS FOR THIS ISSUE</strong><ul>'+list.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul><p>Keep the original notice and relevant records nearby. These are preparation questions, not a conclusion about your benefits. Follow any stated deadline rather than waiting for a planned call.</p>';}
document.querySelector('#call-issue').addEventListener('change',showIssue);showIssue();
