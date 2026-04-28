# General-Claude-Workspace

General workspace for Claude to maintain records of general questions and
prompts for the sc-portfolio.

---

## Branch: `claude/scrape-gaming-screenshots-xaSov`

This branch adds [`gaming-screenshots/`](./gaming-screenshots/) — a
self-contained Python tool that scrapes and downloads gaming screenshots
from <https://www.hasgaha.com/gaming-screenshots/>.

### What the script does

`gaming-screenshots/scrape_hasgaha.py` is a CLI with three subcommands:

- **`crawl`** — walks the gallery's paginated HTML (or hits its WordPress
  AJAX endpoint when a tag filter is given), parses every image's
  full-resolution URL, alt text, title, and game folder, and writes
  `manifest.json`.
- **`download`** — applies tag/game filters and pulls full-res files into
  `gaming-screenshots/images/<game>/<filename>`. Re-running skips files
  already on disk.
- **`list-tags`** — prints the ~230 tag names ↔ IDs the gallery exposes.

Filtering supports the gallery's full tag taxonomy via three repeatable
flags: `--tag NAME`, `--tag-id N`, and `--tag-prefix PREFIX` (all OR'd).
Example:

```bash
# Every Star Citizen screenshot: master tag + all 210 "SC ..." sub-tags
python scrape_hasgaha.py download --tag "Star Citizen" --tag-prefix "SC"
```

See [`gaming-screenshots/README.md`](./gaming-screenshots/README.md) for the
full usage guide and macOS setup.

### Credit reminder — important

All screenshots are by **Hasgaha** (<https://hasgaha.com>). The site owner
permits downloading and reuse, **but requires credit and a link back to
hasgaha.com whenever an image appears in any public project** (video,
graphic, artwork, tattoo, interpretive dance, skywriting — their words).

If you reuse any of the images this script downloads, credit:

> Screenshot by Hasgaha — <https://hasgaha.com>

The full terms (verbatim from the site) are preserved in
[`gaming-screenshots/ATTRIBUTION.md`](./gaming-screenshots/ATTRIBUTION.md),
and the generated `manifest.json` records the original source URL of every
image so per-file attribution can be reconstructed at any time.
