import colorsys
import hashlib
import json
import math
from collections import Counter
from html import escape
from pathlib import Path

START_YEAR = 1985
END_YEAR = 2025

BIRD_FILE_PATTERN = "gbif-hong-kong-birds-{year}.json"
BOUNDARY_FILE = "hong-kong-boundary.geojson"

LON_MIN = 113.75
LON_MAX = 114.50
LAT_MIN = 22.10
LAT_MAX = 22.60

SPECIES_LIMIT = 24

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"
SITE = HERE / "site"


def bird_file(year):
    """Return the cached bird-data file for one year."""
    return DATA / BIRD_FILE_PATTERN.format(year=year)


def load_year(year):
    """Read valid Hong Kong bird observations from one cached JSON file."""
    path = bird_file(year)

    if not path.exists():
        return []

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    records = []

    for record in raw_data["results"]:
        name = record.get("scientificName")
        longitude = record.get("decimalLongitude")
        latitude = record.get("decimalLatitude")

        if not name or longitude is None or latitude is None:
            continue

        longitude = float(longitude)
        latitude = float(latitude)

        if LON_MIN <= longitude <= LON_MAX and LAT_MIN <= latitude <= LAT_MAX:
            records.append(
                {
                    "name": name,
                    "longitude": round(longitude, 5),
                    "latitude": round(latitude, 5),
                }
            )

    return records


def rings_from_geometry(geometry):
    """Extract longitude/latitude rings from Polygon or MultiPolygon GeoJSON."""
    if not geometry:
        return []

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "Polygon":
        return coordinates

    if geometry_type == "MultiPolygon":
        rings = []

        for polygon in coordinates:
            rings.extend(polygon)

        return rings

    return []


def load_boundary():
    """Read Hong Kong outer-boundary rings from cached GeoJSON."""
    path = DATA / BOUNDARY_FILE

    if not path.exists():
        raise SystemExit(
            f"Missing data/{BOUNDARY_FILE}. First run: uv run fetch.py"
        )

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    rings = []

    if raw_data.get("type") == "FeatureCollection":
        for feature in raw_data.get("features", []):
            rings.extend(rings_from_geometry(feature.get("geometry")))

    elif raw_data.get("type") == "Feature":
        rings.extend(rings_from_geometry(raw_data.get("geometry")))

    else:
        rings.extend(rings_from_geometry(raw_data))

    clean_rings = []

    for ring in rings:
        clean_ring = []

        for point in ring:
            if len(point) >= 2:
                clean_ring.append(
                    [round(float(point[0]), 5), round(float(point[1]), 5)]
                )

        if len(clean_ring) >= 3:
            clean_rings.append(clean_ring)

    if not clean_rings:
        raise SystemExit("The cached Hong Kong boundary has no usable polygons.")

    return clean_rings


def hue_for_species(name):
    """Give each species one permanent hue."""
    number = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)
    return number % 360


def hex_colour(hue, saturation=0.9, brightness=1.0):
    """Convert HSV values into a hex colour for SVG."""
    red, green, blue = colorsys.hsv_to_rgb(hue / 360, saturation, brightness)
    return f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"


def map_position(longitude, latitude, left, top, width, height):
    """Map true longitude/latitude to a drawing position."""
    x = left + (longitude - LON_MIN) / (LON_MAX - LON_MIN) * width
    y = top + (LAT_MAX - latitude) / (LAT_MAX - LAT_MIN) * height

    return x, y


def svg_boundary_path(ring, left, top, width, height):
    """Create one SVG path from a boundary ring."""
    points = []

    for longitude, latitude in ring:
        x, y = map_position(longitude, latitude, left, top, width, height)
        points.append((x, y))

    if not points:
        return ""

    start_x, start_y = points[0]
    path = f"M {start_x:.1f} {start_y:.1f}"

    for x, y in points[1:]:
        path += f" L {x:.1f} {y:.1f}"

    return path + " Z"


