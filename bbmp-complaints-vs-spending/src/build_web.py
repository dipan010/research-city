"""Inject the exported data into the page template.

web/template.html is the source you edit; web/index.html is generated and is
what gets published. Keeping them separate means a re-run of the pipeline
actually updates the page instead of silently leaving stale numbers in it.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TPL = ROOT / "web" / "template.html"
DEST = ROOT / "web" / "index.html"
DATA = ROOT / "data" / "out" / "web_data.json"

PLACEHOLDER = "__DATA__"


def main() -> int:
    if not DATA.exists():
        raise SystemExit(f"missing {DATA} - run src/export_web.py first")
    tpl = TPL.read_text()
    if tpl.count(PLACEHOLDER) != 1:
        raise SystemExit(
            f"expected exactly one {PLACEHOLDER} in {TPL}, "
            f"found {tpl.count(PLACEHOLDER)}")
    payload = json.dumps(json.loads(DATA.read_text()), separators=(",", ":"))
    DEST.write_text(tpl.replace(PLACEHOLDER, payload))
    print(f"{DEST}  {DEST.stat().st_size/1024:.0f} KB "
          f"({len(payload)/1024:.0f} KB data, "
          f"{len(json.loads(payload)['wards'])} wards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
