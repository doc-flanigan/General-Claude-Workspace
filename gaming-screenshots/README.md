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
- `ATTRIBUTION.md` — required credit text
- `manifest.json` — generated; metadata for every scraped image
- `images/` — generated; downloaded files, organized by game folder

## Setup

```bash
cd gaming-screenshots
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

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

This walks `?page_number_0=1..N` (currently 32 pages, ~1,500 images) and
records every image's full-resolution URL, alt text, title, and the game
folder parsed from the URL.

### Crawl a single tag (server-side filter via the gallery's AJAX endpoint)

```bash
python scrape_hasgaha.py crawl --tag "Cyberpunk 2077"
python scrape_hasgaha.py crawl --tag-id 74          # "favorite"
python scrape_hasgaha.py crawl --tag-id 31          # "4k"
```

`--tag` is matched against `tags.json` (exact, then unique substring).
`--tag-id` skips the lookup. The script POSTs to the BWG plugin's
`bwg_frontend_data` action with the chosen tag ID and walks pagination from
the server's response.

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
then pulls full-resolution files into `images/<game>/<filename>`:

```bash
# Download everything in the manifest (~1500 files, several GB)
python scrape_hasgaha.py download --skip-filter

# Just RDR2
python scrape_hasgaha.py download --game RDR2

# Just images tagged "favorite" via the site's tag system
python scrape_hasgaha.py download --tag-id 74

# Test with 5 files first
python scrape_hasgaha.py download --tag "Cyberpunk 2077" --limit 5

# Force a fresh crawl before downloading
python scrape_hasgaha.py download --tag "SC Carrack" --refresh
```

Re-running the download skips files that already exist; pass `--overwrite` to
force re-download.

## Notes on the two filter modes

The site uses the WordPress "Photo Gallery" plugin (BWG). It exposes two
viable scraping paths:

1. **Server-rendered pagination** (`?page_number_0=N`) — reliable; returns
   plain HTML you can parse. Used by the default `crawl` and by
   `--client-filter`.
2. **AJAX tag filter** (POST to `wp-admin/admin-ajax.php?action=bwg_frontend_data`
   with a tag ID) — used by `crawl --tag-id N`. Faithful to the site's tag
   taxonomy but more fragile, since it depends on the plugin's internal form
   schema. If the AJAX response shape changes, fall back to client-side
   filtering.

Most game-level questions ("just download Cyberpunk shots") are equally well
served by either mode, since the game name shows up in both the URL path and
the alt text. Tags like `favorite`, `4k`, `Black and White`, or fine-grained
SC ship variants only exist in the server-side tag system, so use
`--tag-id` for those.

## Be polite

The script defaults to a 0.5s delay between requests and retries with
exponential backoff on 5xx / network errors. Bump `--delay` higher if you're
doing a full crawl.
