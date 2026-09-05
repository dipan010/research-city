"""Inject the exported data into the page template.

web/template.html is the source you edit; docs/index.html is generated and is
what GitHub Pages serves. Keeping them separate means a re-run of the pipeline
actually updates the page instead of silently leaving stale numbers in it.

Output goes to the REPOSITORY's docs/ directory, not this project's - GitHub
Pages serves a project site only from the repo root or the repo's /docs, never
from a nested folder. Each project gets its own subdirectory under docs/.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent                      # research-city/ - the Pages root
TPL = ROOT / "web" / "template.html"
DEST = REPO / "docs" / ROOT.name / "index.html"
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
    DEST.parent.mkdir(parents=True, exist_ok=True)
    # .nojekyll stops Pages running the file through Jekyll, which would
    # otherwise mangle anything it mistakes for a template.
    (REPO / "docs" / ".nojekyll").write_text("")
    DEST.write_text(tpl.replace(PLACEHOLDER, payload), encoding="utf-8")
    print(f"{DEST}  {DEST.stat().st_size/1024:.0f} KB "
          f"({len(payload)/1024:.0f} KB data, "
          f"{len(json.loads(payload)['wards'])} wards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
