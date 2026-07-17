(() => {
  const workspace = document.querySelector('[data-media-workspace]');
  if (!workspace) return;
  const grid = workspace.querySelector('[data-library-grid]');
  const search = workspace.querySelector('[data-media-search]');
  const empty = workspace.querySelector('[data-empty-filter]');
  const visibleCount = workspace.querySelector('[data-visible-count]');
  let filter = 'all';

  function applyFilters() {
    if (!grid) return;
    const term = (search?.value || '').trim().toLowerCase();
    let visible = 0;
    grid.querySelectorAll('[data-media-item]').forEach(item => {
      const kind = item.dataset.kind;
      const supported = item.dataset.supported === 'true';
      const filterMatch = filter === 'all' || kind === filter || (filter === 'unsupported' && !supported);
      const searchMatch = !term || item.dataset.name.includes(term);
      item.hidden = !(filterMatch && searchMatch);
      if (!item.hidden) visible += 1;
    });
    if (empty) empty.hidden = visible !== 0;
    if (visibleCount) visibleCount.textContent = String(visible);
  }
  search?.addEventListener('input', applyFilters);
  workspace.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    workspace.querySelectorAll('[data-filter]').forEach(x => x.classList.toggle('is-active', x === button));
    applyFilters();
  }));
  workspace.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
    grid?.classList.toggle('is-list', button.dataset.view === 'list');
    workspace.querySelectorAll('[data-view]').forEach(x => x.classList.toggle('is-active', x === button));
  }));

  const drawer = workspace.querySelector('[data-details-drawer]');
  const backdrop = workspace.querySelector('[data-details-backdrop]');
  function closeDetails(){ drawer?.classList.remove('is-open'); drawer?.setAttribute('aria-hidden','true'); if(backdrop) backdrop.hidden=true; grid?.querySelectorAll('.is-selected').forEach(x=>x.classList.remove('is-selected')); }
  function openDetails(item){
    if (!drawer || item.dataset.kind === 'folder') return;
    grid?.querySelectorAll('.is-selected').forEach(x=>x.classList.remove('is-selected')); item.classList.add('is-selected');
    const set=(sel,val)=>{ const el=drawer.querySelector(sel); if(el) el.textContent=val||'—'; };
    set('[data-details-title]',item.dataset.title); set('[data-details-type]',item.dataset.type); set('[data-details-size]',item.dataset.size); set('[data-details-modified]',item.dataset.modified); set('[data-details-mime]',item.dataset.mime); set('[data-details-resolution]',item.dataset.resolution); set('[data-details-path]',item.dataset.path);
    const preview=drawer.querySelector('[data-details-preview]'); const source=item.querySelector('.media-card-preview img');
    if(preview){ preview.innerHTML=''; if(source){ const img=document.createElement('img'); img.src=source.src; img.alt=item.dataset.title; preview.appendChild(img); } else { const icon=document.createElement('span'); icon.textContent=item.dataset.kind==='video'?'▶':'📄'; preview.appendChild(icon); } }
    drawer.classList.add('is-open'); drawer.setAttribute('aria-hidden','false'); if(backdrop) backdrop.hidden=false;
  }
  grid?.addEventListener('click', e=>{ const item=e.target.closest('[data-media-item]'); if(item && !e.target.closest('a')) openDetails(item); });
  grid?.addEventListener('keydown', e=>{ if((e.key==='Enter'||e.key===' ') && e.target.matches('[data-media-item]')){ e.preventDefault(); openDetails(e.target); } });
  workspace.querySelector('[data-details-close]')?.addEventListener('click',closeDetails); backdrop?.addEventListener('click',closeDetails); document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDetails();});

  const playlist = document.getElementById('playlist-list'); let dragged = null;
  function syncOrder(){ const rows=[...(playlist?.querySelectorAll('.playlist-item')||[])]; rows.forEach((row,index)=>{ const idx=row.querySelector('.playlist-index'); if(idx) idx.textContent=String(index+1); }); const value=rows.map(row=>row.dataset.path).join('\n'); const a=document.getElementById('playlist-order-field'); const b=document.getElementById('sync-playlist-order-field'); if(a)a.value=value;if(b)b.value=value; }
  playlist?.addEventListener('click', event=>{ const button=event.target.closest('[data-move]'); if(!button)return; const row=button.closest('.playlist-item'); const direction=Number(button.dataset.move); if(direction<0&&row.previousElementSibling)playlist.insertBefore(row,row.previousElementSibling); if(direction>0&&row.nextElementSibling)playlist.insertBefore(row.nextElementSibling,row); syncOrder(); });
  playlist?.addEventListener('dragstart',event=>{dragged=event.target.closest('.playlist-item');dragged?.classList.add('dragging');}); playlist?.addEventListener('dragend',()=>{dragged?.classList.remove('dragging');dragged=null;syncOrder();}); playlist?.addEventListener('dragover',event=>{if(!dragged)return;event.preventDefault();const rows=[...playlist.querySelectorAll('.playlist-item:not(.dragging)')];const after=rows.reduce((closest,child)=>{const box=child.getBoundingClientRect();const offset=event.clientY-box.top-box.height/2;return offset<0&&offset>closest.offset?{offset,child}:closest;},{offset:Number.NEGATIVE_INFINITY,child:null}).child;after?playlist.insertBefore(dragged,after):playlist.appendChild(dragged);});

  const selectAll=workspace.querySelector('[data-select-all]'); const boxes=[...workspace.querySelectorAll('input[name="display_ids"]')]; const count=workspace.querySelector('[data-selected-display-count]'); const deploy=workspace.querySelector('[data-deploy-button]');
  function updateDisplayCount(){const n=boxes.filter(x=>x.checked).length;if(count)count.textContent=String(n);if(deploy&&boxes.length)deploy.disabled=n===0; if(selectAll)selectAll.textContent=n===boxes.length&&boxes.length?'Clear all':'Select all';}
  boxes.forEach(box=>box.addEventListener('change',updateDisplayCount)); selectAll?.addEventListener('click',()=>{const shouldSelect=boxes.some(box=>!box.checked);boxes.forEach(box=>{box.checked=shouldSelect;});updateDisplayCount();});
  workspace.querySelector('[data-scroll-to-deploy]')?.addEventListener('click',()=>document.getElementById('deploy-playlist')?.scrollIntoView({behavior:'smooth',block:'start'}));
  syncOrder(); applyFilters(); updateDisplayCount();
})();
/* v9.7 guided workflow additions */
(() => {
 const ws=document.querySelector('[data-media-workspace]'); if(!ws)return;
 const grid=ws.querySelector('[data-library-grid]'), list=document.getElementById('playlist-list');
 const picked=new Set();
 const mediaCards=()=>[...(grid?.querySelectorAll('[data-media-item]')||[])].filter(c=>c.dataset.supported==='true'&&c.dataset.kind!=='folder');
 function updatePicked(){mediaCards().forEach(c=>c.classList.toggle('is-picked',picked.has(c.dataset.path)));const n=ws.querySelector('[data-selected-media-count]');if(n)n.textContent=String(picked.size);const add=ws.querySelector('[data-add-selected-media]');if(add)add.disabled=!picked.size;}
 function playlistPaths(){return new Set([...(list?.querySelectorAll('.playlist-item')||[])].map(r=>r.dataset.path));}
 function addCard(card){if(!list||playlistPaths().has(card.dataset.path))return;const row=document.createElement('div');row.className='playlist-item';row.draggable=true;row.dataset.path=card.dataset.path;const img=card.querySelector('.media-card-preview img');row.innerHTML=`<span class="playlist-grip">⠿</span><span class="playlist-index"></span><span class="playlist-thumb">${img?`<img src="${img.src}" alt="">`:'▶'}</span><span class="playlist-details"><strong></strong><small></small></span><span class="playlist-controls"><button type="button" data-move="-1">↑</button><button type="button" data-move="1">↓</button><button type="button" data-remove-playlist>×</button></span>`;row.querySelector('strong').textContent=card.dataset.title;row.querySelector('small').textContent=`${card.dataset.type} · ${card.dataset.size}`;list.appendChild(row);syncV97();}
 function syncV97(){const rows=[...(list?.querySelectorAll('.playlist-item')||[])];rows.forEach((r,i)=>r.querySelector('.playlist-index').textContent=i+1);const value=rows.map(r=>r.dataset.path).join('\n');['playlist-order-field','sync-playlist-order-field'].forEach(id=>{const e=document.getElementById(id);if(e)e.value=value;});list?.classList.toggle('is-empty',rows.length===0);}
 grid?.addEventListener('click',e=>{const btn=e.target.closest('[data-select-media]');if(!btn)return;e.stopPropagation();const card=btn.closest('[data-media-item]');picked.has(card.dataset.path)?picked.delete(card.dataset.path):picked.add(card.dataset.path);updatePicked();});
 grid?.addEventListener('dblclick',e=>{const card=e.target.closest('[data-media-item]');if(card&&card.dataset.supported==='true'&&card.dataset.kind!=='folder')addCard(card);});
 grid?.addEventListener('dragstart',e=>{const card=e.target.closest('[data-media-item]');if(card&&card.dataset.supported==='true'&&card.dataset.kind!=='folder'){e.dataTransfer.setData('text/media-path',card.dataset.path);e.dataTransfer.effectAllowed='copy';}});
 ws.querySelector('[data-add-selected-media]')?.addEventListener('click',()=>{mediaCards().filter(c=>picked.has(c.dataset.path)).forEach(addCard);picked.clear();updatePicked();list?.scrollIntoView({behavior:'smooth',block:'center'});});
 ws.querySelector('[data-clear-media-selection]')?.addEventListener('click',()=>{picked.clear();updatePicked();});
 list?.addEventListener('dragover',e=>{e.preventDefault();if(!e.target.closest('.playlist-item'))list.classList.add('is-drop-target');});list?.addEventListener('dragleave',()=>list.classList.remove('is-drop-target'));list?.addEventListener('drop',e=>{const path=e.dataTransfer.getData('text/media-path');if(path){e.preventDefault();const card=mediaCards().find(c=>c.dataset.path===path);if(card)addCard(card);}list.classList.remove('is-drop-target');});
 list?.addEventListener('click',e=>{const b=e.target.closest('[data-remove-playlist]');if(b){b.closest('.playlist-item').remove();syncV97();}});
 const observer=new MutationObserver(syncV97);if(list)observer.observe(list,{childList:true});updatePicked();syncV97();
})();
