# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///

import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

START_YEAR = 1985
END_YEAR = 2025
FILE_PATTERN = "gbif-hong-kong-birds-{year}.json"

# Hong Kong geographic bounds.
LON_MIN = 113.75
LON_MAX = 114.50
LAT_MIN = 22.10
LAT_MAX = 22.60

CANVAS_WIDTH = 1040
CANVAS_HEIGHT = 720

MAP_LEFT = 55
MAP_TOP = 105
MAP_WIDTH = 650
MAP_HEIGHT = 500

GRID_COLUMNS = 7
GRID_ROWS = 6
SPECIES_LIMIT = 24
PHASES_PER_YEAR = 2

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"


def file_for_year(year):
    """Return the cached raw GBIF file for one year."""
    return DATA / FILE_PATTERN.format(year=year)


def load_year(year):
    """Read bird name and valid Hong Kong coordinates from one year."""
    path = file_for_year(year)

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
            records.append((name, longitude, latitude))

    return records


def map_position(longitude, latitude):
    """Turn a real longitude/latitude pair into a location on the grid."""
    x = MAP_LEFT + (longitude - LON_MIN) / (LON_MAX - LON_MIN) * MAP_WIDTH
    y = MAP_TOP + (LAT_MAX - latitude) / (LAT_MAX - LAT_MIN) * MAP_HEIGHT

    return x, y


def colour_for_index(index, total):
    """Create evenly spaced, stable neon colours for the legend species."""
    hue = index / total
    red = int(80 + 175 * abs(math.sin(math.tau * (hue + 0.00))))
    green = int(80 + 175 * abs(math.sin(math.tau * (hue + 0.33))))
    blue = int(80 + 175 * abs(math.sin(math.tau * (hue + 0.66))))

    return red, green, blue


def short_name(name, length=25):
    """Keep long scientific names inside the legend table."""
    if len(name) <= length:
        return name

    return name[: length - 1] + "…"


def draw_feather(detail, glow, x, y, colour, breath):
    """Draw one glowing feather at a real observation coordinate."""
    length = 12 + 15 * breath
    width = 4 + 7 * breath

    top = y - length * 0.55
    bottom = y + length * 0.45

    detail_draw = ImageDraw.Draw(detail)
    glow_draw = ImageDraw.Draw(glow)

    # Central shaft.
    glow_draw.line(
        [(x, bottom), (x, top)],
        fill=(*colour, 155),
        width=4,
    )
    detail_draw.line(
        [(x, bottom), (x, top)],
        fill=(*colour, 245),
        width=1,
    )

    # Feather barbs.
    for index in range(7):
        progress = index / 6
        barb_y = bottom - progress * length * 0.85
        barb_width = width * math.sin(math.pi * progress)
        curve = 4 * (1 - progress)

        left = (x - barb_width, barb_y + curve)
        right = (x + barb_width, barb_y + curve)

        glow_draw.line([(x, barb_y), left], fill=(*colour, 120), width=3)
        glow_draw.line([(x, barb_y), right], fill=(*colour, 120), width=3)

        detail_draw.line([(x, barb_y), left], fill=(*colour, 220), width=1)
        detail_draw.line([(x, barb_y), right], fill=(*colour, 220), width=1)


def draw_legend(draw, species, colours, font):
    """Draw a fixed colour table that does not change with the year."""
    legend_x = 750
    legend_y = 130
    row_height = 32
    rows_per_column = 12

    draw.text(
        (legend_x, 92),
        "FIXED SPECIES COLOUR TABLE",
        fill=(185, 215, 255),
        font=font,
    )

    for index, name in enumerate(species):
        column = index // rows_per_column
        row = index % rows_per_column

        x = legend_x + column * 145
        y = legend_y + row * row_height

        draw.ellipse(
            [(x, y), (x + 13, y + 13)],
            fill=colours[name],
        )
        draw.text(
            (x + 20, y + 1),
            short_name(name, 20),
            fill=(190, 210, 235),
            font=font,
        )

    draw.ellipse(
        [(legend_x, 528), (legend_x + 13, 541)],
        fill=(110, 135, 165),
    )
    draw.text(
        (legend_x + 20, 529),
        "Other species",
        fill=(160, 180, 205),
        font=font,
    )


def make_frame(year, phase, records, species, colours):
    """Create one breathing map-grid animation frame."""
    image = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (3, 7, 16, 255))
    base_draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # Geographic grid: no visible coordinate numbers or axes.
    for column in range(GRID_COLUMNS + 1):
        x = MAP_LEFT + MAP_WIDTH * column / GRID_COLUMNS
        base_draw.line(
            [(x, MAP_TOP), (x, MAP_TOP + MAP_HEIGHT)],
            fill=(29, 52, 84, 120),
            width=1,
        )

    for row in range(GRID_ROWS + 1):
        y = MAP_TOP + MAP_HEIGHT * row / GRID_ROWS
        base_draw.line(
            [(MAP_LEFT, y), (MAP_LEFT + MAP_WIDTH, y)],
            fill=(29, 52, 84, 120),
            width=1,
        )

    detail = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))

    for index, (name, longitude, latitude) in enumerate(records):
        x, y = map_position(longitude, latitude)

        # Same species = same colour in every year.
        colour = colours.get(name, (110, 135, 165))

        # Slightly different rhythmic breathing for every observation.
        local_phase = phase * math.tau + index * 0.37
        breath = 0.65 + 0.35 * ((math.sin(local_phase) + 1) / 2)

        draw_feather(detail, glow, x, y, colour, breath)

    soft_glow = glow.filter(ImageFilter.GaussianBlur(radius=11))
    image = Image.alpha_composite(image, soft_glow)
    image = Image.alpha_composite(image, glow)
    image = Image.alpha_composite(image, detail)

    labels = ImageDraw.Draw(image)
    labels.text(
        (MAP_LEFT, 35),
        "HONG KONG BIRD OBSERVATION RECORDS",
        fill=(190, 220, 255),
        font=font,
    )
    labels.text(
        (MAP_LEFT, 58),
        "feather position = recorded longitude and latitude",
        fill=(105, 140, 185),
        font=font,
    )
    labels.text(
        (MAP_LEFT, 635),
        f"YEAR {year}  •  {len(records)} cached GBIF observations",
        fill=(145, 175, 220),
        font=font,
    )

    draw_legend(labels, species, colours, font)

    return image.convert("P", palette=Image.ADAPTIVE, colors=256)


def main():
    years = list(range(START_YEAR, END_YEAR + 1))
    records_by_year = {year: load_year(year) for year in years}

    all_records = []

    for records in records_by_year.values():
        all_records.extend(records)

    if not all_records:
        raise SystemExit("No bird data found. First run: uv run fetch.py")

    all_species = Counter(name for name, longitude, latitude in all_records)
    species = [name for name, count in all_species.most_common(SPECIES_LIMIT)]

    colours = {
        name: colour_for_index(index, len(species))
        for index, name in enumerate(species)
    }

    print("Making animated GIF...")
    frames = []

    for year in years:
        for step in range(PHASES_PER_YEAR):
            phase = step / PHASES_PER_YEAR
            frames.append(
                make_frame(
                    year,
                    phase,
                    records_by_year[year],
                    species,
                    colours,
                )
            )

    OUT.mkdir(exist_ok=True)
    output = OUT / "hong-kong-bird-space-and-rhythm-1985-to-2025.gif"

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=190,
        loop=0,
        disposal=2,
        optimize=True,
    )

    print(f"Saved {output}")


if __name__ == "__main__":
    main()