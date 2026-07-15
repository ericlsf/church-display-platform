from pathlib import Path
import importlib.util


SCRIPT = Path(__file__).with_name("verify-backup-restore.py")
SPEC = importlib.util.spec_from_file_location(
    "verify_backup_restore_impl",
    SCRIPT,
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

sha256 = MODULE.sha256
snapshot_sqlite = MODULE.snapshot_sqlite
snapshot_file = MODULE.snapshot_file
safe_extract = MODULE.safe_extract
main = MODULE.main
