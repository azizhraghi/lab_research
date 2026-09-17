"""Consistent local SQLite snapshots. Never overwrites an existing destination."""
import argparse
import json
from pathlib import Path
import sqlite3
from contextlib import closing

def snapshot(source, destination):
    source=Path(source).resolve(); destination=Path(destination).resolve()
    if source==destination: raise ValueError('Source and destination must differ')
    if not source.is_file(): raise ValueError('Source database does not exist')
    destination.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation prevents accidental replacement of existing records.
    with destination.open('xb'): pass
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('Snapshot failed SQLite integrity verification')
        tables=[r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        counts={name:dst.execute('SELECT count(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in tables}
    return dict(destination=str(destination),integrity='ok',table_counts=counts)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source');parser.add_argument('destination')
    args=parser.parse_args()
    print(json.dumps(snapshot(args.source,args.destination),indent=2))
if __name__=='__main__':main()
