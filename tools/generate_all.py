"""Master script: generate all synthetic data and populate the database.

Usage:
    python -m tools.generate_all          # from repo root
    python tools/generate_all.py          # direct

This replaces the demo seed data with production-grade synthetic data:
  1. Generates 30 patients across 3 villages
  2. Generates realistic observation histories
  3. Generates sample EHR text files
  4. Populates the SQLite database
  5. Runs risk/schedule/ration engines

To reset, delete data/demo.db and re-run this script.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def main():
    print("=" * 60)
    print("  ASHA Sahayak — Synthetic Data Generation Pipeline")
    print("=" * 60)

    # Step 1: Generate synthetic JSON data files
    print("\n[1/3] Generating synthetic patient & observation data...")
    from tools.generate_synthetic_data import generate_all as gen_data
    gen_data()

    # Step 2: Generate sample EHR text files
    print("\n[2/3] Generating sample EHR report files...")
    from tools.generate_sample_ehrs import generate_all as gen_ehrs
    gen_ehrs()

    # Step 3: Delete old DB and populate fresh
    print("\n[3/3] Populating database...")
    db_path = ROOT / "data" / "demo.db"
    for suffix in ("", "-shm", "-wal"):
        p = Path(str(db_path) + suffix)
        if p.exists():
            p.unlink()
    if not db_path.exists():
        print(f"  Cleared old database files")

    from tools.populate_production_db import populate_all
    populate_all()

    print("\n" + "=" * 60)
    print("  All synthetic data generated and loaded.")
    print("  Start the app:  python app/main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
