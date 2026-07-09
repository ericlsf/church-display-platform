from services.schedules import process_due_schedules

queued = process_due_schedules()
print(f"Queued {len(queued)} due scheduled job(s).")
