"""Download portraits for everyone in people.txt from Wikipedia / Wikimedia Commons.

For each person: the article's lead image, plus up to MAX_EXTRA other images on the
article whose file name mentions the person. Only files hosted on Commons under a
licence that allows monetised use (public domain, CC0, CC BY, CC BY-SA) are kept.

Writes people/<slug>/<slug>-NN.<ext>, catalog.json and CATALOG.md.

  python tools/fetch_people.py            # add people not yet in catalog.json
  python tools/fetch_people.py --refresh  # redo everyone
"""
import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "shanedevapp-creator/war-table-photos"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
UA = "WarTablePhotos/1.0 (https://github.com/shanedevapp-creator/war-table-photos)"
ENWIKI = "https://en.wikipedia.org/w/api.php"
ZHWIKI = "https://zh.wikipedia.org/w/api.php"
WIDTH = 1200        # stored width; originals stay on Commons (see "source")
MAX_EXTRA = 4       # extra images per person besides the lead image
MIN_WIDTH = 300
# File names that are about the person but are not photos of them
NOT_PORTRAIT = re.compile(r"signat|unterschrift|arms|statue|grave|grab |tomb|necropolis|monument|memorial|"
                          r"stamp|coin|obverse|reverse|plaque|straße|street|laarzen|alej |carlton gardens|bust", re.I)
STOP = {"von", "der", "de", "of", "the", "ritter", "earl", "viscount", "1st", "6th",
        "tunis", "belgium", "d.", "s.", "c.", "w."}


def api(params, endpoint=ENWIKI):
    params = {**params, "format": "json", "formatversion": "2"}
    req = urllib.request.Request(endpoint + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 3)


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 + attempt * 5)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def clean(v):
    v = re.sub(r"<[^>]+>", " ", v or "")
    return re.sub(r"\s+", " ", html.unescape(v)).strip()


def free_licence(name):
    n = name.lower()
    if "nc" in re.split(r"[\s\-]+", n) or "nd" in re.split(r"[\s\-]+", n):
        return False
    return n.startswith(("public domain", "pd")) or "cc0" in n or n.startswith(("cc by", "cc-by"))


def keywords(title):
    words = re.findall(r"[^\s,]+", title)
    return {slugify(w) for w in words if w.lower() not in STOP and len(slugify(w)) > 2}


