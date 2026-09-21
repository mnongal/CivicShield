let currentPlan=null;
const $ = (s) => document.querySelector(s);
const labels = {preliminary_match:'Initial checks match', resource:'Resource to explore', needs_review:'Needs agency review', criteria_not_met:'A check did not match', not_requested:'Other support', out_of_scope:'Outside MVP coverage'};
const escapeHTML = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const e = escapeHTML;
const sample = {borough:'Brooklyn', household_size:1, age:28, monthly_income:0, annual_income:18000, needs:['food','housing','cash','work','transport'], housing_risk:true, job_loss:true, worked_in_ny:true, able_and_seeking_work:true};
async function api(path, data) {
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(path, {signal:controller.signal, ...(data ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)} : {})});
    if (!res.ok) { const body = await res.json().catch(() => ({})); throw new Error(res.status === 422 ? 'Please check your answers. ' + (body.detail || []).map(x => `${x.loc?.slice(1).join('.')}: ${x.msg}`).join('; ') : 'We could not complete this request. Please try again.'); }
    return await res.json();
  } catch (err) { if(err.name === 'AbortError') throw new Error('The request timed out. Please try again.'); throw err; }
  finally { clearTimeout(timeout); }
}
function source(p) { return `<div class="source"><a href="${e(p.source_url)}" target="_blank" rel="noopener noreferrer">Official program guide ↗</a><span>Reviewed ${e(p.verified_at)}</span><span>Source updated ${e(p.last_updated || 'not stated')}</span></div>`; }
function card(p, library=false) {
  return `<article class="result-card"><div class="result-top"><div><div class="category">${e(p.category)}</div><h3>${e(p.name)}</h3></div>${library ? '' : `<span class="badge ${e(p.status)}">${e(labels[p.status])}</span>`}</div><p>${e(p.summary)}</p>${library ? '' : `<p>${e(p.explanation)}</p>${p.missing.length ? `<p><strong>Still needed:</strong> ${p.missing.map(x => e(x.replaceAll('_',' '))).join(', ')}</p>` : ''}`}<div class="next-step"><strong>NEXT STEP</strong>${e(p.next_step || p.details.action)}</div><details><summary>What to prepare & what we checked</summary><p>${e(p.details.limitations)}</p>${p.details.documents.length ? `<ul>${p.details.documents.map(x=>`<li>${e(x)}</li>`).join('')}</ul><p>Suggested preparation only; check the official document list.</p>` : '<p>No document checklist is provided here. Ask the location about its process.</p>'}${library?'':`<p>Rule version: ${e(p.rule_version)} · ${e(p.explanation_mode)}</p>`}</details>${window.programLinks(p)}${source(p)}${!library?`<label>My progress<select data-progress="${e(p.id)}"><option>To do</option><option>In progress</option><option>Waiting for agency</option><option>Done</option></select></label><label>My notes<textarea data-note="${e(p.id)}" rows="2" maxlength="1000"></textarea></label>`:''}</article>`;
}
document.querySelectorAll('.tab[data-panel]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.tab[data-panel]').forEach(b => {b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button));});
  document.querySelectorAll('.panel').forEach(p => p.hidden=p.id!==button.dataset.panel);
  if(button.dataset.panel==='library') loadLibrary();
}));
async function loadLibrary() {
  $('#library-cards').textContent='Loading official program information…';
  try { $('#library-cards').innerHTML=(await api('/api/programs')).map(p=>card(p,true)).join(''); }
  catch(err) {$('#library-cards').textContent=err.message;}
}
$('#demo').addEventListener('click',()=>{
  const f=$('#intake'); for(const [key,value] of Object.entries(sample)){if(key==='needs'){f.querySelectorAll('[name=needs]').forEach(x=>x.checked=value.includes(x.value));}else{f.elements[key].value=String(value);}}
  $('#form-error').textContent=''; $('#demo').textContent='Demo loaded ✓'; $('#print').hidden=true;
  $('#results-title').textContent='Demo ready — find your next steps.';
  $('#results').textContent='The form now contains a fictional Brooklyn household. Select Find my next steps to create its plan.';
});
$('#intake').addEventListener('submit',async event=>{
  event.preventDefault(); const f=event.target; const fd=new FormData(f); const needs=fd.getAll('needs');
  $('#form-error').textContent=''; if(!needs.length){$('#form-error').textContent='Choose at least one area of support.';return;}
  const payload={borough:fd.get('borough'),needs};
  ['age','household_size','monthly_income','annual_income'].forEach(k=>payload[k]=fd.get(k)===''?null:Number(fd.get(k)));
  ['housing_risk','job_loss','worked_in_ny','able_and_seeking_work'].forEach(k=>payload[k]=fd.get(k)===''?null:fd.get(k)==='true');
  invalidatePlan(); const button=f.querySelector('[type=submit]'); button.disabled=true; button.textContent='Checking programs…'; $('#print').hidden=true;
  $('#results-title').textContent='Reviewing your answers…'; $('#results').textContent='Checking the curated program rules…';
  try {
    const data=await api('/api/screen',payload); currentPlan={...data,profile:payload,progress:{},notes:{}}; $('#plan-tools').hidden=false;
    const relevant=data.results.filter(p=>!['not_requested','out_of_scope'].includes(p.status));
    $('#results-title').textContent=relevant.length?`${relevant.length} programs to consider.`:'This MVP covers NYC residents.';
    $('#results').innerHTML=`${data.urgent?`<div class="alert">${e(data.urgent)}</div>`:''}<p class="muted">${e(data.notice)}</p>`+(relevant.length?relevant.map(p=>card(p)).join(''):'<div class="empty"><h3>Your location is outside this MVP.</h3><p>This does not mean you are ineligible. Check your local agencies or the NY State program guidance in the library.</p></div>');
    const others=data.results.filter(p=>p.status==='not_requested');
    if(others.length) $('#results').innerHTML+=`<details><summary>Other programs (${others.length})</summary>${others.map(p=>card(p)).join('')}</details>`;
    $('#print').hidden=!relevant.length;
  } catch(err){$('#form-error').textContent=err.message;$('#results-title').textContent='We could not create your plan.';$('#results').textContent='Your answers are still in the form. Please try again.';}
  finally {button.disabled=false;button.innerHTML='Find my next steps <span>→</span>';}
});
$('#intake').addEventListener('input',()=>{if(!$('#print').hidden){$('#results-title').textContent='Answers changed — update your plan.';$('#print').hidden=true;}});
$('#print').addEventListener('click',()=>window.print());
$('#results').addEventListener('input',event=>{if(!currentPlan)return;const el=event.target;if(el.dataset.progress)currentPlan.progress[el.dataset.progress]=el.value;if(el.dataset.note)currentPlan.notes[el.dataset.note]=el.value;});
function invalidatePlan(){currentPlan=null;$('#plan-tools').hidden=true;}
$('#intake').addEventListener('input',invalidatePlan);$('#demo').addEventListener('click',invalidatePlan);
$('#download-plan').addEventListener('click',()=>{
 if(!currentPlan)return;
 const content=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>CivicShield plan</title><style>body{font:16px system-ui;max-width:800px;margin:30px auto;padding:20px}article{border-bottom:1px solid #ccc;padding:20px 0}a{display:inline-block;margin:8px}p{white-space:pre-wrap}</style><h1>Your CivicShield plan</h1><p>Created ${e(currentPlan.generated_on)} · ${e(currentPlan.notice)}</p><h2>Your answers</h2><ul>${Object.entries(currentPlan.profile).map(([k,v])=>`<li>${e(k.replaceAll('_',' '))}: ${e(v===null?'Unknown':v)}</li>`).join('')}</ul>${currentPlan.urgent?`<p>${e(currentPlan.urgent)}</p>`:''}${currentPlan.results.filter(p=>p.status!=='not_requested').map(p=>`<article><h2>${e(p.name)}</h2><p>${e(labels[p.status])}: ${e(p.explanation)}</p><p>${e(p.next_step)}</p><ul>${p.details.documents.map(d=>`<li>${e(d)}</li>`).join('')}</ul><p>${e(p.details.limitations)}</p>${source(p)}${window.programLinks(p)}<p>Progress: ${e(currentPlan.progress[p.id]||'To do')}</p><p>Notes: ${e(currentPlan.notes[p.id]||'')}</p></article>`).join('')}<p>Call reminder: ${e($('#call-date').value)} at 8 a.m. New York time. Save the separate calendar file to receive an alert.</p></html>`;
 const blob=new Blob([content.replaceAll('href="/static/','href="'+location.origin+'/static/')],{type:'text/html'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='civicshield-plan.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
if(location.hash==='#reminders')document.querySelector('[data-panel="reminders"]').click();
