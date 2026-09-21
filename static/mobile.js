window.programLinks = p => {
 const links=[];
 if(p.id==='food') links.push(['https://finder.nyc.gov/foodhelp/','Find food by ZIP code']);
 if(['snap','cash','one-shot','fair-fares'].includes(p.id)) links.push(['https://a069-access.nyc.gov/accesshra/','Apply / manage through ACCESS HRA'],['https://apps.apple.com/us/app/nyc-access-hra/id1185595325','ACCESS HRA · App Store'],['https://play.google.com/store/apps/details?id=gov.nyc.hra.SelfService','ACCESS HRA · Google Play']);
 if(p.id==='fair-fares') links.push(['/static/documents/FF-14-E.pdf','Fair Fares suggested documents (PDF)']);
 return links.length?'<div class="resource-links">'+links.map(([url,label])=>`<a href="${url}" target="_blank" rel="noopener noreferrer">${label} ↗</a>`).join('')+(p.id==='fair-fares'?'<p>Checklist dated February 10, 2025. Your application tells you which documents, if any, to submit.</p>':'')+(['snap','cash','one-shot','fair-fares'].includes(p.id)?'<p>Use the website to apply; the mobile app helps upload documents and manage your case.</p>':'')+'</div>':'';
};
// Convert only standalone 311 text; never rewrite user inputs or existing links.
function link311(root){
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const nodes=[];
 while(walker.nextNode()){const n=walker.currentNode;if(/\b311\b/.test(n.textContent)&&!n.parentElement.closest('a,textarea,input,script,style,code,pre'))nodes.push(n);}
 for(const n of nodes){const f=document.createDocumentFragment();n.textContent.split(/(\b311\b)/).forEach(part=>{if(part==='311'){const a=document.createElement('a');a.href='tel:311';a.textContent='311';a.setAttribute('aria-label','Call 311');f.append(a);}else f.append(document.createTextNode(part));});n.replaceWith(f);}
}
const observer=new MutationObserver(()=>{observer.disconnect();link311(document.body);observe();});
function observe(){observer.observe(document.body,{childList:true,subtree:true,characterData:true});}
link311(document.body);observe();
let installPrompt;
window.addEventListener('beforeinstallprompt',event=>{event.preventDefault();installPrompt=event;document.querySelector('#install-app').hidden=false;});
document.querySelector('#install-app').addEventListener('click',async()=>{if(installPrompt){await installPrompt.prompt();installPrompt=null;document.querySelector('#install-app').hidden=true;}});
