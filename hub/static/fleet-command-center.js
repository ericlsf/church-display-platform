(() => {
  const page=document.querySelector("[data-command-center]");
  if(!page)return;
  const drawer=page.querySelector("[data-job-drawer-panel]");
  page.querySelector("[data-job-drawer-toggle]")?.addEventListener("click",()=>{drawer.hidden=!drawer.hidden});
  page.querySelector("[data-job-drawer-close]")?.addEventListener("click",()=>{drawer.hidden=true});
  const esc=v=>String(v??"").replace(/[&<>"']/g,"");
  const refresh=async()=>{
    try{
      const r=await fetch("/command-center/state",{credentials:"same-origin",cache:"no-store"});
      if(!r.ok)return;
      const d=await r.json();
      const map={online:d.metrics.online,updating:d.metrics.updating,offline:d.metrics.offline,alerts:d.metrics.alerts,upgrades:d.metrics.upgrades,freshest:d.metrics.freshest_heartbeat_seconds==null?"Unknown":`${d.metrics.freshest_heartbeat_seconds}s`};
      Object.entries(map).forEach(([k,v])=>{const t=page.querySelector(`[data-metric="${k}"]`);if(t)t.textContent=String(v)});
      const actions=page.querySelector("[data-recommended-actions]");
      const actionCount=page.querySelector("[data-action-count]");
      if(actionCount)actionCount.textContent=String((d.actions||[]).length);
      if(actions)actions.innerHTML=(d.actions||[]).length?(d.actions||[]).map(a=>`<article class="recommended-action ${esc(a.severity)}"><div><strong>${esc(a.title)}</strong><p>${esc(a.detail)}</p></div><a class="button" href="${esc(a.url)}">${esc(a.label)}</a></article>`).join(""):'<div class="empty-state">No immediate fleet actions are required.</div>';
      const jobs=page.querySelector("[data-job-list]");
      const jobCount=page.querySelector("[data-job-count]");
      if(jobCount)jobCount.textContent=String((d.active_jobs||[]).length);
      if(jobs)jobs.innerHTML=(d.active_jobs||[]).length?(d.active_jobs||[]).map(j=>`<article class="job-drawer-row"><strong>${esc(j.display_id)}</strong><span>${esc(j.type)}</span><progress max="100" value="${Number(j.progress||0)}"></progress><small>${esc(j.message||j.status)}</small></article>`).join(""):'<div class="empty-state">No active jobs.</div>';
    }catch(_){}
  };
  page.querySelector("[data-refresh-command-center]")?.addEventListener("click",refresh);
  setInterval(refresh,5000);
})();