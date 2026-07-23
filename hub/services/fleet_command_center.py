from services.alert_center_state import build_alert_center_state
from services.fleet_operations import fleet_rows
from services.fleet_truth import enrich_fleet_rows
from services.jobs import list_jobs

ACTIVE_STATES={"queued","pending","running","retrying","in_progress"}

def _action(row):
    did=row.get("id",""); name=row.get("name") or did
    if not (row.get("online") or row.get("status_online")):
        return {"severity":"critical","title":f"{name} is offline","detail":"Check power, networking, or the display agent.","label":"Open diagnostics","url":f"/display/{did}#health-diagnostics"}
    if row.get("update_available"):
        return {"severity":"warning","title":f"{name} has an update available","detail":f'Installed {row.get("version","unknown")}; latest {row.get("latest_tag","available")}.',"label":"Upgrade","url":f"/display/{did}#software-upgrade"}
    sync=str(row.get("sync_state","")).strip().lower()
    if sync not in {"","success","complete","completed","ok"}:
        return {"severity":"warning","title":f"{name} media is out of sync","detail":f"Current sync state: {sync or 'unknown'}.","label":"Review content","url":f"/display/{did}#content-settings"}
    health=int(row.get("health_score",0) or 0)
    if health<100:
        return {"severity":"warning","title":f"{name} health is {health}%","detail":"Review failed checks and quick actions.","label":"Review health","url":f"/display/{did}#health-diagnostics"}
    return None

def build_fleet_command_center():
    rows=enrich_fleet_rows(fleet_rows())
    jobs=list_jobs(1000)
    alerts=build_alert_center_state()
    active=[j for j in jobs if str(j.get("status","")).lower() in ACTIVE_STATES]
    actions=[a for a in (_action(r) for r in rows) if a][:12]
    online=sum(bool(r.get("online") or r.get("status_online")) for r in rows)
    ages=[r.get("heartbeat_age_seconds") for r in rows if isinstance(r.get("heartbeat_age_seconds"),(int,float))]
    return {
        "metrics":{
            "total":len(rows),
            "online":online,
            "offline":len(rows)-online,
            "updating":sum(str(j.get("type","")).lower()=="deploy_update" for j in active),
            "alerts":alerts.get("counts",{}).get("active",alerts.get("counts",{}).get("total",0)),
            "upgrades":sum(bool(r.get("update_available")) for r in rows),
            "freshest_heartbeat_seconds":min(ages) if ages else None,
        },
        "actions":actions,
        "displays":rows,
        "active_jobs":active[:20],
    }
