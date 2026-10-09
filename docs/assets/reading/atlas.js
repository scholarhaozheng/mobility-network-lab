document.documentElement.dataset.atlasView=["city","stage"].includes(new URL(location.href).searchParams.get("atlas-view"))?new URL(location.href).searchParams.get("atlas-view"):"full";
// Keep the existing city/stage grid; align each row's title, image top and caption start.
function alignReadingCardRows(){
 const galleries=[...document.querySelectorAll('.case-atlas .atlas-gallery')];
 const cards=galleries.flatMap(g=>[...g.querySelectorAll(':scope > .conservative-card')]);
 // Clear earlier measurements so rows can shrink after a resize or font change.
 for(const card of cards){card.style.removeProperty('--atlas-title-height');card.style.removeProperty('--atlas-image-height');}
 const changes=[];
 for(const gallery of galleries){
  const rows=[];
  for(const card of gallery.querySelectorAll(':scope > .conservative-card')){
   if(!card.getClientRects().length)continue;
   const title=card.querySelector(':scope > h5'),image=card.querySelector(':scope > .atlas-image');
   if(!title||!image)continue;
   const top=card.getBoundingClientRect().top;
   let row=rows.find(r=>Math.abs(r.top-top)<1);
   if(!row){row={top,cards:[],title:0,image:0};rows.push(row);}
   row.cards.push(card);
   row.title=Math.max(row.title,title.getBoundingClientRect().height);
   row.image=Math.max(row.image,image.getBoundingClientRect().height);
  }
  for(const row of rows)if(row.cards.length>1)changes.push(row);
 }
 for(const row of changes)for(const card of row.cards){
  card.style.setProperty('--atlas-title-height',row.title+'px');
  card.style.setProperty('--atlas-image-height',row.image+'px');
 }
 document.dispatchEvent(new Event('reading-card-rows-aligned'));
}
let readingAlignmentFrame=0;
function scheduleReadingCardAlignment(){
 if(readingAlignmentFrame)return;
 readingAlignmentFrame=requestAnimationFrame(()=>{readingAlignmentFrame=0;alignReadingCardRows();});
}
// Keep original page navigation after the initial layout settles.
let readingAnchorUserInterrupted=false;
function settleReadingAnchor(){if(document.documentElement.dataset.atlasView!=='full')return;if(readingAnchorUserInterrupted||!location.hash)return;let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}const target=document.getElementById(id);if(target)target.scrollIntoView({block:'start',behavior:'instant'});}
// Static figures declare dimensions; pixel loading does not change geometry.
// Measure rows on initial layout, fonts, widths and instance changes only.
window.addEventListener('resize',scheduleReadingCardAlignment,{passive:true});
window.addEventListener('load',()=>{alignReadingCardRows();settleReadingAnchor();});
if(document.fonts)document.fonts.ready.then(scheduleReadingCardAlignment);
if('ResizeObserver' in window){
 const widths=new WeakMap();
 const observer=new ResizeObserver(entries=>{
  let changed=false;
  for(const entry of entries){const width=entry.contentRect.width;if(widths.get(entry.target)!==width){widths.set(entry.target,width);changed=true;}}
  if(changed)scheduleReadingCardAlignment();
 });
 for(const gallery of document.querySelectorAll('.case-atlas .atlas-gallery'))observer.observe(gallery);
}
scheduleReadingCardAlignment();


// One instance choice controls all three finite-time method rows.
(function initSiouxInstanceSwitch(){
 const section=document.querySelector('[data-stage="sioux-falls-finite"]');
 if(!section)return;
 const tabs=[...section.querySelectorAll('[data-sioux-select]')];
 const panels=[...section.querySelectorAll('.sioux-instance-panel')];
 if(tabs.length!==2||panels.length!==2)return;
 function desiredScale(){
  let target=null;try{target=document.getElementById(decodeURIComponent(location.hash.slice(1)))}catch{}
  const targetScale=target?.closest('.sioux-instance-panel')?.dataset.siouxOd;
  return targetScale||(new URL(location.href).searchParams.get('sioux-od')==='250'?'250':'200');
 }
 function choose(od,writeHistory=false){
  od=od==='250'?'250':'200';
  for(const tab of tabs){const selected=tab.dataset.siouxSelect===od;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1;}
  for(const panel of panels)panel.hidden=panel.dataset.siouxOd!==od;
  section.dataset.selectedOd=od;
  section.querySelector('.sioux-instance-status').textContent='Showing '+od+' OD across CG, Lagrangian and ADMM';
  if(writeHistory){const url=new URL(location.href);url.searchParams.set('sioux-od',od);url.hash='sioux-falls-finite';if(url.href!==location.href)history.pushState({siouxOd:od},'',url);}
  scheduleReadingCardAlignment();
 }
 for(const tab of tabs){
  tab.addEventListener('click',()=>choose(tab.dataset.siouxSelect,true));
  tab.addEventListener('keydown',event=>{
   const i=tabs.indexOf(tab);let next;
   if(event.key==='ArrowRight')next=(i+1)%tabs.length;
   else if(event.key==='ArrowLeft')next=(i+tabs.length-1)%tabs.length;
   else if(event.key==='Home')next=0;
   else if(event.key==='End')next=tabs.length-1;
   else return;
   event.preventDefault();tabs[next].focus();choose(tabs[next].dataset.siouxSelect,true);
  });
 }
 document.addEventListener('click',event=>{
  if(event.button!==0||event.metaKey||event.ctrlKey||event.altKey||event.shiftKey)return;
  const link=event.target.closest('a[href^="#"]');if(!link)return;
  let target;try{target=document.getElementById(decodeURIComponent(link.hash.slice(1)))}catch{return;}
  const od=target?.closest('.sioux-instance-panel')?.dataset.siouxOd;if(od)choose(od);
 },true);
 window.addEventListener('popstate',()=>choose(desiredScale()));
 window.addEventListener('hashchange',()=>choose(desiredScale()));
 document.addEventListener('atlas-sioux-scale',event=>choose(event.detail.scale));
 choose(desiredScale());
})();

