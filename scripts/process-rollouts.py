#!/usr/bin/env python3
from services.rollouts import process_rollouts

data = process_rollouts()
print(f"Processed {len(data.get('rollouts', []))} rollout(s).")
