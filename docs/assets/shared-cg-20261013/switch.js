/* Local, synchronous evidence switch. No requests or stale asynchronous results. */
(function(){
'use strict';
const data=window.MCL_CG_CATALOG;if(!data)return;
const memories=new Map();
function desired(city){
 const url=new URL(location.href),cases=data.cases.filter(c=>c.city===city);
 let id=url.searchParams.get('cg-case');
 if(!id&&city==='sioux-falls')id=url.searchParams.get('sioux-od')==='250'?'sioux_250_H':'sioux_200_H';
 let c=cases.find(c=>c.case_id===id)||cases.find(c=>c.case_id===memories.get(city)?.case)||cases.find(c=>c.case_id===data.defaults[city]);
 const evidenceID=c.case_id===url.searchParams.get('cg-case')?url.searchParams.get('cg-evidence'):memories.get(city)?.evidence;
 let e=c.evidence.find(e=>e.evidence_id===evidenceID)||c.evidence.find(e=>e.evidence_id===c.default_evidence);
 return {c,e};
}
function option(select,id,label){const o=document.createElement('option');o.value=id;o.textContent=label;select.appendChild(o);}
function render(root,c,e){
 const cs=root.querySelector('[data-cg-case]'),es=root.querySelector('[data-cg-evidence]');cs.value=c.case_id;
 es.replaceChildren();for(const x of c.evidence)option(es,x.evidence_id,x.label);es.value=e.evidence_id;
 root.querySelector('.cg-body').innerHTML=root.dataset.cgVolume==='true'?e.volume_html:e.home_html;
 if(root.dataset.cgCompact==='true'){
  // Only this CG branch expands; upstream compact stage cards remain unchanged.
  for(const card of root.querySelectorAll('.cg-figure'))card.removeAttribute('id');
 }
 if(typeof scheduleReadingCardAlignment==='function')scheduleReadingCardAlignment();
}
function init(root){
 if(root.dataset.cgReady)return;root.dataset.cgReady='true';const city=root.dataset.cgCity;
 const cs=root.querySelector('[data-cg-case]'),es=root.querySelector('[data-cg-evidence]');
 cs.replaceChildren();for(const c of data.cases.filter(c=>c.city===city))option(cs,c.case_id,c.case_id+' · '+c.OD.toLocaleString('en-US')+' OD · ×'+c.scale);
 const choose=(isCase)=>{
  const c=data.cases.find(c=>c.case_id===cs.value);const e=(!isCase&&c.evidence.find(e=>e.evidence_id===es.value))||c.evidence.find(e=>e.evidence_id===c.default_evidence);
  memories.set(city,{case:c.case_id,evidence:e.evidence_id});
  const u=new URL(location.href);u.searchParams.set('cg-case',c.case_id);u.searchParams.set('cg-evidence',e.evidence_id);
  if(city==='sioux-falls')u.searchParams.set('sioux-od',c.case_id.includes('250')?'250':'200');
  if(root.dataset.cgCompact!=='true')u.hash='shared-cg-'+city;
  if(u.href!==location.href)history.pushState({cgCase:c.case_id,cgEvidence:e.evidence_id},'',u);
  for(const item of document.querySelectorAll('.cg-component[data-cg-city="'+city+'"]'))render(item,c,e);
 };
 cs.addEventListener('change',()=>choose(true));es.addEventListener('change',()=>choose(false));
 const x=desired(city);render(root,x.c,x.e);
}
function mount(parent,city,volume=false,compact=false){
 const root=document.createElement('section');root.className='cg-component';root.dataset.cgCity=city;root.dataset.cgVolume=String(volume);root.dataset.cgCompact=String(compact);
 root.innerHTML='<h4>Shared column generation</h4><div class="cg-controls"><label>CG instance <select data-cg-case></select></label><label>Evidence version <select data-cg-evidence></select></label></div><div class="cg-body"></div>';
 root.querySelector('[data-cg-case]').setAttribute('aria-label',data.cities[city]+' CG instance');root.querySelector('[data-cg-evidence]').setAttribute('aria-label',data.cities[city]+' CG evidence version');parent.appendChild(root);init(root);return root;
}
function restore(){for(const root of document.querySelectorAll('.cg-component')){if(!root.dataset.cgReady)init(root);else{const x=desired(root.dataset.cgCity);render(root,x.c,x.e);}}}
window.MCLSharedCG={mount};restore();
window.addEventListener('popstate',()=>{memories.clear();restore();});
window.addEventListener('hashchange',()=>{restore();const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(target&&target.closest('.cg-component'))target.scrollIntoView({block:'start'});});
})();
