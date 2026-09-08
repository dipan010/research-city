"""Inject the exported data into the page template and copy the figures.

web/template.html is the source you edit; docs/<project>/index.html is
generated and is what GitHub Pages serves. Keeping them separate means a re-run
of the pipeline updates the page instead of leaving stale numbers in it.

Output goes to the REPOSITORY's docs/ directory, not this project's - Pages
serves a project site from the repo root or the repo's /docs, never from a
nested folder. Each project gets its own subdirectory.
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent                      # research-city/ - the Pages root
TPL = ROOT / "web" / "template.html"
FIGS = ROOT / "figures"
DEST_DIR = REPO / "docs" / ROOT.name
DEST = DEST_DIR / "index.html"
DATA = ROOT / "data" / "out" / "web_data.json"

PLACEHOLDER = "__DATA__"


def main() -> int:
    if not DATA.exists():
        raise SystemExit(f"missing {DATA} - run src/export_web.py first")
    tpl = TPL.read_text(encoding="utf-8")
    if tpl.count(PLACEHOLDER) != 1:
        raise SystemExit(
            f"expected exactly one {PLACEHOLDER} in {TPL}, "
            f"found {tpl.count(PLACEHOLDER)}")

    payload = json.dumps(json.loads(DATA.read_text()), separators=(",", ":"))
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    # .nojekyll stops Pages running files through Jekyll, which would mangle
    # anything it mistakes for a template.
    (REPO / "docs" / ".nojekyll").write_text("")
    DEST.write_text(tpl.replace(PLACEHOLDER, payload), encoding="utf-8")

    copied = 0
    for png in sorted(FIGS.glob("*.png")):
        shutil.copy2(png, DEST_DIR / png.name)
        copied += 1

    data = json.loads(payload)
    print(f"{DEST}  {DEST.stat().st_size / 1024:.0f} KB "
          f"({len(payload) / 1024:.0f} KB data, {len(data['wards'])} wards, "
          f"{len(data['points'])} water bodies)")
    print(f"{copied} figures -> {DEST_DIR}")

    # Every <img src> the page references must have landed next to it.
    import re
    missing = [m for m in re.findall(r'<img src="([^"]+)"', tpl)
               if not (DEST_DIR / m).exists()]
    if missing:
        raise SystemExit(f"page references missing images: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
