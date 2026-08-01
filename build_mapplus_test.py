import re, pathlib, urllib.parse

VAULT_NAME = "Sovereign Creator OS Lite"
VAULT_ROOT = pathlib.Path("/Users/tomrubel/Downloads/Obsidian/Sovereign Creator OS Lite")
p = VAULT_ROOT / "05 - Projects/New England 2026/Places/✅❗️❌ Deuxave.md"
text = p.read_text(encoding="utf-8")
parts = text.split("---", 2)
body = parts[2].strip() if len(parts) >= 3 else text


def get_field(text, field):
    m = re.search(rf'^{re.escape(field)}:[ \t]*(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else None


coords_raw = get_field(text, "Coordinates")
lat, lon = [float(x.strip()) for x in coords_raw.split(",")]
gmaps_url = get_field(text, "url") or ""
rel_path = str(p.relative_to(VAULT_ROOT)).removesuffix(".md")
obsidian_uri = "obsidian://open?vault=" + urllib.parse.quote(VAULT_NAME) + "&file=" + urllib.parse.quote(rel_path)


def md_to_html(text):
    text = re.sub(r'^\[View on Google Maps\]\([^)]+\)\s*\n*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'^#{1,6}\s*(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'^\s*-\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '</p><p>', text)
    text = re.sub(r'\n', '<br/>', text)
    return text


html_body = md_to_html(body)
html_body += (
    f'<hr/><p><a href="{gmaps_url}">View on Google Maps</a></p>'
    f'<p><a href="{obsidian_uri}">Open in Obsidian</a></p>'
)

# KML color is aabbggrr (alpha, blue, green, red) hex -- teal (#008080) -> ff808000
kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<Placemark>
<name>Deuxave</name>
<description><![CDATA[<p>{html_body}]]></description>
<Style>
<IconStyle>
<color>ff808000</color>
<scale>1.2</scale>
<Icon><href>http://maps.google.com/mapfiles/kml/shapes/dining.png</href></Icon>
</IconStyle>
</Style>
<Point>
<coordinates>{lon},{lat},0</coordinates>
</Point>
</Placemark>
</Document>
</kml>
'''

out = pathlib.Path(__file__).parent / "mapplus_test.kml"
out.write_text(kml, encoding="utf-8")
print(f"Wrote KML, {len(kml)} bytes, to {out}")
