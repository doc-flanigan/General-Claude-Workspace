#!/usr/bin/env python3
"""
Scrape gaming screenshots from https://www.hasgaha.com/gaming-screenshots/.

Usage:
    python scrape_hasgaha.py crawl
    python scrape_hasgaha.py crawl --tag "Star Citizen"
    python scrape_hasgaha.py crawl --tag-id 74
    python scrape_hasgaha.py download --tag "Cyberpunk 2077"
    python scrape_hasgaha.py download --game RDR2 --limit 10

    # The "Star Citizen + every SC-prefixed tag" recipe:
    python scrape_hasgaha.py download --tag "Star Citizen" --tag-prefix "SC"

Permission: site owner permits download/use with credit + link back to hasgaha.com.
See ATTRIBUTION.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.hasgaha.com/gaming-screenshots/"
AJAX_URL = "https://www.hasgaha.com/wp-admin/admin-ajax.php"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

GALLERY_FORM_DEFAULTS = {
    "shortcode_id": "272",
    "gallery_type": "thumbnails_mosaic",
    "gallery_id": "0",
    "album_gallery_id": "0",
    "default_tag": "3",
    "theme_id": "2",
    "type": "album",
    "current_url": "/gaming-screenshots/",
    "current_view": "0",
    "block_id": "bwg_thumbnails_mosaic_0",
}

HERE = Path(__file__).resolve().parent
TAGS_FILE = HERE / "tags.json"
MANIFEST_DEFAULT = HERE / "manifest.json"
IMAGES_DIR_DEFAULT = HERE / "images"


@dataclass
class GalleryImage:
    image_id: str
    full_url: str
    thumb_url: str
    alt: str
    title: str
    width: float | None
    height: float | None
    game: str
    page: int

    @property
    def filename(self) -> str:
        return Path(unquote(urlparse(self.full_url).path)).name


def load_tags() -> dict[str, int]:
    return json.loads(TAGS_FILE.read_text())["tags"]


def _split_csv(values: list[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for v in values:
        out.extend(p.strip() for p in v.split(",") if p.strip())
    return out


def resolve_one_tag(tag: str, tags: dict[str, int]) -> int:
    if tag in tags:
        return tags[tag]
    if tag.isdigit():
        return int(tag)
    matches = [name for name in tags if tag.lower() in name.lower()]
    if len(matches) == 1:
        print(f"Resolved --tag {tag!r} -> {matches[0]!r} (id={tags[matches[0]]})")
        return tags[matches[0]]
    if not matches:
        sys.exit(f"No tag matches {tag!r}. See tags.json for the full list.")
    sys.exit(
        f"Tag {tag!r} is ambiguous. Matches:\n  "
        + "\n  ".join(f"{tags[m]:>4}  {m}" for m in matches[:25])
        + "\nUse --tag-id N for an exact match, or pass the full tag name."
    )


def resolve_tag_ids(
    tag: list[str] | None,
    tag_id: list[str] | None,
    tag_prefix: list[str] | None,
    tags: dict[str, int],
) -> list[tuple[int, str]]:
    """Returns a list of (id, name) tuples covering every tag selected by the
    user. Names are unique; the order matches the order specified."""
    name_for_id = {v: k for k, v in tags.items()}
    out: dict[int, str] = {}

    for raw_id in _split_csv(tag_id):
        try:
            tid = int(raw_id)
        except ValueError:
            sys.exit(f"Invalid --tag-id value: {raw_id!r}")
        out.setdefault(tid, name_for_id.get(tid, f"id={tid}"))

    for t in _split_csv(tag):
        tid = resolve_one_tag(t, tags)
        out.setdefault(tid, name_for_id.get(tid, t))

    for prefix in _split_csv(tag_prefix):
        matches = [(tid, name) for name, tid in tags.items() if name.startswith(prefix)]
        if not matches:
            sys.exit(f"No tags start with {prefix!r}.")
        print(f"--tag-prefix {prefix!r} matched {len(matches)} tag(s)")
        for tid, name in matches:
            out.setdefault(tid, name)

    return list(out.items())


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    return s


def get_with_retry(session: requests.Session, url: str, **kwargs) -> requests.Response:
    last_exc: Exception | None = None
    for delay in (0, 2, 4, 8):
        if delay:
            time.sleep(delay)
        try:
            r = session.get(url, timeout=30, **kwargs)
            if r.status_code == 200:
                return r
            if 500 <= r.status_code < 600:
                last_exc = requests.HTTPError(f"{r.status_code} on {url}")
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            last_exc = e
    raise RuntimeError(f"Failed to GET {url}: {last_exc}")


def post_with_retry(session: requests.Session, url: str, data, **kwargs) -> requests.Response:
    last_exc: Exception | None = None
    for delay in (0, 2, 4, 8):
        if delay:
            time.sleep(delay)
        try:
            r = session.post(url, data=data, timeout=30, **kwargs)
            if r.status_code == 200:
                return r
            if 500 <= r.status_code < 600:
                last_exc = requests.HTTPError(f"{r.status_code} on {url}")
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            last_exc = e
    raise RuntimeError(f"Failed to POST {url}: {last_exc}")


GAME_PATH_RE = re.compile(r"/photo-gallery/([^/]+)/")


def parse_gallery_html(html: str, page: int) -> tuple[list[GalleryImage], int]:
    soup = BeautifulSoup(html, "html.parser")
    images: list[GalleryImage] = []
    for a in soup.select("a.bwg_lightbox"):
        href = a.get("href", "").split("?", 1)[0]
        img = a.find("img")
        if not href or not img:
            continue
        thumb = (img.get("data-src") or img.get("src") or "").split("?", 1)[0]
        m = GAME_PATH_RE.search(href)
        game = m.group(1) if m else "unknown"

        def _to_float(v):
            try:
                return float(v) if v is not None else None
            except ValueError:
                return None

        images.append(
            GalleryImage(
                image_id=str(a.get("data-image-id") or img.get("id") or ""),
                full_url=href,
                thumb_url=thumb,
                alt=img.get("alt", ""),
                title=img.get("title", ""),
                width=_to_float(img.get("data-width")),
                height=_to_float(img.get("data-height")),
                game=game,
                page=page,
            )
        )

    pages_count = 1
    el = soup.select_one(".pagination-links")
    if el and el.get("data-pages-count"):
        try:
            pages_count = int(el["data-pages-count"])
        except ValueError:
            pass
    if pages_count == 1:
        total_el = soup.select_one(".total-pages_0")
        if total_el and total_el.text.strip().isdigit():
            pages_count = int(total_el.text.strip())
    return images, pages_count


def crawl_paginated(
    session: requests.Session,
    *,
    delay: float,
    max_pages: int | None,
) -> list[GalleryImage]:
    print(f"Fetching page 1 of (unknown) ...")
    r = get_with_retry(session, BASE_URL, params={"page_number_0": 1})
    images, pages_count = parse_gallery_html(r.text, page=1)
    print(f"  page 1: {len(images)} images. Total pages: {pages_count}")

    last_page = pages_count if max_pages is None else min(pages_count, max_pages)
    for page in range(2, last_page + 1):
        time.sleep(delay)
        print(f"Fetching page {page} of {last_page} ...")
        r = get_with_retry(session, BASE_URL, params={"page_number_0": page})
        page_images, _ = parse_gallery_html(r.text, page=page)
        print(f"  page {page}: {len(page_images)} images")
        images.extend(page_images)
    return images


def crawl_via_ajax_tags(
    session: requests.Session,
    tag_ids: list[int],
    *,
    delay: float,
    max_pages: int | None,
) -> list[GalleryImage]:
    print(f"Tag-filtered crawl via AJAX (tag_ids={tag_ids})")
    get_with_retry(session, BASE_URL)

    block = GALLERY_FORM_DEFAULTS["block_id"]
    view = GALLERY_FORM_DEFAULTS["current_view"]
    tag_field = f"bwg_tag_id_{block}[]"

    all_images: list[GalleryImage] = []
    page = 1
    while True:
        data: list[tuple[str, str]] = [
            ("action", "bwg_frontend_data"),
            ("shortcode_id", GALLERY_FORM_DEFAULTS["shortcode_id"]),
            ("gallery_type", GALLERY_FORM_DEFAULTS["gallery_type"]),
            ("gallery_id", GALLERY_FORM_DEFAULTS["gallery_id"]),
            ("album_gallery_id", GALLERY_FORM_DEFAULTS["album_gallery_id"]),
            ("tag", GALLERY_FORM_DEFAULTS["default_tag"]),
            ("theme_id", GALLERY_FORM_DEFAULTS["theme_id"]),
            ("type", GALLERY_FORM_DEFAULTS["type"]),
            ("current_view", view),
            ("cur_gal_id", block),
            ("form_id", "gal_front_form_0"),
            (f"bwg_search_{view}", ""),
            (f"page_number_{view}", str(page)),
            ("current_url", GALLERY_FORM_DEFAULTS["current_url"]),
        ]
        for tid in tag_ids:
            data.append((tag_field, str(tid)))
        headers = {
            "Referer": BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
        }
        r = post_with_retry(session, AJAX_URL, data=data, headers=headers)
        try:
            payload = r.json()
            html = (
                payload.get("html")
                or payload.get("data")
                or payload.get("body_html")
                or ""
            )
            pages_count = int(payload.get("pages_count") or payload.get("total_pages") or 0) or None
        except ValueError:
            html = r.text
            pages_count = None

        page_images, parsed_pages = parse_gallery_html(html, page=page)
        if pages_count is None:
            pages_count = parsed_pages
        print(f"  ajax page {page} of {pages_count or '?'}: {len(page_images)} images")

        if not page_images:
            break
        all_images.extend(page_images)

        if pages_count and page >= pages_count:
            break
        if max_pages is not None and page >= max_pages:
            break
        page += 1
        time.sleep(delay)

    return all_images


def filter_images(
    images: list[GalleryImage],
    *,
    tag_substrings: list[str],
    game: str | None,
    alt_contains: str | None,
) -> list[GalleryImage]:
    out = images
    if game:
        g = game.lower()
        out = [i for i in out if g in i.game.lower()]
    if tag_substrings:
        needles = [t.lower() for t in tag_substrings if t]
        out = [
            i for i in out
            if any(
                n in i.alt.lower() or n in i.title.lower() or n in i.full_url.lower()
                for n in needles
            )
        ]
    if alt_contains:
        a = alt_contains.lower()
        out = [i for i in out if a in i.alt.lower()]
    return out


def dedupe_by_id(images: list[GalleryImage]) -> list[GalleryImage]:
    seen: set[str] = set()
    out: list[GalleryImage] = []
    for i in images:
        key = i.image_id or i.full_url
        if key in seen:
            continue
        seen.add(key)
        out.append(i)
    return out


def download_images(
    session: requests.Session,
    images: Iterable[GalleryImage],
    out_dir: Path,
    *,
    delay: float,
    overwrite: bool,
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for img in images:
        game_dir = out_dir / img.game
        game_dir.mkdir(parents=True, exist_ok=True)
        target = game_dir / img.filename
        if target.exists() and not overwrite:
            print(f"  skip (exists): {target.relative_to(out_dir)}")
            continue
        print(f"  downloading: {target.relative_to(out_dir)}")
        try:
            r = get_with_retry(session, img.full_url, stream=True)
        except RuntimeError as e:
            print(f"  ! failed: {e}")
            continue
        with target.open("wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
        count += 1
        time.sleep(delay)
    return count


def write_manifest(images: list[GalleryImage], path: Path, filter_desc: str) -> None:
    payload = {
        "source": BASE_URL,
        "attribution": "Screenshots by Hasgaha (https://hasgaha.com). Use with credit + link back per site terms.",
        "filter": filter_desc,
        "count": len(images),
        "images": [asdict(i) for i in images],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote manifest: {path} ({len(images)} images)")


def cmd_crawl(args: argparse.Namespace) -> None:
    tags = load_tags()
    selected = resolve_tag_ids(args.tag, args.tag_id, args.tag_prefix, tags)
    tag_substrings = _split_csv(args.tag) + [name for _, name in selected]
    session = make_session()

    if selected and not args.client_filter:
        ids = [tid for tid, _ in selected]
        names = [name for _, name in selected]
        print(f"Selected {len(selected)} tag(s): {', '.join(names)}")
        images = crawl_via_ajax_tags(session, ids, delay=args.delay, max_pages=args.max_pages)
        images = dedupe_by_id(images)
        filter_desc = f"server-side tag_ids={ids} ({', '.join(names)})"
    else:
        images = crawl_paginated(session, delay=args.delay, max_pages=args.max_pages)
        if tag_substrings or args.game or args.alt_contains:
            images = filter_images(
                images,
                tag_substrings=tag_substrings,
                game=args.game,
                alt_contains=args.alt_contains,
            )
        filter_desc_parts = []
        if tag_substrings:
            filter_desc_parts.append(f"tag_substrings={tag_substrings}")
        if args.game:
            filter_desc_parts.append(f"game={args.game!r}")
        if args.alt_contains:
            filter_desc_parts.append(f"alt_contains={args.alt_contains!r}")
        filter_desc = ", ".join(filter_desc_parts) or "none"

    write_manifest(images, args.manifest, filter_desc)


def cmd_download(args: argparse.Namespace) -> None:
    if not args.manifest.exists() or args.refresh:
        cmd_crawl(args)

    payload = json.loads(args.manifest.read_text())
    images = [GalleryImage(**i) for i in payload["images"]]

    if not args.skip_filter:
        tags = load_tags()
        selected = resolve_tag_ids(args.tag, args.tag_id, args.tag_prefix, tags)
        tag_substrings = _split_csv(args.tag) + [name for _, name in selected]
        images = filter_images(
            images,
            tag_substrings=tag_substrings,
            game=args.game,
            alt_contains=args.alt_contains,
        )

    if args.limit:
        images = images[: args.limit]

    print(f"Downloading {len(images)} images to {args.images_dir}")
    session = make_session()
    n = download_images(
        session, images, args.images_dir,
        delay=args.delay, overwrite=args.overwrite,
    )
    print(f"Done: {n} new file(s) downloaded.")


def cmd_list_tags(args: argparse.Namespace) -> None:
    tags = load_tags()
    q = (args.query or "").lower()
    rows = [(tid, name) for name, tid in tags.items() if q in name.lower()]
    rows.sort(key=lambda r: r[1].lower())
    for tid, name in rows:
        print(f"{tid:>4}  {name}")
    print(f"\n{len(rows)} tag(s)" + (f" matching {args.query!r}" if args.query else ""))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    common.add_argument("--delay", type=float, default=0.5, help="Seconds between requests (default: 0.5)")
    common.add_argument("--max-pages", type=int, default=None, help="Stop after N pages (testing)")
    common.add_argument("--tag", action="append", default=None, metavar="NAME",
                        help="Tag name (repeatable, comma-sep ok). Resolved against tags.json. Multiple tags = OR.")
    common.add_argument("--tag-id", action="append", default=None, metavar="ID",
                        help="Numeric tag ID (repeatable, comma-sep ok)")
    common.add_argument("--tag-prefix", action="append", default=None, metavar="PREFIX",
                        help='Select every tag whose name starts with PREFIX, case-sensitive (e.g. --tag-prefix "SC")')
    common.add_argument("--game", help="Filter by game folder substring (e.g. 'RDR2', 'Star_Citizen')")
    common.add_argument("--alt-contains", help="Filter by alt-text substring")
    common.add_argument("--client-filter", action="store_true", help="Force pagination crawl + client-side filter even when tags are given")

    pc = sub.add_parser("crawl", parents=[common], help="Crawl gallery and write manifest.json")
    pc.set_defaults(func=cmd_crawl)

    pd = sub.add_parser("download", parents=[common], help="Crawl (if needed) then download images")
    pd.add_argument("--images-dir", type=Path, default=IMAGES_DIR_DEFAULT)
    pd.add_argument("--limit", type=int, default=None, help="Download at most N images")
    pd.add_argument("--overwrite", action="store_true")
    pd.add_argument("--refresh", action="store_true", help="Re-crawl even if manifest exists")
    pd.add_argument("--skip-filter", action="store_true", help="Download everything in the manifest as-is")
    pd.set_defaults(func=cmd_download)

    pt = sub.add_parser("list-tags", help="Print known tags (optionally filtered)")
    pt.add_argument("query", nargs="?", help="Substring filter")
    pt.set_defaults(func=cmd_list_tags)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
