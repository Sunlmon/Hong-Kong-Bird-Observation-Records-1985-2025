# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch the numbers once, save the raw reply to data/, and never fetch again.

    uv run fetch.py

Change URL and FILE. The default is the Hong Kong Observatory's daily mean
temperature for 2026, so the template runs before you have touched it and you
can see what a file looks like when it arrives. It is an example, not your
phenomenon: handing it in unchanged is handing in nothing.
"""

import json
import time
from pathlib import Path

import requests

START_YEAR = 1985
END_YEAR = 2025

URL = "https://api.gbif.org/v1/occurrence/search"
FILE_PATTERN = "gbif-hong-kong-birds-{year}.json"

HERE = Path(__file__).parent
DATA = HERE / "data"


def file_for_year(year):
    """Return the local raw-data filename for one year."""
    return DATA / FILE_PATTERN.format(year=year)


def fetch_year(year):
    """Fetch one year's raw GBIF reply once, then keep it."""
    path = file_for_year(year)

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

    print(f"{year}: downloading...")
    reply = requests.get(
        URL,
        params=parameters,
        timeout=60,
        headers={"User-Agent": "PolyU Assignment 2 student project"},
    )
    reply.raise_for_status()

    # Save the raw reply unchanged.
    path.write_text(reply.text, encoding="utf-8")

    info = json.loads(reply.text)
    print(f"{year}: saved {len(info['results'])} records to data/{path.name}")
    time.sleep(0.6)


def main():
    DATA.mkdir(exist_ok=True)

    for year in range(START_YEAR, END_YEAR + 1):
        fetch_year(year)


if __name__ == "__main__":
    main()