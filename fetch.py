# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

import json
import time
from pathlib import Path

import requests

START_YEAR = 1985
END_YEAR = 2025

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"
BIRD_FILE_PATTERN = "gbif-hong-kong-birds-{year}.json"

# Hong Kong Government district-boundary GeoJSON.
BOUNDARY_URL = (
    "https://www.had.gov.hk/psi/"
    "hong-kong-administrative-boundaries/"
    "hksar_18_district_boundary.json"
)
BOUNDARY_FILE = "hong-kong-boundary.geojson"

HERE = Path(__file__).parent
DATA = HERE / "data"

HEADERS = {
    "User-Agent": "PolyU Assignment 2 bird visualisation project"
}


def bird_file(year):
    """Return the cache path for one year of bird records."""
    return DATA / BIRD_FILE_PATTERN.format(year=year)


def fetch_boundary():
    """Fetch and cache the Hong Kong boundary GeoJSON once."""
    path = DATA / BOUNDARY_FILE

    if path.exists():
        print("Boundary: already saved — skipping")
        return

    print("Boundary: downloading Hong Kong boundary GeoJSON...")
    reply = requests.get(
        BOUNDARY_URL,
        timeout=60,
        headers=HEADERS,
    )
    reply.raise_for_status()

    # Save the raw government JSON unchanged.
    path.write_text(reply.text, encoding="utf-8")
    print(f"Boundary: saved data/{BOUNDARY_FILE}")


def fetch_birds_for_year(year):
    """Fetch and cache one year of raw GBIF bird records once."""
    path = bird_file(year)

    if path.exists():
        print(f"{year}: already saved — skipping")
        return

    parameters = {
        "class": "Aves",
        "country": "HK",
        "year": year,
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "limit": 300,
    }

    print(f"{year}: downloading bird records...")
    reply = requests.get(
        GBIF_URL,
        params=parameters,
        timeout=60,
        headers=HEADERS,
    )
    reply.raise_for_status()

    # Save the raw GBIF reply unchanged.
    path.write_text(reply.text, encoding="utf-8")

    info = json.loads(reply.text)
    print(
        f"{year}: saved {len(info['results'])} records "
        f"to data/{path.name}"
    )

    # Be polite to the public API.
    time.sleep(0.6)


def main():
    DATA.mkdir(exist_ok=True)

    fetch_boundary()

    for year in range(START_YEAR, END_YEAR + 1):
        fetch_birds_for_year(year)


if __name__ == "__main__":
    main()