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

## Units (drawn graphics)

`units/` holds original vector drawings of WW2 equipment and soldiers for overlays and map animations. All share one style: dark outline `#2c2f27`, transparent background, side view facing right (flip horizontally for the other direction). Each comes as an `.svg` (scales to any size) and a `.png` render.

| Group | Files |
|---|---|
| German army | `panzer-iv-side`, `panzer-iv-top` (map counter, rotate to heading), `lefh18-howitzer-side`, `german-infantry-side` |
| Allied army | `char-b1-side` (French heavy tank), `matilda-ii-side` (British), `french-infantry-side`, `british-infantry-side`, `supply-truck-side` |
| Aircraft | `bf109-side`, `ju87-stuka-side`, `he111-side` (German); `spitfire-side`, `d520-side` (Allied) |
| Warships | `battleship-side`, `cruiser-side`, `destroyer-side`, `submarine-side`, `carrier-side` (generic, no national markings) |

## Map icons

`icons/` holds map symbols in the same style.

- Unit counters (NATO style), two sides each — `unit-<type>-german` (grey) and `unit-<type>-allied` (blue), type = `infantry`, `armor`, `mechanized`, `artillery`, `recon`, `headquarters`
- Unit size markers to place above a counter: `size-army` (XXXX), `size-corps` (XXX), `size-division` (XX), `size-brigade` (X), `size-regiment` (III)
- `attack-arrow-red`, `attack-arrow-blue`, `attack-arrow-grey`
- `explosion`, `fortress`, `airfield`, `port`, `supply`, `defense-line` (repeatable horizontally)

Raw URL pattern: `https://raw.githubusercontent.com/shanedevapp-creator/war-table-photos/main/<units|icons>/<file>`. These are drawn for the channel, so no credit line is needed.
