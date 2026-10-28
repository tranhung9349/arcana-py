"""Write a consistent SQLite backup to stdout for Docker exec redirection.

Use: docker compose exec -T app python /app/deploy/backup.py > backup.sqlite3
Status goes to stderr; stdout contains only the database bytes.
"""
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile


def main():
    source_path = Path(os.environ["RANDOMYST_DATABASE"])
    with tempfile.TemporaryDirectory(prefix="arcana-backup-") as directory:
        backup_path = Path(directory) / "draws.sqlite3"
        with sqlite3.connect(source_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=30) as source:
            with sqlite3.connect(backup_path) as destination:
                source.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("SQLite backup integrity check failed")
        with backup_path.open("rb") as stream:
            shutil.copyfileobj(stream, sys.stdout.buffer)
    print("Arcana backup completed.", file=sys.stderr)


if __name__ == "__main__":
    main()
