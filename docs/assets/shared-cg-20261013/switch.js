/* Saved-result selection only. No fetching, recomputation, or invented OD/time combinations. */
(function(){
'use strict';
const data=window.MCL_CG_CATALOG;if(!data)return;
const memories=new Map();
let alignmentFrame;
function alignComparison(){
 cancelAnimationFrame(alignmentFrame);alignmentFrame=requestAnimationFrame(()=>{
  for(const grid of document.querySelectorAll('[data-cg-compare="reference-three"]')){
   const columns=[...grid.children];
   const groups=['.av-city-title','.cg-controls','.cg-body>.atlas-method-heading','.cg-body>.atlas-method-instance','.cg-body>.atlas-method-summary'].map(s=>columns.map(c=>c.querySelector(s)));
   for(let i=0;i<3;i++)groups.push(columns.map(c=>c.querySelectorAll('.cg-body>.cg-gallery>.atlas-card')[i]));
   for(const group of groups)for(const el of group)if(el)el.style.minHeight='';
   if(columns.length===3&&getComputedStyle(grid).gridTemplateColumns.split(' ').length===3){
    for(const group of groups){const height=Math.max(...group.map(el=>el?.getBoundingClientRect().height||0));for(const el of group)if(el)el.style.minHeight=Math.ceil(height)+'px';}
   }
  }
 });
}
const odKey=c=>c.OD+'|'+c.scale;
function option(s,value,label){const o=document.createElement('option');o.value=value;o.textContent=label;s.appendChild(o);}
function timeLabel(c){const dt=c.dt_seconds;const time=dt==null?c.horizon_steps+' native steps':dt+' s · '+c.horizon_steps.toLocaleString('en-US')+' steps ('+(dt*c.horizon_steps/60).toLocaleString('en-US',{maximumFractionDigits:3})+' min)';return time+' · '+(c.events===c.OD?'pulse':'1 h release')+' · '+(c.reference?(c.reference_label||'764e086 reference'):c.case_id);}
function desired(city){
 const u=new URL(location.href),cases=data.cases.filter(c=>c.city===city);let id=u.searchParams.get('cg-case');
 if(!id&&city==='sioux-falls'&&u.searchParams.has('sioux-od'))id=u.searchParams.get('sioux-od')==='250'?'sioux_250_original':'sioux_200_original';
 const hash=decodeURIComponent(u.hash.slice(1));const original=cases.find(c=>c.reference&&c.reference_anchors.includes(hash));
 const c=original||cases.find(c=>c.case_id===id)||cases.find(c=>c.case_id===memories.get(city)?.case)||cases.find(c=>c.case_id===data.defaults[city]);
 const eid=c.case_id===id?u.searchParams.get('cg-evidence'):memories.get(city)?.evidence;
 return {c,e:c.evidence.find(e=>e.evidence_id===eid)||c.evidence.find(e=>e.evidence_id===c.default_evidence)};
}
function render(root,c,e){
 const os=root.querySelector('[data-cg-od]'),cs=root.querySelector('[data-cg-case]'),es=root.querySelector('[data-cg-evidence]'),ls=root.querySelector('[data-cg-layout]');const cases=data.cases.filter(x=>x.city===c.city);
 os.replaceChildren();const groups=new Set();for(const x of cases){const key=odKey(x);if(!groups.has(key)){option(os,key,x.OD.toLocaleString('en-US')+' ODs · vehicle demand ×'+x.scale);groups.add(key);}}os.value=odKey(c);os.disabled=groups.size===1;
 cs.replaceChildren();for(const x of cases.filter(x=>odKey(x)===odKey(c)))option(cs,x.case_id,timeLabel(x));cs.value=c.case_id;
 es.replaceChildren();for(const x of c.evidence)option(es,x.evidence_id,x.label);es.value=e.evidence_id;
 const layout=ls?new URL(location.href).searchParams.get('cg-layout')||'five':'five';if(ls){const unavailable=c.city==='sioux-falls'&&!c.sioux_reference;ls.querySelector('option[value="original"]').disabled=unavailable;ls.value=layout==='original'&&!unavailable?'original':'five';}
 const key=(root.dataset.cgVolume==='true'?'volume':'home')+'_'+(c.selected_three?'selected':ls&&ls.value==='original'?'original':'five')+'_html';root.querySelector('.cg-body').innerHTML=e[key];
 if(root.dataset.cgCompact==='true')for(const item of root.querySelectorAll('.cg-body [id]'))item.removeAttribute('id');
 if(typeof scheduleReadingCardAlignment==='function')scheduleReadingCardAlignment();
 alignComparison();
}
function init(root){
 if(root.dataset.cgReady)return;root.dataset.cgReady='true';const city=root.dataset.cgCity;
 const os=root.querySelector('[data-cg-od]'),cs=root.querySelector('[data-cg-case]'),es=root.querySelector('[data-cg-evidence]'),ls=root.querySelector('[data-cg-layout]');
 function choose(kind){
  const cases=data.cases.filter(c=>c.city===city);const c=kind==='od'?cases.find(c=>odKey(c)===os.value):cases.find(c=>c.case_id===cs.value);const e=(kind==='evidence'||kind==='layout'?c.evidence.find(e=>e.evidence_id===es.value):null)||c.evidence.find(e=>e.evidence_id===c.default_evidence);
  memories.set(city,{case:c.case_id,evidence:e.evidence_id});const u=new URL(location.href);u.searchParams.set('cg-case',c.case_id);u.searchParams.set('cg-evidence',e.evidence_id);if(ls)u.searchParams.set('cg-layout',ls.value);if(city==='sioux-falls')u.searchParams.set('sioux-od',c.OD===250?'250':'200');
  if(root.dataset.cgCompact!=='true')u.hash='shared-cg-'+city;if(u.href!==location.href)history.pushState({},'',u);
  for(const item of document.querySelectorAll('.cg-component[data-cg-city="'+city+'"]'))render(item,c,e);
 }
 os.addEventListener('change',()=>choose('od'));cs.addEventListener('change',()=>choose('case'));es.addEventListener('change',()=>choose('evidence'));if(ls)ls.addEventListener('change',()=>choose('layout'));
 root.addEventListener('toggle',alignComparison,true);
 const x=desired(city);render(root,x.c,x.e);
}
function mount(parent,city,volume=false,compact=false){
 const root=document.createElement('section');root.className='cg-component';root.dataset.cgCity=city;root.dataset.cgVolume=String(volume);root.dataset.cgCompact=String(compact);
 root.innerHTML='<div class="cg-controls"><label>OD scope / demand factor<select data-cg-od></select></label><label>Time model / experiment<select data-cg-case></select></label><label>Result version<select data-cg-evidence></select></label></div><div class="cg-body"></div>';
 for(const sel of root.querySelectorAll('select'))sel.setAttribute('aria-label',data.cities[city]+' '+sel.parentElement.firstChild.textContent);parent.appendChild(root);init(root);return root;
}
function restore(){for(const root of document.querySelectorAll('.cg-component')){if(!root.dataset.cgReady)init(root);else{const x=desired(root.dataset.cgCity);render(root,x.c,x.e);}}}
function reveal(){const el=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(el&&el.closest('.cg-component')){for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;el.scrollIntoView({block:'start'});}}
window.MCLSharedCG={mount};restore();reveal();window.addEventListener('popstate',()=>{memories.clear();restore();reveal();});window.addEventListener('hashchange',()=>{restore();reveal();});
window.addEventListener('resize',alignComparison);
})();
