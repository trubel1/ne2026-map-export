#!/usr/bin/env python3
"""
Export New England 2026 vault notes for a given day to GeoJSON, for Guru Maps.

Usage:
    python3 export_day.py [YYYY-MM-DD]

If no date is given, defaults to tomorrow (relative to today).
Scans Places/ and Destinations/ for notes whose `day` frontmatter includes
the target date, and writes map.geojson in this directory.
"""
import re
import sys
import json
import pathlib
import datetime

VAULT = pathlib.Path("/Users/tomrubel/Downloads/Obsidian/Sovereign Creator OS Lite/05 - Projects/New England 2026")
OUT_DIR = pathlib.Path(__file__).parent

DAY_ABBR = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]  # Monday=0 .. Sunday=6, matches datetime.weekday()

def target_daynote(date_str):
    d = datetime.date.fromisoformat(date_str)
    abbr = DAY_ABBR[d.weekday()]
    return f"{d.isoformat()} {abbr}"

def get_field(text, field):
    m = re.search(rf'^{re.escape(field)}:[ \t]*(.+)$', text, re.MULTILINE)
    if m:
        val = m.group(1).strip()
        return val if val else None
    return None

def get_field_multiline(text, field):
    """Handles both `field: value` and `field:\\n  - value` (list) forms."""
    m = re.search(rf'^{re.escape(field)}:[ \t]*(.*)$', text, re.MULTILINE)
    if not m:
        return []
    inline = m.group(1).strip()
    if inline:
        return [inline.strip('"')]
    # list form: collect subsequent "  - ..." lines
    start = m.end()
    rest = text[start:]
    items = []
    for line in rest.split('\n'):
        lm = re.match(r'^\s*-\s*(.+)$', line)
        if lm:
            items.append(lm.group(1).strip().strip('"'))
        elif line.strip() == '':
            continue
        else:
            break
    return items

def get_list_type(text):
    m = re.search(r'^type:\s*\n\s*-\s*(\S+)', text, re.MULTILINE)
    if m:
        return m.group(1)
    m = re.search(r'^type:\s*(\S+)', text, re.MULTILINE)
    return m.group(1) if m else None

def matches_day(text, target_link):
    day_values = get_field_multiline(text, "day")
    for v in day_values:
        # v looks like [[2026-08-22 SA]] or [[2026-08-22 SA|Display]]
        inner = v.strip('[]').split('|')[0].strip()
        if inner == target_link:
            return True
    return False

def build_feature(p, text):
    name = p.stem
    icon = get_field(text, "icon") or "circle"
    color = get_field(text, "color") or "red"
    coords_raw = get_field(text, "Coordinates")
    if not coords_raw:
        return None
    try:
        lat, lon = [float(x.strip()) for x in coords_raw.split(",")]
    except ValueError:
        return None
    ptype = get_list_type(text)
    desc = get_field(text, "description") or ""
    url = get_field(text, "url") or ""
    start_dt = get_field(text, "start-date-time") or ""
    detail = desc
    if start_dt:
        detail = f"Time: {start_dt}\n\n" + detail if detail else f"Time: {start_dt}"
    if url:
        detail = (detail + "\n\n" if detail else "") + "Google Maps: " + url
    return {
        "type": "Feature",
        "properties": {
            "name": name,
            "icon": icon,
            "color": color,
            "vault_type": ptype,
            "description": desc,
            "url": url,
            "start_date_time": start_dt,
            "detail": detail,
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }

def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else (
        datetime.date.today() + datetime.timedelta(days=1)
    ).isoformat()
    target_link = target_daynote(date_str)

    features = []
    for folder in ["Places", "Destinations"]:
        for p in sorted((VAULT / folder).glob("*.md")):
            text = p.read_text(encoding="utf-8", errors="ignore")
            if matches_day(text, target_link):
                f = build_feature(p, text)
                if f:
                    features.append(f)

    fc = {"type": "FeatureCollection", "features": features}
    out = OUT_DIR / "map.geojson"
    out.write_text(json.dumps(fc, indent=2))

    print(f"Target day: {target_link}")
    print(f"Wrote {len(features)} features to {out}")
    for f in features:
        pr = f["properties"]
        print(" -", pr["name"], "|", pr["icon"], "|", pr["color"])

if __name__ == "__main__":
    main()
