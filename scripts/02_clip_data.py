import geopandas as gpd
from shapely.geometry import box
import os
from pathlib import Path
import sys
from typing import Tuple

sys.path.append(str(Path(__file__).parent))
from cities import CITIES

class ChainDataClipper:
    def __init__(self, in_dir: str, out_dir: str):
        # City list with predefined bounding boxes
        # bbox format: (min_lon, min_lat, max_lon, max_lat)
        self.cities = CITIES

        # Create output directory
        self.in_dir = in_dir
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
    
    def create_bbox(self, bbox_coords: Tuple[float, float, float, float]) -> box:
        """Create shapely box object from bounding box coordinates"""
        min_lon, min_lat, max_lon, max_lat = bbox_coords
        return box(min_lon, min_lat, max_lon, max_lat)
    
    def clip_city_data(self, city_key: str):
        """Clip data for single city"""
        city_info = self.cities[city_key]
        bbox = self.create_bbox(city_info['bbox'])
        
        # Set input and output paths
        input_dir = os.path.join(self.in_dir, city_key)
        output_dir = os.path.join(self.out_dir, city_key)
        os.makedirs(output_dir, exist_ok=True)
        
        # Process geoparquet file
        geoparquet_path = os.path.join(input_dir, f"{city_key}_segment.geoparquet")
        if os.path.exists(geoparquet_path):
            try:
                # Read GeoParquet file
                gdf = gpd.read_parquet(geoparquet_path)
                gdf = gpd.GeoDataFrame(gdf).to_crs(epsg=4326)
                
                # Keep only road subtype data
                gdf = gdf[gdf['subtype'] == 'road']
                
                # Use intersects to filter data
                mask = gdf.geometry.intersects(bbox)
                clipped_gdf = gdf[mask].copy()
                
                # Then use clip to precisely clip intersecting segments
                clipped_gdf.geometry = clipped_gdf.geometry.clip(bbox)
                
                # Keep only specified columns
                columns_to_keep = ['id', 'subtype', 'class', 'geometry']
                clipped_gdf = clipped_gdf[columns_to_keep]
                
                # Save clipped file
                clipped_parquet_path = os.path.join(output_dir, f"{city_key}_segments_clipped.geoparquet")
                
                clipped_gdf.to_parquet(clipped_parquet_path)
                
                print(f"Successfully clipped data for {city_info['name']}")
                print(f"Original features: {len(gdf)}")
                print(f"Clipped features: {len(clipped_gdf)}")
                
            except Exception as e:
                print(f"Error processing {city_key}: {str(e)}")
        else:
            print(f"No data found for {city_key}")
    
    def process_all_cities(self):
        """Process all cities that have downloaded data"""
        for city_key in self.cities.keys():
            if not os.path.isdir(os.path.join(self.in_dir, city_key)):
                continue
            print(f"\nProcessing {city_key}...")
            self.clip_city_data(city_key)

def main():
    in_dir = "data/input/city"
    out_dir = "data/input/city"
    clipper = ChainDataClipper(in_dir, out_dir)
    clipper.process_all_cities()

if __name__ == "__main__":
    main()