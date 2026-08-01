#!/usr/bin/env python3
"""
Export ONE note's full body content as a rich-content point for Guru Maps,
as a standalone overlay separate from the main day-to-day export.

Usage:
    python3 export_rich_note.py "<filename without .md>"

Searches Places/ and Destinations/ for a matching filename (with or without
the ✅/❗️/❌ status-prefix emojis some notes use), strips markdown down to
plain text (headers, bold, italics, links, wikilinks, images, blockquote
markers -- Guru's detail panel doesn't render any of that, and a link with
a real href mid-text breaks the renderer entirely), and writes a GeoJSON +
matching .ms Map Source file naming both after the note, e.g.:

    Deuxave.geojson, Deuxave.ms

Import Deuxave.ms into Guru Maps once; it's a separate overlay from the
main trip plan, so it won't collide with anything. Re-running this after
editing the note requires either waiting for the 60-min auto-refresh or
deleting and reimporting the .ms to force a fresh pull.
"""
import re
import sys
import json
import pathlib

VAULT = pathlib.Path("/Users/tomrubel/Downloads/Obsidian/Sovereign Creator OS Lite/05 - Projects/New England 2026")
OUT_DIR = pathlib.Path(__file__).parent
REPO_RAW_BASE = "https://raw.githubusercontent.com/trubel1/ne2026-map-export/main"


def get_field(text, field):
    m = re.search(rf'^{re.escape(field)}:[ \t]*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else None


def find_note(name):
    for folder in ["Places", "Destinations"]:
        for p in (VAULT / folder).glob("*.md"):
            if p.stem == name or p.stem.endswith(" " + name) or name in p.stem:
                return p
    return None


def clean_body(body):
    cleaned = body
    cleaned = re.sub(r'^\[View on Google Maps\]\([^)]+\)\s*\n*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', cleaned)  # images
    cleaned = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', cleaned)  # [[note|display]]
    cleaned = re.sub(r'\[\[([^\]]+)\]\]', r'\1', cleaned)  # [[note]]
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)  # [label](url)
    cleaned = re.sub(r'^#{1,6}\s*', '', cleaned, flags=re.MULTILINE)  # headers
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # bold
    cleaned = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', cleaned)  # italics
    cleaned = re.sub(r'>\s*', '', cleaned)  # blockquote markers
    cleaned = re.sub(r'\.[a-z]+(\+\d+)?(?=\s|\n|$)', '.', cleaned)  # AI-tool citation noise, e.g. ".chronogram+1"
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export_rich_note.py \"<note name>\"")
        sys.exit(1)
    query = sys.argv[1]
    p = find_note(query)
    if not p:
        print(f"No note found matching '{query}' in Places/ or Destinations/")
        sys.exit(1)

    text = p.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    body = parts[2].strip() if len(parts) >= 3 else text

    coords_raw = get_field(text, "Coordinates")
    if not coords_raw:
        print(f"'{p.name}' has no Coordinates -- can't place it on the map.")
        sys.exit(1)
    lat, lon = [float(x.strip()) for x in coords_raw.split(",")]
    icon = get_field(text, "icon") or "circle"
    color = get_field(text, "color") or "red"
    url = get_field(text, "url") or ""

    # strip status-prefix emojis for a clean display name
    clean_name = re.sub(r'^[^\w]+\s*', '', p.stem).strip()

    detail = clean_body(body)
    feature = {
        "type": "Feature",
        "properties": {"name": clean_name, "icon": icon, "color": color, "detail": detail, "website": url},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }
    fc = {"type": "FeatureCollection", "features": [feature]}

    slug = re.sub(r'[^A-Za-z0-9]+', '', clean_name)
    geojson_path = OUT_DIR / f"{slug}.geojson"
    mapcss_path = OUT_DIR / "map.mapcss"  # reuse the shared style
    ms_path = OUT_DIR / f"{slug}.ms"

    geojson_path.write_text(json.dumps(fc, indent=2))
    ms_path.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<customMapSource overlay="true">
    <name>{clean_name} (rich content)</name>
    <geojson url="{REPO_RAW_BASE}/{slug}.geojson" updateInterval="60"/>
    <style url="{REPO_RAW_BASE}/map.mapcss" updateInterval="60"/>
</customMapSource>
''')

    print(f"Wrote {geojson_path.name} ({len(detail)} chars) and {ms_path.name}")
    print(f"Import URL: {REPO_RAW_BASE}/{slug}.ms")
    print("Remember: git add/commit/push both files before that URL will work.")


if __name__ == "__main__":
    main()