def svg_feather(x, y, colour, opacity, bend):
    """Return SVG paths for one curved feather."""
    length = 26
    width = 10
    parts = []

    parts.append(
        f'<path d="M {x:.1f} {y + length * 0.45:.1f} '
        f'Q {x + bend:.1f} {y:.1f} {x:.1f} {y - length * 0.55:.1f}" '
        f'stroke="{colour}" stroke-width="1.4" fill="none" opacity="{opacity:.2f}"/>'
    )

    for index in range(1, 8):
        progress = index / 8
        shaft_y = y + length * 0.45 - progress * length
        barb = width * math.sin(math.pi * progress)
        curve = 4 * (1 - progress)

        parts.append(
            f'<path d="M {x + bend * math.sin(math.pi * progress):.1f} {shaft_y:.1f} '
            f'Q {x - barb * 0.35:.1f} {shaft_y + curve:.1f} '
            f'{x - barb:.1f} {shaft_y + curve * 1.8:.1f}" '
            f'stroke="{colour}" stroke-width="1" fill="none" opacity="{opacity:.2f}"/>'
        )
        parts.append(
            f'<path d="M {x + bend * math.sin(math.pi * progress):.1f} {shaft_y:.1f} '
            f'Q {x + barb * 0.35:.1f} {shaft_y + curve:.1f} '
            f'{x + barb:.1f} {shaft_y + curve * 1.8:.1f}" '
            f'stroke="{colour}" stroke-width="1" fill="none" opacity="{opacity:.2f}"/>'
        )

    return parts


