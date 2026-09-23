"""
Step 1 - Download POI (place) and road (segment) data from Overture Maps.

Requires the Overture Maps CLI:  pip install overturemaps

Output: data/input/city/<city>/<city>_place.geoparquet
        data/input/city/<city>/<city>_segment.geoparquet

Usage:
    python scripts/01_download_data.py                  # all cities in cities.py
    python scripts/01_download_data.py amsterdam paris  # selected cities only
"""
import os
import sys
import time
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from cities import CITIES

OUT_ROOT = "data/input/city"
DATA_TYPES = ["place", "segment"]  # POIs and transportation segments


def download_city(city_key: str, city_info: dict, out_root: str = OUT_ROOT) -> None:
    city_folder = os.path.join(out_root, city_key)
    os.makedirs(city_folder, exist_ok=True)
    min_lon, min_lat, max_lon, max_lat = city_info["bbox"]

    for data_type in DATA_TYPES:
        output_file = os.path.join(city_folder, f"{city_key}_{data_type}.geoparquet")
        if os.path.exists(output_file):
            print(f"  {data_type}: already exists, skipping")
            continue
        cmd = [
            "overturemaps", "download",
            f"--bbox={min_lon},{min_lat},{max_lon},{max_lat}",
            "-f", "geoparquet",
            f"--type={data_type}",
            "-o", output_file,
        ]
        print(f"  downloading {data_type} ...")
        subprocess.run(cmd, check=True)
        time.sleep(2)  # be gentle with the remote storage


def main():
    selected = sys.argv[1:] or list(CITIES.keys())
    for idx, city_key in enumerate(selected, 1):
        if city_key not in CITIES:
            print(f"Unknown city '{city_key}' - add it to scripts/cities.py first")
            continue
        print(f"\n[{idx}/{len(selected)}] {CITIES[city_key]['name']}")
        try:
            download_city(city_key, CITIES[city_key])
        except Exception as e:
            print(f"Error downloading {city_key}: {e}")
    print("\nDownload finished.")


if __name__ == "__main__":
    main()