// Reading location, chapter progress, and the existing Section 04 city/stage navigation.
(function initReadingLocationBar(){
 const section=document.getElementById('04-explore-the-three-cases');
 const globalNav=document.querySelector('body > .nav');
 const page=document.querySelector('.mcl-page');
 const atlasElements=[...document.querySelectorAll('.case-atlas[data-city]')];
 if(!section||!globalNav||!page||!atlasElements.length)return;
 const chapters=[
  {id:'mobility-computation-lab',number:'00',name:'Introduction'},
  {id:'01-what-this-project-adds',number:'01',name:'Project contributions'},
  {id:'02-complete-project-structure',number:'02',name:'Project structure'},
  {id:'03-case-coverage-and-selected-evidence',number:'03',name:'Coverage & statistics'},
  {id:'04-explore-the-three-cases',number:'04',name:'Evidence atlas'},
  {id:'05-run-and-inspect',number:'05',name:'Run & inspect'},
  {id:'06-attribution-scope-and-further-reading',number:'06',name:'Sources & reading'}
 ].map(chapter=>({...chapter,element:document.getElementById(chapter.id)})).filter(chapter=>chapter.element);
 const cities=atlasElements.map(element=>({
  key:element.dataset.city,
  label:element.querySelector(':scope > h3')?.textContent.trim()||element.dataset.city,
  element,
  // Keep reading navigation attached to the actual city article, even if a legacy external anchor is misplaced.
  target:element.querySelector(':scope > h3')||element,
  stages:[...element.querySelectorAll(':scope > .atlas-stage[data-stage]')].map(stage=>({
   key:stage.dataset.stage,
   label:stage.querySelector(':scope > h4')?.textContent.trim()||stage.dataset.stage,
   element:stage,
   target:document.getElementById(stage.dataset.stage)||stage
  }))
 }));
 const bar=document.createElement('nav');bar.className='reading-location-bar';bar.hidden=false;
 bar.setAttribute('aria-label','Reading location and chapter navigation');
 const inner=document.createElement('div');inner.className='reading-location-inner';
 const breadcrumb=document.createElement('div');breadcrumb.className='reading-location-breadcrumb';breadcrumb.setAttribute('aria-label','Current location');
 const sectionLink=document.createElement('a');sectionLink.href='#'+section.id;sectionLink.textContent='04';
 const citySeparator=document.createElement('span');citySeparator.textContent='›';citySeparator.setAttribute('aria-hidden','true');
 const cityLink=document.createElement('a');cityLink.textContent='Overview';cityLink.href='#'+section.id;
 const stageSeparator=document.createElement('span');stageSeparator.textContent='›';stageSeparator.setAttribute('aria-hidden','true');
 const currentStage=document.createElement('span');currentStage.className='reading-location-current-stage';currentStage.setAttribute('aria-current','location');
 breadcrumb.append(sectionLink,citySeparator,cityLink,stageSeparator,currentStage);
 const controls=document.createElement('div');controls.className='reading-location-controls';controls.hidden=true;
 function selectControl(labelText){
  const label=document.createElement('label');const text=document.createElement('span');text.textContent=labelText;
  const select=document.createElement('select');select.className='reading-location-select';label.append(text,select);controls.append(label);return select;
 }
 const citySelect=selectControl('City');const stageSelect=selectControl('Stage');
 const cityPlaceholder=new Option('Choose city','');cityPlaceholder.disabled=true;citySelect.append(cityPlaceholder);
 for(const city of cities)citySelect.append(new Option(city.label,city.key));
 const detailsWrap=document.createElement('div');detailsWrap.className='reading-details-wrap';
 const detailsTrigger=document.createElement('button');detailsTrigger.type='button';detailsTrigger.className='reading-details-trigger';detailsTrigger.textContent='Reading details';
 detailsTrigger.setAttribute('aria-expanded','false');detailsTrigger.setAttribute('aria-controls','reading-details-panel');
 const detailsPanel=document.createElement('section');detailsPanel.id='reading-details-panel';detailsPanel.className='reading-details-panel';detailsPanel.hidden=true;
 detailsPanel.setAttribute('aria-labelledby','reading-details-heading');
 const detailsHeading=document.createElement('h2');detailsHeading.id='reading-details-heading';detailsHeading.className='reading-details-heading';
 const detailsProgress=document.createElement('div');detailsProgress.className='reading-details-progress';
 function progressItem(label,key){
  const item=document.createElement('div');item.className='reading-progress-item';
  const labelRow=document.createElement('div');labelRow.className='reading-progress-label';
  const text=document.createElement('span');text.textContent=label;const value=document.createElement('span');value.setAttribute('data-progress-'+key,'');value.textContent='0%';
  const track=document.createElement('div');track.className='reading-progress-track';track.setAttribute('role','progressbar');track.setAttribute('aria-label',label);track.setAttribute('aria-valuemin','0');track.setAttribute('aria-valuemax','100');
  const fill=document.createElement('span');fill.setAttribute('data-progress-'+key+'-fill','');track.append(fill);labelRow.append(text,value);item.append(labelRow,track);detailsProgress.append(item);
  return {value,track,fill};
 }
 const pageProgress=progressItem('Page position','page');const sectionProgress=progressItem('Within this section','section');
 const chapterList=document.createElement('ol');chapterList.className='reading-chapter-list';
 const chapterButtons=chapters.map(chapter=>{
  const item=document.createElement('li');const button=document.createElement('button');button.type='button';button.dataset.readingJump=chapter.id;
  const number=document.createElement('span');number.className='reading-chapter-number';number.textContent=chapter.number;
  const title=document.createElement('span');title.className='reading-chapter-title';title.textContent=chapter.name;
  button.append(number,title);item.append(button);chapterList.append(item);return button;
 });
 detailsPanel.append(detailsHeading,detailsProgress,chapterList);detailsWrap.append(detailsTrigger,detailsPanel);
 const progressLine=document.createElement('div');progressLine.className='reading-progress-line';progressLine.setAttribute('aria-hidden','true');
 const progressLineFill=document.createElement('span');progressLineFill.setAttribute('data-progress-line-fill','');progressLine.append(progressLineFill);
 inner.append(breadcrumb,controls,detailsWrap);bar.append(inner,progressLine);document.body.append(bar);
 document.documentElement.dataset.readingLocationReady='true';
 let selectedCity='',selectedStage='',frame=0,lastOffset='';
 let heldTarget=null,anchorFrame=0,currentChapter=chapters[0],chapterBarHeight=0,chapterAtlasBarHeight=0,chapterBarWidth=0;
 let detailsHovered=false,detailsPinned=false,detailsKeyboard=false,detailsDismissed=false,keyboardInput=false,closeTimer=0;
 function refreshDetails(){
  const open=!detailsDismissed&&(detailsHovered||detailsPinned||detailsKeyboard);
  if(detailsPanel.hidden===open)detailsPanel.hidden=!open;
  detailsTrigger.setAttribute('aria-expanded',String(open));bar.dataset.detailsOpen=String(open);
 }
 function closeDetails(restoreFocus=false){
  clearTimeout(closeTimer);detailsHovered=false;detailsPinned=false;detailsKeyboard=false;detailsDismissed=true;
  refreshDetails();if(restoreFocus)detailsTrigger.focus({preventScroll:true});
 }
 function enterDetails(){clearTimeout(closeTimer);detailsHovered=true;detailsDismissed=false;refreshDetails();}
 function leaveDetails(){clearTimeout(closeTimer);closeTimer=setTimeout(()=>{detailsHovered=false;refreshDetails();},150);}
 detailsWrap.addEventListener('pointerenter',event=>{if(event.pointerType!=='touch')enterDetails();});
 detailsWrap.addEventListener('pointerleave',event=>{if(event.pointerType!=='touch')leaveDetails();});
 controls.addEventListener('pointerdown',()=>closeDetails());
 detailsTrigger.addEventListener('click',()=>{clearTimeout(closeTimer);detailsPinned=!detailsPinned;detailsDismissed=!detailsPinned;detailsHovered=false;detailsKeyboard=false;refreshDetails();});
 detailsWrap.addEventListener('focusin',event=>{
  if(keyboardInput||event.target.matches(':focus-visible')){detailsKeyboard=true;detailsDismissed=false;refreshDetails();}
 });
 detailsWrap.addEventListener('focusout',event=>{
  if(event.relatedTarget instanceof Node&&detailsWrap.contains(event.relatedTarget))return;
  requestAnimationFrame(()=>{
   if(!detailsWrap.contains(document.activeElement)){detailsKeyboard=false;detailsPinned=false;refreshDetails();}
  });
 });
 detailsTrigger.addEventListener('keydown',event=>{
  if(event.key==='ArrowDown'){event.preventDefault();detailsKeyboard=true;detailsDismissed=false;refreshDetails();chapterButtons[0]?.focus({preventScroll:true});}
 });
 document.addEventListener('keydown',event=>{
  keyboardInput=true;
  if(event.key==='Escape'&&!detailsPanel.hidden){event.preventDefault();closeDetails(false);detailsTrigger.focus({preventScroll:true});detailsDismissed=true;detailsKeyboard=false;refreshDetails();}
 },true);
 document.addEventListener('pointerdown',event=>{
  keyboardInput=false;
  if(!detailsWrap.contains(event.target))closeDetails();
 },true);
 function applyOffset(target){
  const top=Math.max(0,globalNav.getBoundingClientRect().bottom);
  const topValue=top+'px';if(bar.style.top!==topValue)bar.style.top=topValue;
  const panelHeight=Math.max(160,innerHeight-bar.getBoundingClientRect().bottom-26)+'px';
  if(bar.style.getPropertyValue('--reading-panel-max-height')!==panelHeight)bar.style.setProperty('--reading-panel-max-height',panelHeight);
  const inAtlas=target?belongsToAtlas(target)&&target!==section:currentChapter?.number==='04';
  const toolbarHeight=inAtlas?(document.getElementById('atlas-view-controls')?.getBoundingClientRect().height||0):0;
  const offset=Math.ceil(top+bar.getBoundingClientRect().height+toolbarHeight+12)+'px';
  if(offset!==lastOffset){document.documentElement.style.setProperty('--reading-navigation-offset',offset);lastOffset=offset;}
  return top;
 }
 function setLocation(city,stage){
  const key=city?.key||'';
  if(key!==selectedCity||!stageSelect.options.length){
   stageSelect.replaceChildren(new Option(city?'City overview':'Choose a city',''));
   for(const item of city?.stages||[])stageSelect.append(new Option(item.label,item.key));
   stageSelect.disabled=!city;selectedCity=key;
  }
  selectedStage=stage?.key||'';citySelect.value=key;stageSelect.value=selectedStage;
  cityLink.textContent=city?.label||'Overview';cityLink.href='#'+(city?.target.id||section.id);
  cityLink.toggleAttribute('aria-current',!stage);if(!stage)cityLink.setAttribute('aria-current','location');
  stageSeparator.hidden=!stage;currentStage.hidden=!stage;currentStage.textContent=stage?.label||'';currentStage.title=stage?.label||'';
 }
 function genericLocation(chapter,view){
  cityLink.textContent=chapter.name;cityLink.href='#'+chapter.id;cityLink.setAttribute('aria-current','location');
  let detail='';
  if(chapter.number==='04'&&view!=='full'){
   const selectedControl=view==='city'
    ? document.querySelector('#atlas-compact-panel .av-city-picker button[aria-pressed="true"]')
    : document.querySelector('#atlas-compact-panel [data-av-control="stage"] option:checked');
   const selected=selectedControl?.textContent.trim();
   detail=(view==='city'?'By city':'By stage')+(selected?' · '+selected:'');
  }
  stageSeparator.hidden=!detail;currentStage.hidden=!detail;currentStage.textContent=detail;currentStage.title=detail;
 }
 function updateProgress(top){
  const clamp=value=>Math.min(100,Math.max(0,value));
  const pageRect=page.getBoundingClientRect();const readingTop=top+bar.getBoundingClientRect().height;
  const pageStart=Math.max(0,pageRect.top+scrollY-readingTop);
  const pageEnd=Math.max(pageStart+1,pageRect.bottom+scrollY-innerHeight);
  const total=clamp((scrollY-pageStart)/(pageEnd-pageStart)*100);
  const index=chapters.indexOf(currentChapter);
  const start=currentChapter.element.getBoundingClientRect().top+scrollY;
  const finish=chapters[index+1]?.element.getBoundingClientRect().top+scrollY||pageRect.bottom+scrollY;
  const within=clamp((scrollY+readingTop-start)/Math.max(1,finish-start)*100);
  for(const [progress,value] of [[pageProgress,total],[sectionProgress,within]]){
   const rounded=Math.round(value);if(progress.value.textContent!==rounded+'%')progress.value.textContent=rounded+'%';progress.fill.style.width=value+'%';if(progress.track.getAttribute('aria-valuenow')!==String(rounded))progress.track.setAttribute('aria-valuenow',String(rounded));
  }
  progressLineFill.style.width=total+'%';
 }
 function update(){
  frame=0;bar.hidden=false;
  const top=Math.max(0,globalNav.getBoundingClientRect().bottom);
  const view=document.documentElement.dataset.atlasView||'full';
  // Measure both layouts so chapter thresholds do not depend on the visible controls.
  const barWidth=bar.getBoundingClientRect().width;
  if(barWidth!==chapterBarWidth||!chapterBarHeight){
   const wasHidden=controls.hidden;controls.hidden=true;
   chapterBarHeight=bar.getBoundingClientRect().height;
   controls.hidden=false;chapterAtlasBarHeight=bar.getBoundingClientRect().height;
   chapterBarWidth=barWidth;controls.hidden=wasHidden;
  }
  currentChapter=chapters[0];
  for(const chapter of chapters){
   const height=chapter.number==='04'&&view==='full'?chapterAtlasBarHeight:chapterBarHeight;
   if(chapter.element.getClientRects().length&&chapter.element.getBoundingClientRect().top<=top+height+16)currentChapter=chapter;
  }
  const inFullAtlas=currentChapter.number==='04'&&view==='full';
  controls.hidden=!inFullAtlas;bar.dataset.chapter=currentChapter.number;
  sectionLink.textContent=currentChapter.number;sectionLink.href='#'+currentChapter.id;sectionLink.setAttribute('aria-label',currentChapter.number+' '+currentChapter.name);
  if(inFullAtlas){
   const line=top+bar.getBoundingClientRect().height+(document.getElementById('atlas-view-controls')?.getBoundingClientRect().height||0)+20;
   let city=null,stage=null;
   for(const item of cities){if(item.element.getBoundingClientRect().top<=line)city=item;else break;}
   for(const item of city?.stages||[]){if(item.element.getBoundingClientRect().top<=line)stage=item;else break;}
   setLocation(city,stage);
  }else genericLocation(currentChapter,view);
  applyOffset();detailsHeading.textContent=currentChapter.number+' / '+currentChapter.name;
  chapterButtons.forEach(button=>{if(button.dataset.readingJump===currentChapter.id)button.setAttribute('aria-current','location');else button.removeAttribute('aria-current');});
  updateProgress(top);
 }
 function schedule(){if(!frame)frame=requestAnimationFrame(update);}
 function belongsToAtlas(target){return target===section||!!target.closest('.case-atlas')||cities.some(city=>target===city.target);}
 function isChapter(target){return chapters.some(chapter=>chapter.element===target);}
 function positionTarget(target){
  bar.hidden=false;controls.hidden=!(belongsToAtlas(target)&&(document.documentElement.dataset.atlasView||'full')==='full');applyOffset(target);
  const offset=parseFloat(document.documentElement.style.getPropertyValue('--reading-navigation-offset'))||84;
  const drift=target.getBoundingClientRect().top-offset;
  if(Math.abs(drift)>.5)window.scrollTo({top:Math.max(0,window.scrollY+drift),behavior:'instant'});
 }
 function stopAnchorHold(){heldTarget=null;readingAnchorUserInterrupted=true;if(anchorFrame){cancelAnimationFrame(anchorFrame);anchorFrame=0;}}
 function scheduleAnchorHold(){
  schedule();if(!heldTarget||anchorFrame)return;
  anchorFrame=requestAnimationFrame(()=>{anchorFrame=0;if(!heldTarget?.isConnected)return;positionTarget(heldTarget);update();});
 }
 function jump(target,writeHistory=true){
  if(!target)return;if(anchorFrame){cancelAnimationFrame(anchorFrame);anchorFrame=0;}
  heldTarget=target;readingAnchorUserInterrupted=false;positionTarget(target);
  if(writeHistory&&target.id){const url=new URL(location.href);url.hash=target.id;if(url.href!==location.href)history.pushState(null,'',url);}
  update();scheduleAnchorHold();
 }
 chapterButtons.forEach(button=>button.addEventListener('click',()=>{closeDetails();detailsTrigger.focus({preventScroll:true});detailsDismissed=true;detailsKeyboard=false;refreshDetails();jump(document.getElementById(button.dataset.readingJump));}));
 citySelect.addEventListener('change',()=>{const city=cities.find(item=>item.key===citySelect.value);if(city){setLocation(city,null);jump(city.target);}});
 stageSelect.addEventListener('change',()=>{const city=cities.find(item=>item.key===citySelect.value);if(city)jump(city.stages.find(item=>item.key===stageSelect.value)?.target||city.target);});
 document.addEventListener('click',event=>{
  if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.altKey||event.shiftKey)return;
  const link=event.target.closest('a[href^="#"]');if(!link||link.target||link.hasAttribute('download'))return;
  let id;try{id=decodeURIComponent(link.hash.slice(1));}catch{return;}
  const target=document.getElementById(id);if(!target||(!belongsToAtlas(target)&&!isChapter(target)))return;
  if(belongsToAtlas(target)&&!isChapter(target)&&(document.documentElement.dataset.atlasView||'full')!=='full')return;
  event.preventDefault();jump(target);
 });
 function restoreAtlasHash(){
  let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
  const target=document.getElementById(id);
  if(target&&(isChapter(target)||(belongsToAtlas(target)&&(document.documentElement.dataset.atlasView||'full')==='full')))jump(target,false);
  else{stopAnchorHold();schedule();}
 }
 let stageCorrectionSequence=0;
 document.addEventListener('change',event=>{
  const select=event.target;
  if(!(select instanceof HTMLSelectElement)||!select.matches('#atlas-compact-panel .av-stage-jumpbar [data-av-control="stage"]')||document.documentElement.dataset.atlasView!=='stage')return;
  const key=select.value;const sequence=++stageCorrectionSequence;
  requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>{
   if(sequence!==stageCorrectionSequence||document.documentElement.dataset.atlasView!=='stage'||!select.isConnected)return;
   const target=document.getElementById('atlas-compare-'+key);const toolbar=document.getElementById('atlas-view-controls');const jumpbar=document.querySelector('#atlas-compact-panel .av-stage-jumpbar');
   if(!target?.getClientRects().length||!toolbar||!jumpbar)return;
   const offset=Math.max(0,globalNav.getBoundingClientRect().bottom)+bar.getBoundingClientRect().height+toolbar.getBoundingClientRect().height+jumpbar.getBoundingClientRect().height+18;
   const drift=target.getBoundingClientRect().top-offset;if(Math.abs(drift)>.5)window.scrollBy({top:drift,behavior:'instant'});schedule();
  })));
 });
 for(const type of ['wheel','touchstart','pointerdown'])window.addEventListener(type,()=>{stopAnchorHold();stageCorrectionSequence++;},{passive:true,capture:true});
 window.addEventListener('keydown',event=>{stageCorrectionSequence++;if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','PageUp','PageDown','Home','End',' ','Tab'].includes(event.key))stopAnchorHold();},{capture:true});
 window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',scheduleAnchorHold,{passive:true});window.addEventListener('hashchange',restoreAtlasHash);
 window.addEventListener('load',()=>{if(!readingAnchorUserInterrupted)restoreAtlasHash();else schedule();});
 document.addEventListener('reading-card-rows-aligned',scheduleAnchorHold);document.addEventListener('atlas-view-toolbar-resized',schedule);
 new MutationObserver(schedule).observe(document.documentElement,{attributes:true,attributeFilter:['data-atlas-view']});
 // Page ResizeObserver corrects anchor geometry without a pass per lazy image.
 if(document.fonts)document.fonts.ready.then(scheduleAnchorHold);
 if('ResizeObserver' in window){const observer=new ResizeObserver(scheduleAnchorHold);observer.observe(globalNav);observer.observe(bar);observer.observe(page);}
 setLocation(null,null);schedule();
})();

