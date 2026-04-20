#!/usr/bin/env python3
"""
Master pipeline: Run all extraction phases in sequence.

Phase 1: Environment setup (manual, or via setup script)
Phase 2: Extract LifeTech member directory
Phase 3: Fetch member websites
Phase 4: Three-stage data extraction (BeautifulSoup + Mistral + FireCrawl)
Phase 5: SQLite logging (automatic in each phase)
Phase 6: Export to GeoJSON
Phase 7: Generate map (manual open of map.html)
Phase 8: Model comparison report
"""

import sys
import subprocess
from pathlib import Path

def run_phase(phase_num: int, script_name: str, description: str) -> bool:
    """Run a single phase."""
    print(f"\n{'='*70}")
    print(f"PHASE {phase_num}: {description}")
    print(f"{'='*70}")

    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            cwd=Path(__file__).parent.parent
        )
        print(f"\n✅ Phase {phase_num} completed successfully!")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Phase {phase_num} failed with return code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Phase {phase_num} failed: {e}")
        return False


def main():
    """Run full pipeline."""
    print("LifeTech Member Extraction Pipeline - Full Run")
    print("=" * 70)

    phases = [
        (2, "extract_lifetech_members.py", "Extract LifeTech Members Directory"),
        (3, "fetch_member_websites.py", "Fetch Member Websites"),
        (4, "extract_company_data.py", "Three-Stage Data Extraction"),
        (6, "export_for_map.py", "Export to GeoJSON for Map"),
    ]

    results = {}
    for phase_num, script, description in phases:
        results[phase_num] = run_phase(phase_num, script, description)
        if not results[phase_num]:
            print(f"\n⚠️  Phase {phase_num} failed. Continue anyway? (y/n)")
            # In non-interactive mode, continue
            continue

    # Summary
    print(f"\n{'='*70}")
    print("PIPELINE SUMMARY")
    print(f"{'='*70}")

    for phase_num in sorted(results.keys()):
        status = "✅ OK" if results[phase_num] else "❌ FAILED"
        print(f"Phase {phase_num}: {status}")

    # Final messages
    print("\n" + "=" * 70)
    print("Next steps:")
    print("1. Review output files in lifetech.brussels/")
    print("2. Open map.html in browser to view member map")
    print("3. Check members_enhanced.toml for extracted data")
    print("4. Review quality issues in extraction_log.db")
    print("=" * 70)

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