def read_people():
    people = []
    for line in (ROOT / "people.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        title, country, tags, *slug = [p.strip() for p in line.split("|")]
        people.append((title, country, [t for t in tags.split(",") if t], slug[0] if slug else None))
    return people


def fetch_person(title, country, tags, slug=None):
    page = api({"action": "query", "titles": title, "redirects": 1,
                "prop": "pageimages|langlinks|images|pageprops", "piprop": "name",
                "lllang": "zh", "imlimit": "max"})["query"]["pages"][0]
    if page.get("missing"):
        print(f"  !! no article: {title}")
        return None
    slug = slug or slugify(page["title"])
    keys = keywords(page["title"])
    lead = page.get("pageimage")
    files = [f"File:{lead}"] if lead else []
    for im in page.get("images", []):
        name = im["title"]
        if name in files or not re.search(r"\.(jpe?g|png|tiff?)$", name, re.I):
            continue
        if keys & set(slugify(name).split("-")) and not NOT_PORTRAIT.search(name):
            files.append(name)

    info = api({"action": "query", "titles": "|".join(files[:40]), "prop": "imageinfo",
                "iiprop": "url|size|mime|sha1|extmetadata", "iiurlwidth": WIDTH})["query"]["pages"] if files else []
    by_title = {p["title"]: p for p in info}

    out_dir = ROOT / "people" / slug
    photos, skipped, seen = [], [], set()
    for name in files:
        p = by_title.get(name.replace("_", " "))
        if not p or p.get("imagerepository") != "shared" or not p.get("imageinfo"):
            skipped.append((name, "not on Commons (non-free or local)"))
            continue
        ii = p["imageinfo"][0]
        meta = {k: v.get("value", "") for k, v in ii.get("extmetadata", {}).items()}
        lic = clean(meta.get("LicenseShortName"))
        if not free_licence(lic):
            skipped.append((name, f"licence: {lic or 'unknown'}"))
            continue
        if ii["width"] < MIN_WIDTH:
            skipped.append((name, f"too small ({ii['width']}px)"))
            continue
        if ii["sha1"] in seen:
            skipped.append((name, "duplicate of an earlier file"))
            continue
        seen.add(ii["sha1"])
        if len(photos) >= 1 + MAX_EXTRA:
            break
        url = ii.get("thumburl") if ii["width"] > WIDTH else ii["url"]
        ext = Path(urllib.parse.urlparse(url).path).suffix.lower().replace(".jpeg", ".jpg")
        if ext in (".tif", ".tiff"):
            ext = ".jpg"
        rel = f"people/{slug}/{slug}-{len(photos) + 1:02d}{ext}"
        out_dir.mkdir(parents=True, exist_ok=True)
        download(url, ROOT / rel)
        w = ii.get("thumbwidth") if url != ii["url"] else ii["width"]
        h = ii.get("thumbheight") if url != ii["url"] else ii["height"]
        photos.append({
            "file": rel,
            "raw_url": RAW + urllib.parse.quote(rel),
            "lead": name == files[0] and bool(lead),
            "width": w, "height": h,
            "description": clean(meta.get("ImageDescription"))[:400],
            "date": re.sub(r"\s*date QS:.*$", "", clean(meta.get("DateTimeOriginal")))[:80],
            "author": clean(meta.get("Artist"))[:200],
            "credit": clean(meta.get("Credit"))[:200],
            "license": lic,
            "license_url": clean(meta.get("LicenseUrl")),
            "attribution_required": clean(meta.get("AttributionRequired")) == "true",
            "commons_file": name,
            "source": ii["descriptionurl"],
        })
        time.sleep(0.3)

    for name, why in skipped:
        print(f"     skip {name}: {why}")
    zh = next((l["title"] for l in page.get("langlinks", []) if l["lang"] == "zh"), "")
    if zh:  # Traditional Chinese (Taiwan) form of the title
        zp = api({"action": "query", "titles": zh, "prop": "info", "inprop": "varianttitles"},
                 ZHWIKI)["query"]["pages"][0]
        zh = zp.get("varianttitles", {}).get("zh-tw", zh)
    return slug, {
        "name": page["title"],
        "zh_name": zh,
        "country": country,
        "tags": tags,
        "wikipedia": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(page["title"].replace(" ", "_")),
        "wikidata": page.get("pageprops", {}).get("wikibase_item", ""),
        "photos": photos,
    }


def write_markdown(cat):
    lines = ["# People", "",
             "Generated by `tools/fetch_people.py` from `catalog.json`. Licences and authors are in `catalog.json`.", "",
             "| Person | 中文 | Country | Photos |", "|---|---|---|---|"]
    for slug, p in sorted(cat["people"].items(), key=lambda kv: (kv[1]["country"], kv[0])):
        imgs = " ".join(f'<img src="{ph["file"]}" height="90">' for ph in p["photos"])
        lines.append(f"| [{p['name']}]({p['wikipedia']}) `{slug}` | {p['zh_name']} | {p['country']} | {imgs or '—'} |")
    (ROOT / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    refresh = "--refresh" in sys.argv
    cat_path = ROOT / "catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8")) if cat_path.exists() else {}
    cat.setdefault("raw_base", RAW)
    cat.setdefault("people", {})
    done = {p["name"] for p in cat["people"].values()}
    for title, country, tags, slug in read_people():
        if title in done and not refresh:
            continue
        print(f"- {title}")
        res = fetch_person(title, country, tags, slug)
        if res:
            slug, entry = res
            cat["people"][slug] = entry
            print(f"     {len(entry['photos'])} photo(s), zh: {entry['zh_name']}")
            cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(0.5)
    cat["people"] = dict(sorted(cat["people"].items()))
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    write_markdown(cat)
    n = sum(len(p["photos"]) for p in cat["people"].values())
    print(f"done: {len(cat['people'])} people, {n} photos")


if __name__ == "__main__":
    main()
