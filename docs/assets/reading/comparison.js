(function(){
  'use strict';
  var root=document.querySelector('.coverage-comparison');if(!root)return;
  var table=root.querySelector('.comparison-table'),scroller=root.querySelector('.cmp-scroll');
  var checks=Array.from(root.querySelectorAll('[data-cmp-city]'));
  var stage=root.querySelector('[data-cmp-stage]'),width=root.querySelector('[data-cmp-width]');
  var groups=Array.from(root.querySelectorAll('[data-cmp-group-toggle]'));
  var status=root.querySelector('[data-cmp-status]');
  function announce(){status.textContent=root.querySelector('[data-cmp-city-count]').textContent+', '+root.querySelector('[data-cmp-row-count]').textContent+'. Full descriptions are displayed.';}
  function rows(){
    groups.forEach(function(button){var body=button.closest('tbody');body.hidden=stage.value!=='all'&&stage.value!==body.dataset.group;body.querySelectorAll('.cmp-data-row').forEach(function(row){row.hidden=button.getAttribute('aria-expanded')!=='true';});});
    var n=Array.from(root.querySelectorAll('.cmp-data-row')).filter(function(row){return !row.hidden&&!row.closest('tbody').hidden;}).length;
    root.querySelector('[data-cmp-row-count]').textContent=n+' of 19 items';announce();
  }
  function cities(){
    var selected=checks.filter(function(c){return c.checked;}).map(function(c){return c.dataset.cmpCity;});root.style.setProperty('--cmp-city-count',String(selected.length));
    table.querySelectorAll('[data-city]').forEach(function(cell){cell.hidden=selected.indexOf(cell.dataset.city)<0;});
    table.querySelectorAll('.cmp-group-row td').forEach(function(cell){cell.colSpan=selected.length;});
    checks.forEach(function(c){c.disabled=selected.length===1&&c.checked;});
    root.querySelector('[data-cmp-custom-label]').textContent='Choose cities ('+selected.length+')';root.querySelector('[data-cmp-city-count]').textContent=selected.length+' cities';announce();
  }
  checks.forEach(function(c){c.addEventListener('change',cities);});
  groups.forEach(function(button){button.addEventListener('click',function(){var open=button.getAttribute('aria-expanded')!=='true';button.setAttribute('aria-expanded',String(open));button.querySelector('.cmp-icon').textContent=open?'−':'+';rows();});});
  stage.addEventListener('change',function(){if(stage.value!=='all'){var b=root.querySelector('[data-cmp-group-toggle="'+stage.value+'"]');b.setAttribute('aria-expanded','true');b.querySelector('.cmp-icon').textContent='−';}rows();scroller.scrollTop=0;});
  width.addEventListener('change',function(){root.dataset.columnWidth=width.value;scroller.scrollLeft=0;status.textContent='Column width changed; all text and links are retained.';});
  root.querySelector('[data-cmp-reset]').addEventListener('click',function(){checks.forEach(function(c){c.checked=true;});stage.value='all';groups.forEach(function(b){b.setAttribute('aria-expanded','true');b.querySelector('.cmp-icon').textContent='−';});root.querySelector('.cmp-cities').open=false;rows();cities();scroller.scrollTop=0;scroller.scrollLeft=0;});
  root.dataset.ready='true';rows();cities();
})();
