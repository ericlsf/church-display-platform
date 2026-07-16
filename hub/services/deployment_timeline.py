from services.deployment_verification import deployment_verification_state

STAGES = [
    ("queued","Queued"),
    ("downloading","Downloading package"),
    ("verifying","Verifying checksum"),
    ("installing","Installing software"),
    ("restarting","Restarting services"),
    ("waiting_heartbeat","Waiting for heartbeat"),
    ("verified","Version verified"),
]

def deployment_timeline(display_id):
    verification = deployment_verification_state(display_id)
    job = verification.get("job") or {}
    status = str(job.get("status","")).lower()
    progress = int(job.get("progress",0) or 0)

    if verification.get("state") == "verified":
        current = "verified"
    elif verification.get("state") == "verification_failed":
        current = "waiting_heartbeat"
    elif status in {"failed","cancelled","timed_out"}:
        current = "failed"
    elif status in {"success","succeeded","complete","completed"}:
        current = "waiting_heartbeat"
    elif progress < 20:
        current = "queued"
    elif progress < 45:
        current = "downloading"
    elif progress < 55:
        current = "verifying"
    elif progress < 80:
        current = "installing"
    else:
        current = "restarting"

    current_index = next((i for i,(key,_) in enumerate(STAGES) if key == current), -1)
    stages = []
    for i,(key,label) in enumerate(STAGES):
        state = "complete" if current == "verified" or i < current_index else "active" if i == current_index else "pending"
        stages.append({"key":key,"label":label,"state":state})
    return {"current_stage":current,"stages":stages,"verification":verification,"job":job}