def write_preview_svg(records_by_year, species, hues, boundary):
    """Write a static preview image that README.md can embed."""
    preview_year = END_YEAR
    records = records_by_year[str(preview_year)]

    if not records:
        for year in range(END_YEAR, START_YEAR - 1, -1):
            if records_by_year[str(year)]:
                preview_year = year
                records = records_by_year[str(year)]
                break

    width = 1160
    height = 720
    map_left = 100
    map_top = 105
    map_width = 650
    map_height = 480

    counts = Counter(record["name"] for record in records)
    highest_count = max(counts.values(), default=1)

    feathers = []

    for index, record in enumerate(records):
        name = record["name"]

        x, y = map_position(
            record["longitude"],
            record["latitude"],
            map_left,
            map_top,
            map_width,
            map_height,
        )

        focus = name in hues
        saturation = 0.20 + 0.78 * math.sqrt(counts[name] / highest_count)
        hue = hues[name] if focus else 210

        if not focus:
            saturation *= 0.28

        colour = hex_colour(hue, saturation, 0.92)

        feathers.append(
            (
                saturation,
                focus,
                x,
                y,
                colour,
                math.sin(index * 1.71) * 5,
            )
        )

    feathers.sort(key=lambda feather: feather[0])

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="720" viewBox="0 0 1160 720">',
        '<defs><filter id="softGlow"><feGaussianBlur stdDeviation="4"/></filter></defs>',
        '<rect width="1160" height="720" fill="#030710"/>',
        '<rect x="100" y="105" width="650" height="480" fill="#08162a" stroke="#284866"/>',
        '<text x="100" y="42" fill="#c7dcf7" font-family="Arial" font-size="18">HONG KONG BIRD OBSERVATION RECORDS</text>',
        f'<text x="100" y="65" fill="#86a5cb" font-family="Arial" font-size="13">YEAR {preview_year} • feather position = recorded longitude and latitude</text>',
        f'<text x="100" y="615" fill="#7898bf" font-family="Arial" font-size="12">{LON_MIN:.2f}°E</text>',
        f'<text x="700" y="615" fill="#7898bf" font-family="Arial" font-size="12">{LON_MAX:.2f}°E</text>',
        f'<text x="20" y="110" fill="#7898bf" font-family="Arial" font-size="12">{LAT_MAX:.2f}°N</text>',
        f'<text x="20" y="585" fill="#7898bf" font-family="Arial" font-size="12">{LAT_MIN:.2f}°N</text>',
        '<text x="805" y="92" fill="#c9ddf7" font-family="Arial" font-size="14">FIXED SPECIES COLOUR TABLE</text>',
    ]

    # Grey Hong Kong boundary is behind all feathers.
    parts.append('<g stroke="#a9b2bb" stroke-width="1" fill="none" opacity="0.36">')

    for ring in boundary:
        path = svg_boundary_path(ring, map_left, map_top, map_width, map_height)

        if path:
            parts.append(f'<path d="{path}"/>')

    parts.append("</g>")

    # Soft glow only for focus species.
    parts.append('<g filter="url(#softGlow)" opacity="0.30">')

    for saturation, focus, x, y, colour, bend in feathers:
        if focus:
            parts.extend(svg_feather(x, y, colour, 0.65, bend))

    parts.append("</g>")

    # Detailed feathers on top.
    for saturation, focus, x, y, colour, bend in feathers:
        opacity = 0.85 if focus else 0.38
        parts.extend(svg_feather(x, y, colour, opacity, bend))

    for index, name in enumerate(species):
        column = index // 12
        row = index % 12
        x = 805 + column * 175
        y = 130 + row * 32
        colour = hex_colour(hues[name])

        parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{colour}"/>')
        parts.append(
            f'<text x="{x + 14}" y="{y + 4}" fill="#c8d8eb" '
            f'font-family="Arial" font-size="11">{escape(name)}</text>'
        )

    parts.append(
        '<circle cx="805" cy="530" r="6" fill="#6e87a5"/>'
        '<text x="819" y="534" fill="#a0b4cd" font-family="Arial" font-size="11">Other species</text>'
    )
    parts.append("</svg>")

    OUT.mkdir(exist_ok=True)
    output = OUT / f"hong-kong-bird-records-{preview_year}.svg"
    output.write_text("\n".join(parts), encoding="utf-8")
    print(f"Saved {output}")


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hong Kong Bird Records</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    min-height: 100vh;
    color: #dceaff;
    background: #030710;
    font-family: Arial, sans-serif;
}
main { width: min(1200px, 96vw); margin: 24px auto; }
header {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 16px;
    margin-bottom: 16px;
}
h1 { margin: 0; font-size: clamp(20px, 3vw, 32px); letter-spacing: 0.08em; }
p { margin: 8px 0 0; color: #8fa8ca; }
label { color: #bcd3ef; font-size: 14px; }
select {
    margin-left: 8px; padding: 8px 12px; border: 1px solid #345071;
    border-radius: 6px; color: #e9f4ff; background: #0b1424; font-size: 16px;
}
.layout { display: grid; grid-template-columns: minmax(0, 1fr) 330px; gap: 18px; }
canvas {
    width: 100%; height: auto; display: block;
    border: 1px solid #223d5c; background: #030710;
}
aside { padding: 18px; border: 1px solid #223d5c; background: #07101e; }
aside h2 {
    margin: 0 0 14px; font-size: 14px; letter-spacing: 0.12em; color: #c9ddf7;
}
#legend { display: grid; grid-template-columns: 1fr 1fr; gap: 9px 12px; }
.legend-row {
    display: flex; align-items: center; gap: 7px; min-width: 0;
    color: #c8d8eb; font-size: 11px;
}
.dot {
    width: 11px; height: 11px; flex: 0 0 auto; border-radius: 50%;
    box-shadow: 0 0 7px currentColor;
}
.legend-row span:last-child {
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.note {
    margin-top: 18px; padding-top: 12px; border-top: 1px solid #223d5c;
    color: #7895ba; font-size: 12px; line-height: 1.5;
}
@media (max-width: 850px) {
    .layout { grid-template-columns: 1fr; }
    #legend { grid-template-columns: repeat(3, 1fr); }
    header { align-items: start; flex-direction: column; }
}
</style>
</head>
<body>
<main>
<header>
    <div>
        <h1>HONG KONG BIRD OBSERVATION RECORDS</h1>
        <p>Each feather is one cached GBIF observation. Position uses longitude and latitude.</p>
    </div>
    <label>Select year: <select id="year"></select></label>
</header>

<div class="layout">
    <canvas id="map" width="760" height="650"></canvas>
    <aside>
        <h2>FIXED SPECIES COLOUR TABLE</h2>
        <div id="legend"></div>
        <div class="note">
            This project transforms bird observation records in Hong Kong from 1985 to 2025
            into an interactive visualisation. I chose birds as the research subject because
            they are connected to natural environments, urban space, and human
            observation activities.
        </div>
    </aside>
</div>
</main>

<script>
const DATA = __DATA__;

const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
const yearSelect = document.getElementById("year");
const legend = document.getElementById("legend");

const MAP_LEFT = 80;
const MAP_TOP = 92;
const MAP_WIDTH = 620;
const MAP_HEIGHT = 450;

const hueBySpecies = new Map(DATA.species.map(item => [item.name, item.hue]));
let selectedYear = DATA.defaultYear;
let points = [];

function colour(hue, saturation, brightness, alpha = 1) {
    return `hsla(${hue}, ${saturation}%, ${brightness}%, ${alpha})`;
}

function mapPosition(longitude, latitude) {
    return {
        x: MAP_LEFT + (longitude - DATA.bounds.lonMin)
            / (DATA.bounds.lonMax - DATA.bounds.lonMin) * MAP_WIDTH,
        y: MAP_TOP + (DATA.bounds.latMax - latitude)
            / (DATA.bounds.latMax - DATA.bounds.latMin) * MAP_HEIGHT,
    };
}

function drawBoundary() {
    ctx.save();
    ctx.strokeStyle = "rgba(185, 195, 205, 0.35)";
    ctx.lineWidth = 1;
    ctx.beginPath();

    for (const ring of DATA.boundary) {
        ring.forEach((point, index) => {
            const position = mapPosition(point[0], point[1]);

            if (index === 0) {
                ctx.moveTo(position.x, position.y);
            } else {
                ctx.lineTo(position.x, position.y);
            }
        });

        ctx.closePath();
    }

    ctx.stroke();
    ctx.restore();
}

function prepareYear(year) {
    const records = DATA.records[year] || [];
    const counts = new Map();

    for (const record of records) {
        counts.set(record.name, (counts.get(record.name) || 0) + 1);
    }

    const maxCount = Math.max(1, ...counts.values());

    points = records.map((record, index) => {
        const position = mapPosition(record.longitude, record.latitude);
        const count = counts.get(record.name);
        const isFocusSpecies = hueBySpecies.has(record.name);

        let saturation = 20 + 78 * Math.sqrt(count / maxCount);
        let hue = hueBySpecies.get(record.name);

        if (!isFocusSpecies) {
            hue = 210;
            saturation *= 0.28;
        }

        return {
            ...position,
            hue,
            saturation,
            brightness: 54 + 40 * Math.sqrt(count / maxCount),
            glows: isFocusSpecies,
            phase: index * 0.37,
        };
    });

    // Low saturation first, high saturation on top.
    points.sort((a, b) => a.saturation - b.saturation);
}

function drawFeatherLines(length, width, bend) {
    ctx.beginPath();
    ctx.moveTo(0, length * 0.45);
    ctx.quadraticCurveTo(bend, 0, 0, -length * 0.55);
    ctx.stroke();

    for (let index = 1; index < 10; index++) {
        const progress = index / 10;
        const y = length * 0.45 - progress * length;
        const barb = width * Math.sin(Math.PI * progress);
        const curve = 4 * (1 - progress);

        ctx.beginPath();
        ctx.moveTo(bend * Math.sin(Math.PI * progress), y);
        ctx.quadraticCurveTo(-barb * 0.35, y + curve, -barb, y + curve * 1.8);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bend * Math.sin(Math.PI * progress), y);
        ctx.quadraticCurveTo(barb * 0.35, y + curve, barb, y + curve * 1.8);
        ctx.stroke();
    }
}

function drawFeather(point, time) {
    const breath = 0.72 + 0.28 * ((Math.sin(time * 0.002 + point.phase) + 1) / 2);
    const length = 14 + 20 * breath;
    const width = 5 + 7 * breath;
    const bend = Math.sin(point.phase * 2.7) * 5;

    ctx.save();
    ctx.translate(point.x, point.y);
    ctx.rotate(Math.sin(point.phase) * 0.15);

    if (point.glows) {
        ctx.shadowColor = colour(point.hue, point.saturation, point.brightness, 0.35);
        ctx.shadowBlur = 9;
        ctx.strokeStyle = colour(point.hue, point.saturation, point.brightness, 0.26);
        ctx.lineWidth = 3.2;
        drawFeatherLines(length, width, bend);
    }

    ctx.shadowBlur = 0;
    ctx.strokeStyle = point.glows
        ? colour(point.hue, point.saturation, point.brightness, 0.82)
        : colour(point.hue, point.saturation, point.brightness, 0.42);

    ctx.lineWidth = point.glows ? 1.15 : 0.8;
    drawFeatherLines(length, width, bend);

    ctx.restore();
}

function label(text, x, y, align = "left") {
    ctx.textAlign = align;
    ctx.fillStyle = "#7898bf";
    ctx.font = "11px Arial";
    ctx.fillText(text, x, y);
}

function drawMap(time) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const gradient = ctx.createRadialGradient(380, 300, 20, 380, 300, 540);
    gradient.addColorStop(0, "#08162a");
    gradient.addColorStop(1, "#030710");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "#284866";
    ctx.lineWidth = 1;
    ctx.strokeRect(MAP_LEFT, MAP_TOP, MAP_WIDTH, MAP_HEIGHT);

    drawBoundary();

    label(`${DATA.bounds.lonMin.toFixed(2)}°E`, MAP_LEFT, MAP_TOP + MAP_HEIGHT + 25);
    label(`${DATA.bounds.lonMax.toFixed(2)}°E`, MAP_LEFT + MAP_WIDTH, MAP_TOP + MAP_HEIGHT + 25, "right");
    label(`${DATA.bounds.latMax.toFixed(2)}°N`, MAP_LEFT - 10, MAP_TOP + 4, "right");
    label(`${DATA.bounds.latMin.toFixed(2)}°N`, MAP_LEFT - 10, MAP_TOP + MAP_HEIGHT, "right");

    for (const point of points) {
        drawFeather(point, time);
    }

    ctx.textAlign = "left";
    ctx.fillStyle = "#c7dcf7";
    ctx.font = "16px Arial";
    ctx.fillText(`YEAR ${selectedYear}`, MAP_LEFT, 42);

    ctx.fillStyle = "#86a5cb";
    ctx.font = "12px Arial";
    ctx.fillText(
        `${points.length} cached GBIF observations • feather position = geographic record`,
        MAP_LEFT,
        64,
    );

    requestAnimationFrame(drawMap);
}

function makeLegend() {
    for (const species of DATA.species) {
        const row = document.createElement("div");
        row.className = "legend-row";

        const dot = document.createElement("span");
        dot.className = "dot";
        dot.style.background = colour(species.hue, 90, 60);
        dot.style.color = colour(species.hue, 90, 60);

        const name = document.createElement("span");
        name.textContent = species.name;
        name.title = species.name;

        row.append(dot, name);
        legend.append(row);
    }
}

for (const year of DATA.years) {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;

    if (year === selectedYear) {
        option.selected = true;
    }

    yearSelect.append(option);
}

yearSelect.addEventListener("change", event => {
    selectedYear = Number(event.target.value);
    prepareYear(selectedYear);
});

makeLegend();
prepareYear(selectedYear);
requestAnimationFrame(drawMap);
</script>
</body>
</html>
"""


def main():
    years = list(range(START_YEAR, END_YEAR + 1))
    records_by_year = {str(year): load_year(year) for year in years}
    boundary = load_boundary()

    all_records = []

    for records in records_by_year.values():
        all_records.extend(records)

    if not all_records:
        raise SystemExit("No bird data found. First run: uv run fetch.py")

    counts = Counter(record["name"] for record in all_records)
    species = [name for name, count in counts.most_common(SPECIES_LIMIT)]
    hues = {name: hue_for_species(name) for name in species}

    available_years = [
        year for year in years if records_by_year[str(year)]
    ]
    default_year = available_years[-1] if available_years else END_YEAR

    page_data = {
        "years": years,
        "defaultYear": default_year,
        "bounds": {
            "lonMin": LON_MIN,
            "lonMax": LON_MAX,
            "latMin": LAT_MIN,
            "latMax": LAT_MAX,
        },
        "species": [{"name": name, "hue": hues[name]} for name in species],
        "records": records_by_year,
        "boundary": boundary,
    }

    SITE.mkdir(exist_ok=True)
    html_output = SITE / "index.html"

    page = HTML.replace(
        "__DATA__",
        json.dumps(page_data, ensure_ascii=False),
    )

    html_output.write_text(page, encoding="utf-8")
    print(f"Saved {html_output}")

    write_preview_svg(records_by_year, species, hues, boundary)


if __name__ == "__main__":
    main()