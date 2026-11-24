"""SQLite backup + legacy schema verification + migration. Never drops user records."""
import argparse
from contextlib import closing
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, inspect
from config import DATABASE_URL, BACKEND_DIR

ROOT = BACKEND_DIR.parent

def alembic(url, *args):
    env = dict(os.environ, DATABASE_URL=url)
    subprocess.run([sys.executable, '-m', 'alembic', '-c', str(ROOT/'alembic.ini'), *args], cwd=ROOT, env=env, check=True)


def upgrade_sqlite(path):
    path = path.resolve()
    if not path.is_file():
        raise ValueError('Existing database file required.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    backups = path.parent/'backups'
    backups.mkdir(exist_ok=True)
    backup = backups/f'{path.stem}-{stamp}.db'
    with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as target:
        source.backup(target)
    with tempfile.TemporaryDirectory(prefix='politiads_upgrade_') as tmp:
        trial = Path(tmp)/'trial.db'
        with closing(sqlite3.connect(backup)) as source, closing(sqlite3.connect(trial)) as target:
            source.backup(target)
        with closing(sqlite3.connect(trial)) as connection:
            versioned = connection.execute("SELECT count(*) FROM sqlite_master WHERE name='alembic_version'").fetchone()[0]
        if not versioned:
            # Build frozen baseline and verify required columns/types, unique indexes and FKs.
            baseline = Path(tmp)/'baseline.db'
            alembic('sqlite:///'+baseline.as_posix(), 'upgrade', '2a808ca65829')
            actual_engine = create_engine('sqlite:///'+trial.as_posix())
            baseline_engine = create_engine('sqlite:///'+baseline.as_posix())
            actual, expected = inspect(actual_engine), inspect(baseline_engine)
            try:
                for table in expected.get_table_names():
                    if table == 'alembic_version': continue
                    if table not in actual.get_table_names(): raise ValueError(f'Legacy baseline missing table: {table}')
                    columns = {c['name']: c for c in actual.get_columns(table)}
                    for col in expected.get_columns(table):
                        if col['name'] not in columns or columns[col['name']]['type']._type_affinity != col['type']._type_affinity:
                            raise ValueError(f'Legacy schema mismatch: {table}.{col["name"]}')
                    for idx in expected.get_indexes(table):
                        if idx.get('unique') and not any(x.get('unique') and x['column_names']==idx['column_names'] for x in actual.get_indexes(table)):
                            raise ValueError(f'Missing unique index: {table}.{idx["name"]}')
                # No unvalidated stamping of arbitrary schemas.
            finally:
                actual_engine.dispose(); baseline_engine.dispose()
            alembic('sqlite:///'+trial.as_posix(), 'stamp', '2a808ca65829')
        alembic('sqlite:///'+trial.as_posix(), 'upgrade', 'head')
        alembic('sqlite:///'+trial.as_posix(), 'check')
        with closing(sqlite3.connect(trial)) as connection:
            if connection.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Foreign-key violations in trial upgrade; original preserved.')
        # Upgrade original only after copy succeeds, retaining its verified backup.
        if not versioned: alembic('sqlite:///'+path.as_posix(), 'stamp', '2a808ca65829')
        alembic('sqlite:///'+path.as_posix(), 'upgrade', 'head')
    print('Upgrade successful. Backup:', backup)
    return backup

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--existing-sqlite', type=Path)
    args = parser.parse_args()
    if args.existing_sqlite:
        upgrade_sqlite(args.existing_sqlite)
    else:
        alembic(DATABASE_URL, 'upgrade', 'head')
