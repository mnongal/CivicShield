(()=>{
const get=s=>document.querySelector(s);let config=null,draft=null,revision=0;
const status=get('#suggest-status'),button=get('#suggest-answers');
fetch('/api/intake-ai/config').then(r=>{if(!r.ok)throw Error();return r.json();}).then(c=>{config=c;button.disabled=!c.configured;status.textContent=c.configured?'You can also skip AI and fill in the form below.':'AI is not configured. Fill in the form below.';}).catch(()=>status.textContent='AI unavailable. Fill in the form below.');
get('#situation-text').addEventListener('input',()=>{revision++;draft=null;get('#suggest-preview').hidden=true;get('#suggest-consent').checked=false;});
button.addEventListener('click',async()=>{
 const text=get('#situation-text').value.trim(),version=revision;
 if(text.length<10){status.textContent='Enter at least 10 characters describing your situation.';return;}
 if(!get('#suggest-consent').checked){status.textContent='Confirm sharing the description with Groq first.';return;}
 button.disabled=true;draft=null;get('#suggest-preview').hidden=true;status.textContent='Finding suggested answers…';const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
 try{const r=await fetch('/api/intake-ai/suggest',{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json','X-Civic-Token':config.token},body:JSON.stringify({text,consent:true})});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Please check your description.');
 if(version!==revision){status.textContent='Description changed. Select Suggest answers again.';return;}
 draft=d;get('#suggest-summary').textContent=`Borough: ${d.borough||'Unknown — choose it yourself'}. Support: ${d.needs.join(', ')||'Unknown — choose it yourself'}.`;
 get('#suggest-preview').hidden=false;status.textContent='Review the suggestions. Your form has not changed.';
 }catch(e){status.textContent=e.name==='AbortError'?'AI timed out. You can fill in the form yourself.':e.message;}finally{clearTimeout(timer);button.disabled=!config?.configured;}
});
get('#apply-suggestions').addEventListener('click',()=>{if(!draft)return;const f=get('#intake');f.elements.borough.value=draft.borough||'';f.querySelectorAll('[name=needs]').forEach(el=>el.checked=draft.needs.includes(el.value));f.dispatchEvent(new Event('input',{bubbles:true}));status.textContent='Suggestions applied. Review every answer, complete the remaining fields, then select Find my next steps.';get('#suggest-preview').hidden=true;draft=null;f.scrollIntoView({behavior:'smooth',block:'start'});});
})();