/* r09 continuous stage atlas. Content is read from the unchanged full atlas. */
(function () {
  'use strict';
  var DEFAULT_METHODS = {
    static: [
      {id: 'fw', label: 'Frank–Wolfe'},
      {id: 'algorithm-b', label: 'Algorithm B'},
      {id: 'finite-path', label: 'Finite-path reference'}
    ],
    finite: [
      {id: 'cg', label: 'Column generation'},
      {id: 'lagrangian', label: 'Lagrangian'},
      {id: 'admm', label: 'ADMM'}
    ]
  };
  function node(tag, cls, text) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null && text !== '') el.textContent = String(text);
    return el;
  }
  function cleanText(value) { return value == null ? '' : String(value).trim(); }
  function safeURL(value) {
    var url = cleanText(value);
    return url && !/^(?:javascript|data|vbscript):/i.test(url) ? url : '';
  }
  function stageFor(city, key) {
    return (city.stages || []).find(function (s) { return s.key === key; });
  }
  function availableCards(stage, city, scale) {
    return (stage && stage.cards || []).filter(function (card) {
      if (city.id !== 'sioux-falls' && city.id !== 'sioux') return true;
      if (!card.scale || String(card.scale) === 'shared') return true;
      if (Array.isArray(card.scale)) return card.scale.map(String).indexOf(scale) !== -1;
      var scales = String(card.scale).match(/200|250/g);
      return !scales || scales.indexOf(scale) !== -1;
    });
  }
  function selectedID(selection, scale) {
    if (typeof selection === 'string') return selection;
    if (!selection || typeof selection !== 'object') return '';
    if (selection[scale]) return selectedID(selection[scale], scale);
    if (selection.default) return selectedID(selection.default, scale);
    return selection.id || selection.cardId || '';
  }
  function selectedText(value, scale) {
    if (typeof value === 'string') return value;
    if (!value || typeof value !== 'object') return '';
    return selectedText(value[scale] || value.default, scale);
  }
  function findCard(stage, city, selection, scale) {
    var id = selectedID(selection, scale);
    var cards = availableCards(stage, city, scale);
    return cards.find(function (c) { return c.id === id; }) || null;
  }
  function paragraph(parent, cls, value) {
    var text = cleanText(value);
    if (text) parent.appendChild(node('p', cls, text));
  }
  function render(container, model, state, onChange, onFull, renderOptions) {
    renderOptions = renderOptions || {};
    model = model || {};
    state = state || {};
    var cities = model.cities || [];
    var scale = String(state.siouxOd || '200');
    var activeCity = cities.find(function (c) { return c.id === state.city; }) || cities[0];
    var stageOrder = model.stageOrder || Array.from(new Set(cities.flatMap(function (c) {
      return (c.stages || []).map(function (s) { return s.key; });
    })));
    var key = stageOrder.indexOf(state.stage) !== -1 ? state.stage : stageOrder[0];
    var shell = node('div', 'mcl-atlas-compact');
    shell.dataset.view = state.view === 'stage' ? 'stage' : 'city';
    function update(patch, focusKey) {
      onChange(patch);
      if (focusKey) queueMicrotask(function () {
        var control = container.querySelector('[data-av-control="' + focusKey + '"]');
        if (control) control.focus({preventScroll: true});
      });
    }
    function openStage(stage, card) {
      if (stage) onFull(stage.id, card && card.id);
    }
    function scalePicker(parent, context) {
      var group = node('div', 'av-instance-picker');
      var label = node('span', 'av-control-label', context === 'city' ? 'Optimization instance' : 'Sioux Falls instance');
      group.appendChild(label);
      var options = node('div', 'av-segmented');
      options.setAttribute('role', 'group');
      options.setAttribute('aria-label', label.textContent);
      ['200', '250'].forEach(function (od) {
        var button = node('button', 'av-choice', od + ' ODs');
        button.type = 'button';
        button.dataset.avControl = 'scale-' + od;
        button.setAttribute('aria-pressed', String(scale === od));
        button.addEventListener('click', function () { update({siouxOd: od}, 'scale-' + od); });
        options.appendChild(button);
      });
      group.appendChild(options);
      if (context === 'city') paragraph(group, 'av-control-note', 'Applies to finite optimization.');
      parent.appendChild(group);
    }
    function sharedNotice(parent, city, includeCityName) {
      var notice = city && city.sharedNotice;
      if (!notice || !cleanText(notice.text)) return;
      var details = node('details', 'av-shared-notice');
      var label = 'Sources and model scope · © OpenStreetMap contributors / ODbL 1.0';
      if (includeCityName) label = city.name + ' · ' + label;
      details.appendChild(node('summary', '', label));
      paragraph(details, 'av-shared-notice-text', notice.text);
      var href = safeURL(notice.href);
      if (href) {
        var link = node('a', '', 'Complete source and model notice');
        link.href = href;
        details.appendChild(link);
      }
      parent.appendChild(details);
    }
    function actionLink(parent, stage, card, text, cls) {
      var button = node('button', cls || 'av-open', text);
      button.type = 'button';
      button.addEventListener('click', function () { openStage(stage, card); });
      parent.appendChild(button);
      return button;
    }
    function evidenceLinks(parent, city, card) {
      var row = node('div', 'av-evidence-links');
      var href = safeURL(card && (card.evidence || (!/\.(svg|png|pdf)(?:[?#]|$)/i.test(card.href || '') && card.href)) || city.volume);
      if (href) {
        var link = node('a', '', 'Read complete evidence');
        link.href = href;
        row.appendChild(link);
      }
      if (city.directFigureLinks && card && card.links) {card.links.forEach(function(item){var href = safeURL(item.href);if(!href)return;var assetLink = node('a', '', item.label);assetLink.href = href;row.appendChild(assetLink);});}
      if (row.childNodes.length) parent.appendChild(row);
    }
    function fullCount(parent, city, stage, selectedCard) {
      if (selectedCard && selectedCard.currentMethodFigureCount) {
        actionLink(parent, stage, selectedCard, "View all " + selectedCard.currentMethodFigureCount + " " + selectedCard.currentMethodLabel + " figures", "av-open av-stage-link");
        return;
      }
      var cards = availableCards(stage, city, scale);
      var count = cards.reduce(function (sum, card) { return sum + (Number(card.figureCount) || 1); }, 0);
      if (count) actionLink(parent, stage, null, 'View all ' + count + ' figure' + (count === 1 ? '' : 's') + ' in this stage', 'av-open av-stage-link');
      else if (stage && stage.id) actionLink(parent, stage, null, 'Read stage scope', 'av-open av-stage-link');
    }
    function figure(parent, city, stage, card, compare, comparisonNote) {
      var source = safeURL(card.src);
      var direct = city.directFigureLinks && safeURL(card.evidence);
      var series = card.r11Figures && card.r11Figures.length ? card.r11Figures : (source ? [{src:source,title:card.title}] : []);
      var imageGroup = node('div','av-figure-series');imageGroup.dataset.columns=String(Math.min(3,series.length));
      series.forEach(function (item) {
        var imageButton = node(direct ? 'a' : 'button', 'av-figure');
        if (direct) imageButton.href = safeURL(card.evidence);
        else {imageButton.type='button';imageButton.addEventListener('click',function(){openStage(stage,card);});}
        imageButton.setAttribute('aria-label','Open '+item.title+' in the complete city record');
        var img=node('img');img.alt=item.title||'';img.loading='lazy';img.decoding='async';if(window.MCLPreviewImage)window.MCLPreviewImage(img,safeURL(item.src));else img.src=safeURL(item.src);imageButton.appendChild(img);imageGroup.appendChild(imageButton);
      });
      if (series.length) parent.appendChild(imageGroup);
      parent.appendChild(node(compare ? 'h4' : 'h5', 'av-figure-title', card.title));
      paragraph(parent, 'av-instance', card.instance);
      var scope = cleanText(stage.scope);
      var summary = cleanText(card.summary);
      if (summary) paragraph(parent, 'av-scope', summary);
      if (scope && scope !== summary) paragraph(parent, 'av-scope', scope);
      if (comparisonNote) paragraph(parent, 'av-scope av-comparison-note', comparisonNote);
      else if (compare && card.methodSummary && card.methodSummary !== scope && card.methodSummary !== summary) paragraph(parent, 'av-scope av-method-scope', card.methodSummary);
      var caption = cleanText(card.caption);
      if (caption && caption !== summary && caption !== scope) {
        var details = node('details', 'av-caption-details');
        details.appendChild(node('summary', '', 'Figure description'));
        paragraph(details, '', caption);
        parent.appendChild(details);
      }
      if (city.sharedNotice && card.notice) {
        var attribution = node('small', 'av-attribution');
        var sourceLink = node('a', '', '© OpenStreetMap contributors · ODbL 1.0');
        sourceLink.href = 'https://www.openstreetmap.org/copyright';
        attribution.appendChild(sourceLink);
        attribution.appendChild(node('span', '', ' · Modeled scenario, not observed traffic.'));
        parent.appendChild(attribution);
      }
      var footer = node('div', 'av-card-footer');
      if (direct) { var directLink = node('a', 'av-open av-figure-link', 'Open figure in complete city record'); directLink.href = safeURL(card.evidence); footer.appendChild(directLink); }
      else actionLink(footer, stage, card, 'Open figure in full atlas', 'av-open av-figure-link');
      fullCount(footer, city, stage, card);
      evidenceLinks(footer, city, card);
      parent.appendChild(footer);
    }
    function empty(parent, city, stage, message) {
      var box = node('div', 'av-empty');
      box.appendChild(node('span', 'av-status', stage && stage.status === 'not-run' ? 'Not run for this benchmark' : 'Scope note'));
      paragraph(box, '', message || stage && stage.scope || 'Open the complete city evidence for the available material.');
      parent.appendChild(box);
      var footer = node('div', 'av-card-footer');
      fullCount(footer, city, stage);
      evidenceLinks(footer, city, null);
      parent.appendChild(footer);
    }
    if (!activeCity) {
      paragraph(shell, 'av-scope', 'No city evidence is available.');
      container.replaceChildren(shell);
      return;
    }
    if (state.view !== 'stage') {
      var top = node('div', 'av-controls av-city-controls');
      var picker = node('div', 'av-segmented av-city-picker');
      picker.setAttribute('role', 'group');
      picker.setAttribute('aria-label', 'Choose a city');
      cities.forEach(function (city) {
        var button = node('button', 'av-choice', city.name);
        button.type = 'button';
        button.dataset.avControl = 'city-' + city.id;
        button.setAttribute('aria-pressed', String(city.id === activeCity.id));
        button.addEventListener('click', function () { update({city: city.id}, 'city-' + city.id); });
        picker.appendChild(button);
      });
      top.appendChild(picker);
      if (activeCity.id === 'sioux-falls' || activeCity.id === 'sioux') scalePicker(top, 'city');
      shell.appendChild(top);
      var heading = node('div', 'av-view-heading');
      heading.appendChild(node('h3', '', activeCity.name));
      paragraph(heading, 'av-intro', activeCity.summary);
      if (activeCity.directFigureLinks) {var recordLink = node('a', 'av-open', 'Read complete city record');recordLink.href = safeURL(activeCity.volume);heading.appendChild(recordLink);}
      paragraph(heading, 'av-help', 'One selected figure per stage. Open a stage to read its complete figure set and source records.');
      shell.appendChild(heading);
      sharedNotice(shell, activeCity, false);
      var grid = node('div', 'av-city-grid');
      var unavailableStages = [];
      stageOrder.forEach(function (stageKey, index) {
        var stage = stageFor(activeCity, stageKey);
        if (!stage) return;
        if ((stage.status === 'not-run' || activeCity.textOnlyStages) && !availableCards(stage, activeCity, scale).length) { unavailableStages.push(stage); return; }
        var panelMethods = stage.methods || model.methods && model.methods[stageKey] || DEFAULT_METHODS[stageKey] || [];
        var requestedMethod = state.cityMethods && state.cityMethods[stageKey];
        var panelMethod = panelMethods.some(function (m) { return m.id === requestedMethod; }) ? requestedMethod : panelMethods[0] && panelMethods[0].id;
        var panelComparisons = model.comparisons && model.comparisons[stageKey];
        var selection = panelMethods.length && panelComparisons ? panelComparisons[panelMethod] && panelComparisons[panelMethod][activeCity.id] : model.representatives && model.representatives[activeCity.id] && model.representatives[activeCity.id][stageKey];
        var card = findCard(stage, activeCity, selection, scale);
        var cell = node('article', 'av-card av-stage-card');
        cell.dataset.avStage = stageKey;
        var cellTitle = node('h4', 'av-stage-title');
        cellTitle.appendChild(node('span', 'av-stage-number', (model.stageNumbers && model.stageNumbers[stageKey] || String(index + 1).padStart(2, '0'))));
        cellTitle.appendChild(node('span', '', stage.title));
        cell.appendChild(cellTitle);
        var panelControl = node('div', 'av-panel-control');
        if (panelMethods.length) {
          var panelLabel = node('label', 'av-panel-method');
          panelLabel.appendChild(node('span', '', panelMethods.length + ' methods'));
          var panelSelect = node('select', 'av-select');
          panelSelect.dataset.avControl = 'city-method-' + stageKey;
          panelSelect.setAttribute('aria-label', activeCity.name + ' ' + stage.title + ' method');
          panelMethods.forEach(function (m) {
            var option = node('option', '', m.label);
            option.value = m.id;
            option.selected = m.id === panelMethod;
            panelSelect.appendChild(option);
          });
          panelSelect.addEventListener('change', function () {
            var nextMethods = Object.assign({}, state.cityMethods || {});
            nextMethods[stageKey] = panelSelect.value;
            update({cityMethods: nextMethods}, 'city-method-' + stageKey);
          });
          panelLabel.appendChild(panelSelect);
          panelControl.appendChild(panelLabel);
        } else {
          var overviewCount = availableCards(stage, activeCity, scale).reduce(function (sum, c) { return sum + (Number(c.figureCount) || 1); }, 0);
          panelControl.appendChild(node('span', 'av-overview-label', '1 of ' + overviewCount + ' figure' + (overviewCount === 1 ? '' : 's')));
        }
        cell.appendChild(panelControl);
        if (card) {
          cell.dataset.avFigure = card.id;
          var panelNote = model.comparisonNotes && model.comparisonNotes[stageKey] && model.comparisonNotes[stageKey][panelMethod] && model.comparisonNotes[stageKey][panelMethod][activeCity.id];
          figure(cell, activeCity, stage, card, false, selectedText(panelNote, scale));
        } else empty(cell, activeCity, stage, stage.currentMethodNotes && stage.currentMethodNotes[panelMethod]);
        grid.appendChild(cell);
      });
      if (grid.children.length === 4) grid.classList.add('av-city-grid-four');
      shell.appendChild(grid);
      if (unavailableStages.length) {
        var coverage = node('details', 'av-unavailable-stages');
        coverage.appendChild(node('summary', '', unavailableStages.length + ' stages are outside this benchmark’s computed scope'));
        var list = node('dl', 'av-coverage-list');
        unavailableStages.forEach(function (stage) {
          list.appendChild(node('dt', '', stage.title));
          list.appendChild(node('dd', '', stage.scope));
        });
        coverage.appendChild(list);
        shell.appendChild(coverage);
      }
    } else {
      function stageSection(stageKey, index) {
        var section = node('section', 'av-stage-section');
        section.id = 'atlas-compare-' + stageKey;
        section.dataset.avStageBlock = stageKey;
        var firstStage = cities.map(function (city) { return stageFor(city, stageKey); }).find(Boolean);
        var comparisons = model.comparisons && model.comparisons[stageKey];
        var methods = model.methods && model.methods[stageKey] || DEFAULT_METHODS[stageKey] || [];
        var requested = state.cityMethods && state.cityMethods[stageKey];
        var method = methods.some(function (m) { return m.id === requested; }) ? requested : methods[0] && methods[0].id;
        var header = node('div', 'av-stage-section-header');
        var heading = node('h3', 'av-stage-heading');
        heading.id = section.id + '-title';
        heading.appendChild(node('span', 'av-stage-range', model.stageNumbers && model.stageNumbers[stageKey] || String(index + 1).padStart(2, '0')));
        heading.appendChild(node('span', '', firstStage && firstStage.title || stageKey));
        section.setAttribute('aria-labelledby', heading.id);
        header.appendChild(heading);
        if (methods.length) {
          var controls = node('div', 'av-controls av-method-controls');
          var methodLabel = node('label', 'av-select-label');
          methodLabel.appendChild(node('span', 'av-control-label', 'Method'));
          var methodSelect = node('select', 'av-select');
          methodSelect.dataset.avControl = 'method-' + stageKey;
          methodSelect.setAttribute('aria-label', (firstStage && firstStage.title || stageKey) + ' method');
          methods.forEach(function (m) {
            var option = node('option', '', m.label);
            option.value = m.id;option.selected = m.id === method;
            methodSelect.appendChild(option);
          });
          methodSelect.addEventListener('change', function () { update({stage: stageKey, method: methodSelect.value}, 'method-' + stageKey); });
          methodLabel.appendChild(methodSelect);controls.appendChild(methodLabel);
          if (stageKey === 'finite') scalePicker(controls, 'stage');
          header.appendChild(controls);
          var definition = methods.find(function (m) { return m.id === method; });
          paragraph(header, 'av-intro', definition && definition.description);
        }
        section.appendChild(header);
        var grid = node('div', 'av-comparison-grid');
        var textScopes = node('dl', 'av-coverage-list six-city-stage-scope');
        cities.forEach(function (city) {
          var stage = stageFor(city, stageKey);if (!stage) return;
          var selection = comparisons && methods.length ? comparisons[method] && comparisons[method][city.id] : model.representatives && model.representatives[city.id] && model.representatives[city.id][stageKey];
          var card = findCard(stage, city, selection, scale);
          if (!card && city.textOnlyStages) {textScopes.appendChild(node('dt', '', city.name));textScopes.appendChild(node('dd', '', methods.length ? (stage.scope + ' No saved ' + method + ' figure is supplied for this case.') : stage.scope));return;}
          var cell = node('article', 'av-card av-comparison-card');
          cell.dataset.avCity = city.id;
          cell.appendChild(node('h4', 'av-city-title', city.name));
          var note = model.comparisonNotes && model.comparisonNotes[stageKey] && model.comparisonNotes[stageKey][method] && model.comparisonNotes[stageKey][method][city.id];
          note = selectedText(note, scale);
          if (card) {cell.dataset.avFigure = card.id;figure(cell, city, stage, card, true, note);}
          else empty(cell, city, stage, note);
          grid.appendChild(cell);
        });
        section.appendChild(grid);if (textScopes.childNodes.length) section.appendChild(textScopes);return section;
      }
      // Method/instance changes replace only their own stage, preserving all other DOM.
      var existing = renderOptions.patchStage && container.querySelector('[data-av-stage-block="' + renderOptions.patchStage + '"]');
      if (existing) {existing.replaceWith(stageSection(renderOptions.patchStage, stageOrder.indexOf(renderOptions.patchStage)));return;}
      var controls = node('nav', 'av-controls av-stage-controls av-stage-jumpbar');
      controls.setAttribute('aria-label', 'Navigate the stage atlas');
      var label = node('label', 'av-select-label');
      label.appendChild(node('span', 'av-control-label', 'Jump to stage'));
      var select = node('select', 'av-select');select.dataset.avControl = 'stage';
      stageOrder.forEach(function (stageKey, index) {
        var stage = cities.map(function (c) { return stageFor(c, stageKey); }).find(Boolean);
        var option = node('option', '', (model.stageNumbers && model.stageNumbers[stageKey] || String(index + 1).padStart(2, '0')) + ' · ' + (stage && stage.title || stageKey));
        option.value = stageKey;option.selected = stageKey === key;select.appendChild(option);
      });
      select.addEventListener('change', function () { onChange({jumpToStage: select.value}); });
      label.appendChild(select);controls.appendChild(label);
      paragraph(controls, 'av-jump-help', 'All stages are shown below. This menu moves to a stage.');
      shell.appendChild(controls);
      paragraph(shell, 'av-help av-stage-introduction', 'The atlas contains ' + cities.length + ' city cases. Each stage retains the available figures and explicit scope notes; open the complete evidence for each model instance.');
      cities.forEach(function (city) { sharedNotice(shell, city, true); });
      stageOrder.forEach(function (stageKey, index) {shell.appendChild(stageSection(stageKey, index));});
    }
    container.replaceChildren(shell);
  }
  window.MCLAtlasViews = {render: render};
})();

(function initAtlasViews(){
'use strict';
const model=window.MCL_ATLAS_MODEL;
const shell=document.getElementById('atlas-view-shell');
const toolbar=document.getElementById('atlas-view-controls');
const full=document.getElementById('atlas-full-panel');
const compact=document.getElementById('atlas-compact-panel');
const status=document.getElementById('atlas-view-status');
const tabs=[...toolbar.querySelectorAll('[data-atlas-view]')];
const names=Object.fromEntries(model.cities.map(c=>[c.id,c.name]));
const originalNav=document.querySelector('body > .nav');
const locationBar=document.querySelector('.reading-location-bar');
// BERKELEY_CITY_METHOD_NORMALIZER_R1
const methods={static:['fw','algorithm-b','finite-path'],finite:['cg','lagrangian','admm']};
function methodIds(key,cityId,view){
 const city=model.cities.find(c=>c.id===cityId);
 const stage=city?.stages.find(s=>s.key===key);
 const definitions=view==='city'&&stage?.methods?stage.methods:model.methods?.[key];
 return definitions?.map(m=>m.id)||methods[key]||[];
}
function normalized(next){
 const s={view:'full',city:'boston',stage:'sources',method:'fw',siouxOd:'200',...next};
 if(!['full','city','stage'].includes(s.view))s.view='full';
 if(!names[s.city])s.city='boston';
 if(!model.stageOrder.includes(s.stage))s.stage='sources';
 const active=methodIds(s.stage,s.city,s.view);
 if(methods[s.stage]&&!active.includes(s.method))s.method=active[0];
 s.siouxOd=s.siouxOd==='250'?'250':'200';
 s.cityMethods={static:'fw',finite:'cg',...s.cityMethods};
 for(const key of ['static','finite']){
  const allowed=methodIds(key,s.city,s.view);
  if(!allowed.includes(s.cityMethods[key]))s.cityMethods[key]=allowed[0];
 }
 return s;
}
function fromUrl(){
 const p=new URL(location.href).searchParams;
 const next={view:p.get('atlas-view')||'full',city:p.get('city')||'boston',stage:p.get('stage')||'sources',method:p.get('method')||'fw',siouxOd:p.get('sioux-od')||'200',cityMethods:{static:p.get('static-method')||'fw',finite:p.get('finite-method')||'cg'}};
 const hashKey=location.hash.replace('#atlas-compare-','');
 if(location.hash.startsWith('#atlas-compare-')&&model.stageOrder.includes(hashKey))next.stage=hashKey;
 if(p.has('method')&&methodIds(next.stage,next.city,next.view).includes(next.method))next.cityMethods[next.stage]=next.method;
 return normalized(next);
}
let state=fromUrl();
function saveUrl(hash){
 const url=new URL(location.href);
 url.searchParams.set('atlas-view',state.view);url.searchParams.set('city',state.city);
 url.searchParams.set('stage',state.stage);url.searchParams.set('sioux-od',state.siouxOd);
 url.searchParams.set('static-method',state.cityMethods.static);url.searchParams.set('finite-method',state.cityMethods.finite);
 if(methods[state.stage])url.searchParams.set('method',state.method);else url.searchParams.delete('method');
 if(hash!==undefined)url.hash=hash;
 if(url.href!==location.href)history.pushState({atlasView:state.view},'',url);
}
// Preserve one set of tabs: only its presentation changes after the original row scrolls away.
const viewPanel=document.createElement('div');viewPanel.className='atlas-view-panel';viewPanel.id='atlas-view-panel';
viewPanel.append(...toolbar.childNodes);
const viewTrigger=document.createElement('button');viewTrigger.type='button';viewTrigger.className='atlas-view-trigger';
viewTrigger.setAttribute('aria-controls',viewPanel.id);viewTrigger.setAttribute('aria-expanded','false');
toolbar.append(viewTrigger,viewPanel);
const viewOrigin=document.createElement('span');viewOrigin.className='atlas-view-origin';viewOrigin.setAttribute('aria-hidden','true');
const viewSpacer=document.createElement('div');viewSpacer.className='atlas-view-spacer';viewSpacer.setAttribute('aria-hidden','true');
toolbar.before(viewOrigin);toolbar.after(viewSpacer);
let viewDocked=false,viewExpandedHeight=0,viewMeasuredWidth=0,viewHovered=false,viewPinned=false,viewDismissed=false;
function refreshViewDisclosure(){
 const keyboardFocus=toolbar.contains(document.activeElement)&&document.activeElement.matches(':focus-visible');
 const open=viewDocked&&!viewDismissed&&(viewHovered||viewPinned||keyboardFocus);
 toolbar.classList.toggle('is-open',open);
 viewTrigger.setAttribute('aria-expanded',String(open));
 viewPanel.inert=viewDocked&&!open;
 if(viewDocked&&!open)viewPanel.setAttribute('aria-hidden','true');else viewPanel.removeAttribute('aria-hidden');
}
function dockViewControls(top){
 // Measure at full width before deciding to collapse; the spacer preserves the document's height.
 const width=shell.clientWidth;
 if(!viewDocked||width!==viewMeasuredWidth){
  toolbar.classList.remove('is-docked');
  viewExpandedHeight=toolbar.getBoundingClientRect().height;viewMeasuredWidth=width;
  toolbar.classList.toggle('is-docked',viewDocked);
 }
 const naturalBottom=viewOrigin.getBoundingClientRect().top+(parseFloat(getComputedStyle(toolbar).marginTop)||0)+viewExpandedHeight;
 const docked=naturalBottom<=top;
 if(docked!==viewDocked){
  viewDocked=docked;toolbar.classList.toggle('is-docked',docked);
  viewPinned=false;viewDismissed=false;viewHovered=docked&&toolbar.matches(':hover');
 }
 viewSpacer.style.height=(viewDocked?Math.max(0,viewExpandedHeight-toolbar.getBoundingClientRect().height):0)+'px';
 refreshViewDisclosure();
}
toolbar.addEventListener('pointerenter',event=>{if(event.pointerType==='touch')return;viewHovered=true;viewDismissed=false;refreshViewDisclosure();});
toolbar.addEventListener('pointerleave',event=>{if(event.pointerType==='touch')return;viewHovered=false;viewPinned=false;refreshViewDisclosure();});
toolbar.addEventListener('focusin',()=>{viewDismissed=false;refreshViewDisclosure();});
toolbar.addEventListener('focusout',()=>requestAnimationFrame(refreshViewDisclosure));
viewTrigger.addEventListener('click',()=>{viewPinned=!viewPinned;viewDismissed=!viewPinned;refreshViewDisclosure();});
toolbar.addEventListener('keydown',event=>{
 if(event.key!=='Escape'||!viewDocked)return;
 event.preventDefault();viewTrigger.focus();viewPinned=false;viewHovered=false;viewDismissed=true;refreshViewDisclosure();
});
document.addEventListener('pointerdown',event=>{
 if(!viewDocked||toolbar.contains(event.target))return;
 viewPinned=false;viewHovered=false;viewDismissed=true;refreshViewDisclosure();
});
let layoutFrame=0;
function updateToolbar(){
 layoutFrame=0;
 const navHeight=Math.max(0,originalNav?.getBoundingClientRect().bottom||0);
 const locationHeight=locationBar&&!locationBar.hidden?locationBar.getBoundingClientRect().height:0;
 const v=(navHeight+locationHeight)+'px';
 if(shell.style.getPropertyValue('--atlas-view-top')!==v)shell.style.setProperty('--atlas-view-top',v);
 shell.style.setProperty('--atlas-global-nav-height',navHeight+'px');
 dockViewControls(navHeight+locationHeight);
 const height=toolbar.getBoundingClientRect().height+'px';
 if(shell.style.getPropertyValue('--atlas-viewbar-height')!==height){
  shell.style.setProperty('--atlas-viewbar-height',height);
  document.dispatchEvent(new Event('atlas-view-toolbar-resized'));
 }
}
function scheduleToolbar(){if(!layoutFrame)layoutFrame=requestAnimationFrame(updateToolbar);}
function showControls(){requestAnimationFrame(()=>{updateToolbar();const navBottom=Math.max(0,originalNav?.getBoundingClientRect().bottom||0);window.scrollTo({top:Math.max(0,window.scrollY+shell.getBoundingClientRect().top-navBottom-8),behavior:'instant'});});}
function currentFullContext(){
 const selects=[...document.querySelectorAll('.reading-location-select')];
 const city=selects[0]?.value;if(names[city])state.city=city;
 const stage=selects[1]?.value;if(stage?.startsWith(state.city+'-'))state.stage=stage.slice(state.city.length+1);
 const scale=document.querySelector('[data-stage="sioux-falls-finite"]')?.dataset.selectedOd;
 if(scale)state.siouxOd=scale;
}
function render(renderOptions){
 state=normalized(state);document.documentElement.dataset.atlasView=state.view;
 const isFull=state.view==='full';full.hidden=!isFull;compact.hidden=isFull;
 for(const tab of tabs){const selected=tab.dataset.atlasView===state.view;tab.setAttribute('aria-selected',String(selected));tab.tabIndex=selected?0:-1;}
 if(!isFull){
  if(locationBar)locationBar.hidden=true;
  compact.setAttribute('aria-labelledby','atlas-tab-'+state.view);
  window.MCLAtlasViews.render(compact,model,state,change,openFull,renderOptions);
 }else{
  compact.replaceChildren();
  document.dispatchEvent(new CustomEvent('atlas-sioux-scale',{detail:{scale:state.siouxOd}}));
  if(typeof scheduleReadingCardAlignment==='function')scheduleReadingCardAlignment();
 }
 viewTrigger.textContent='View: '+(isFull?'Full atlas':state.view==='city'?'By city':'By stage')+' ▾';
 viewTrigger.setAttribute('aria-label','Choose atlas view. Current view: '+(isFull?'Full atlas':state.view==='city'?'By city':'By stage'));
 status.textContent=isFull?'All figures, in the existing reading order':state.view==='city'?'Selected figures · '+names[state.city]:'All stages · ' + model.cities.length + ' city records';
 scheduleToolbar();window.dispatchEvent(new Event('scroll'));
}
function change(patch){
 if(patch.jumpToStage){jumpStage(patch.jumpToStage);return;}
 const next={...state,...patch,cityMethods:{...state.cityMethods,...patch.cityMethods}};
 if(patch.cityMethods){
  const changed=['static','finite'].find(k=>patch.cityMethods[k]&&patch.cityMethods[k]!==state.cityMethods[k]);
  if(changed){next.stage=changed;next.method=next.cityMethods[changed];}
 }
 if(patch.siouxOd&&next.view==='stage'){next.stage='finite';next.method=next.cityMethods.finite;}
 if(patch.stage&&methods[patch.stage]&&!patch.method)next.method=next.cityMethods[patch.stage];
 if(patch.method&&methods[next.stage])next.cityMethods[next.stage]=patch.method;
 state=normalized(next);
 const patchStage=state.view==='stage'?(patch.siouxOd?'finite':patch.stage||state.stage):null;
 saveUrl(patchStage?'atlas-compare-'+patchStage:'04-explore-the-three-cases');
 render(patchStage?{patchStage}:undefined);
}
function switchView(view){
 if(state.view==='full')currentFullContext();
 state=normalized({...state,view});
 saveUrl('04-explore-the-three-cases');render();showControls();
}
function openFull(stageId,cardId,siouxOd){
 const city=model.cities.find(c=>stageId.startsWith(c.id+'-'));
 if(!city)return;
 const stage=city.stages.find(s=>s.id===stageId);
 const card=stage?.cards.find(c=>c.id===cardId);
 if(stage?.status==='not-run'){location.href=stage.evidence||city.volume;return;}
 state=normalized({...state,view:'full',city:city.id,stage:stage?.key||state.stage,siouxOd:siouxOd||state.siouxOd});
 const anchor=card?.anchor||stageId;saveUrl(anchor);render();
 window.dispatchEvent(new PopStateEvent('popstate'));
 requestAnimationFrame(()=>{if(typeof alignReadingCardRows==='function')alignReadingCardRows();window.dispatchEvent(new HashChangeEvent('hashchange'));});
}
// Existing Section 03 and in-page evidence links reveal their original targets.
document.addEventListener('click',event=>{
 if(state.view==='full'||event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.altKey||event.shiftKey)return;
 const link=event.target.closest('a[href^="#"]');if(!link||link.target)return;
 let target;try{target=document.getElementById(decodeURIComponent(link.hash.slice(1)));}catch{return;}
 if(!target||!full.contains(target))return;
 event.preventDefault();
 const stage=target.closest('.atlas-stage');const card=target.closest('.atlas-card[data-figure]');
 const scale=target.closest('.sioux-instance-panel')?.dataset.siouxOd||state.siouxOd;
 if(stage){openFull(stage.dataset.stage,card?.dataset.figure,scale);return;}
 state=normalized({...state,view:'full',siouxOd:scale});saveUrl(target.id);render();
 requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'instant'}));
},true);
for(const tab of tabs){
 tab.addEventListener('click',()=>switchView(tab.dataset.atlasView));
 tab.addEventListener('keydown',event=>{
  let n=tabs.indexOf(tab);if(event.key==='ArrowRight')n=(n+1)%tabs.length;
  else if(event.key==='ArrowLeft')n=(n+tabs.length-1)%tabs.length;
  else if(event.key==='Home')n=0;else if(event.key==='End')n=tabs.length-1;else return;
  event.preventDefault();tabs[n].focus();switchView(tabs[n].dataset.atlasView);
 });
}

let stagePositionFrame=0,pendingStageJump=null;
function stageScrollOffset(){
 const globalBottom=Math.max(0,originalNav?.getBoundingClientRect().bottom||0);
 const jumpbar=compact.querySelector('.av-stage-jumpbar');
 return globalBottom+(locationBar&&!locationBar.hidden?locationBar.getBoundingClientRect().height:0)+toolbar.getBoundingClientRect().height+(jumpbar?.getBoundingClientRect().height||0)+18;
}
function jumpStage(key,writeHistory=true){
 if(state.view!=='stage'||!model.stageOrder.includes(key))return;
 const target=document.getElementById('atlas-compare-'+key);if(!target)return;
 state.stage=key;if(methods[key])state.method=state.cityMethods[key];
 const select=compact.querySelector('[data-av-control="stage"]');if(select)select.value=key;
 if(writeHistory)saveUrl(target.id);
 pendingStageJump=key;
 requestAnimationFrame(()=>{
  if(state.view!=='stage'||pendingStageJump!==key)return;
  updateToolbar();
  const top=Math.max(0,window.scrollY+target.getBoundingClientRect().top-stageScrollOffset());
  window.scrollTo({top,behavior:'instant'});
  state.stage=key;if(select)select.value=key;
  pendingStageJump=null;scheduleStagePosition();
 });
}
function updateStagePosition(){
 stagePositionFrame=0;
 if(state.view!=='stage'||pendingStageJump)return;
 const sections=[...compact.querySelectorAll('.av-stage-section')];if(!sections.length)return;
 const line=stageScrollOffset()+2;
 if(shell.getBoundingClientRect().bottom<line)return;
 let selected=sections[0];
 for(const section of sections){if(section.getBoundingClientRect().top<=line)selected=section;else break;}
 const key=selected.dataset.avStageBlock;
 state.stage=key;if(methods[key])state.method=state.cityMethods[key];
 const select=compact.querySelector('[data-av-control="stage"]');if(select&&select.value!==key)select.value=key;
}
function scheduleStagePosition(){if(!stagePositionFrame)stagePositionFrame=requestAnimationFrame(updateStagePosition);}
function restoreStagePosition(){
 if(state.view!=='stage')return;
 if(location.hash.startsWith('#atlas-compare-')||new URL(location.href).searchParams.has('stage'))jumpStage(state.stage,false);
 else showControls();
}
window.addEventListener('scroll',scheduleStagePosition,{passive:true});
window.addEventListener('resize',scheduleStagePosition,{passive:true});
window.addEventListener('hashchange',()=>{if(state.view==='stage'&&location.hash.startsWith('#atlas-compare-')){const key=location.hash.slice('#atlas-compare-'.length);jumpStage(key,false);}});

window.addEventListener('popstate',()=>{state=fromUrl();render();restoreStagePosition();});
window.addEventListener('resize',scheduleToolbar,{passive:true});
window.addEventListener('scroll',scheduleToolbar,{passive:true});
if(locationBar)new MutationObserver(scheduleToolbar).observe(locationBar,{attributes:true,attributeFilter:['hidden']});
if('ResizeObserver' in window){const ro=new ResizeObserver(scheduleToolbar);ro.observe(toolbar);if(originalNav)ro.observe(originalNav);if(locationBar)ro.observe(locationBar);}
render();
if(state.view==='stage')restoreStagePosition();
else if(state.view!=='full')showControls();
})();
