# gaming-screenshots

Tooling to scrape and download Hasgaha's gaming screenshots from
<https://www.hasgaha.com/gaming-screenshots/>, with optional filtering by the
gallery's tags.

The site owner permits download/use with credit and a link back. See
[ATTRIBUTION.md](./ATTRIBUTION.md) — keep that file alongside any images you
use or redistribute.

## What's here

- `scrape_hasgaha.py` — the scraper (crawl, download, list-tags)
- `tags.json` — full ID ↔ name mapping for the gallery's ~230 tags
- `requirements.txt` — Python deps (`requests`, `beautifulsoup4`)
- `setup.sh` — one-shot venv + deps for macOS / Linux
- `ATTRIBUTION.md` — required credit text
- `manifest.json` — generated; metadata for every scraped image
- `images/` — generated; downloaded files, organized by game folder

## Setup (macOS)

macOS ships with `python3` (10.15+). One command:

```bash
cd gaming-screenshots
bash setup.sh
source .venv/bin/activate
```

If you don't have `python3`, install it via [python.org](https://www.python.org/downloads/macos/)
or `brew install python`.

## The headline recipe

Download every Star Citizen image (the master `Star Citizen` tag plus every
tag whose name starts with `SC`):

```bash
python scrape_hasgaha.py download --tag "Star Citizen" --tag-prefix "SC"
```

That single invocation:
1. Crawls the gallery (or reuses an existing `manifest.json`).
2. Selects the `Star Citizen` tag (id=2) **plus all 210 `SC ...` tags**
   (ships, stations, alpha versions, IAE day-by-day, etc.).
3. Filters with **OR** semantics — an image kept if it matches **any** of the
   selected tags.
4. Writes manifest metadata for everything kept.
5. Downloads full-res files to `images/<game>/<filename>`, skipping anything
   already on disk.

The prefix match is case-sensitive, so it picks up `SC ...` but not the
unrelated lowercase tags `screenshot` / `science fiction`.

## Other usage

### List tags

```bash
python scrape_hasgaha.py list-tags
python scrape_hasgaha.py list-tags cyberpunk
python scrape_hasgaha.py list-tags "SC Aegis"
```

### Crawl the whole gallery (writes `manifest.json`)

```bash
python scrape_hasgaha.py crawl
```

Walks `?page_number_0=1..N` (~32 pages, ~1,500 images) and records every
image's full-resolution URL, alt text, title, and game folder.

### Crawl with tag filters (server-side via the gallery's AJAX endpoint)

```bash
python scrape_hasgaha.py crawl --tag "Cyberpunk 2077"
python scrape_hasgaha.py crawl --tag-id 74              # "favorite"
python scrape_hasgaha.py crawl --tag "Star Citizen" --tag-prefix "SC"
python scrape_hasgaha.py crawl --tag "Hob,Limbo,ABZU"   # comma-separated
```

`--tag` and `--tag-id` are repeatable (and accept comma-separated values).
`--tag-prefix` is repeatable too. Multiple selections are OR'd in a single
AJAX request.

### Crawl everything and filter client-side (no AJAX)

Useful if the AJAX endpoint changes or you want to combine filters:

```bash
python scrape_hasgaha.py crawl --tag "Carrack" --client-filter
python scrape_hasgaha.py crawl --game RDR2
python scrape_hasgaha.py crawl --game Star_Citizen --alt-contains "Yela"
```

Client-side filters match against alt text, title, and URL path.

### Download images

`download` re-uses an existing `manifest.json` (or crawls first), filters,
then pulls files into `images/<game>/<filename>`:

```bash
python scrape_hasgaha.py download --skip-filter                       # everything (~1500 files, several GB)
python scrape_hasgaha.py download --game RDR2                         # one game
python scrape_hasgaha.py download --tag-id 74                         # "favorite"
python scrape_hasgaha.py download --tag "Cyberpunk 2077" --limit 5    # smoke test
python scrape_hasgaha.py download --tag "SC Carrack" --refresh        # re-crawl first
```

Re-running skips files that already exist; pass `--overwrite` to force
re-download.

## Notes on the two filter modes

The site uses the WordPress "Photo Gallery" plugin (BWG). Two viable paths:

1. **Server-rendered pagination** (`?page_number_0=N`) — reliable, plain HTML.
   Used by the default `crawl` and by `--client-filter`.
2. **AJAX tag filter** (POST to `wp-admin/admin-ajax.php?action=bwg_frontend_data`)
   — used when any of `--tag` / `--tag-id` / `--tag-prefix` is given. Faithful
   to the site's tag taxonomy. If the AJAX response shape ever changes, fall
   back to `--client-filter`.

Most game-level questions are equally well served by either mode (the game
name shows up in both URL and alt text). Tags like `favorite`, `4k`,
`Black and White`, or fine-grained SC ship variants only exist in the
server-side tag system, so use `--tag` / `--tag-id` / `--tag-prefix` for
those.

## Be polite

Defaults: 0.5s delay between requests, exponential-backoff retries on 5xx /
network errors, real User-Agent. Bump `--delay` higher for full crawls.
