# War Table photos

Photo library for the YouTube channel **The War Table** (animated history map films). Public so that any Claude session, including claude.ai on a phone, can download images by URL without a login.

Right now it holds **people**: portraits of WW2 leaders and commanders, taken from the lead image and other images on each person's English Wikipedia article. Only Wikimedia Commons files with licences that allow monetised use are kept (public domain, CC0, CC BY, CC BY-SA). Images are stored at most 1200 px wide; the full-size original is at each photo's `source`.

## For Claude: how to use this

1. Fetch the index:
   `https://raw.githubusercontent.com/shanedevapp-creator/war-table-photos/main/catalog.json`
2. `people` is keyed by slug (`heinz-guderian`, `gort`, `kleist`, …). Each person has `name`, `zh_name` (Traditional Chinese), `country`, `tags` (`1940`, `panzer`, `navy`, `pacific`, …) and `photos`.
3. Each photo has `raw_url` (download it with curl), `lead` (true = the Wikipedia infobox portrait, usually the best choice), `width`/`height`, `date`, `description`, `author`, `license`, `source`.
4. Prefer a photo whose `date` falls in the film's period. For example, use Guderian in 1940 for Case Yellow, not 1945.
5. **Credits:** for every photo used whose `license` is not public domain or CC0, add a line to the video description:
   `<person> photo: <author or credit>, <license>, via Wikimedia Commons`.
   Bundesarchiv photos (`CC BY-SA 3.0 de`) are credited as `Bundesarchiv, Bild <number> / <photographer>`, which is already in `author`/`credit`.

`CATALOG.md` shows every photo as a thumbnail, so you can browse the library on a phone.

## Adding people

Add a line to `people.txt` (the English Wikipedia article title, a country code, tags, and an optional short slug), then:

```
python tools/fetch_people.py
```

It only fetches people not yet in `catalog.json` (`--refresh` redoes everyone), then rewrites `CATALOG.md`. Commit and push.

No free photo was found for René Prioux (French Cavalry Corps, 1940).
