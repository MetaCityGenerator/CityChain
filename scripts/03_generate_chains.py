import ast
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, MultiPoint, MultiLineString, LineString
import time
from typing import Dict, Tuple, List
import numpy as np

class POIChainProcessor:
    """POI Chain Processor Class"""
    
    BUFFER_WIDTHS = {
        'motorway': 200,
        'trunk': 150,
        'primary': 100,
        'secondary': 75,
        'tertiary': 50,
        'residential': 25,
        'living_street': 15,
        'service': 30,
        'pedestrian': 15
    }
    DEFAULT_BUFFER = 50

    def __init__(self, cities_root: str, out_dir:str):
        """
        Initialize processor
        Args:
            cities_root: Root directory for city data
        """
        self.cities_root = cities_root
        self.out_dir = out_dir
        self.start_time = time.time()

    def time_count(self, process_name: str) -> None:
        """Timer for tracking processing time"""
        elapsed_time = round(time.time() - self.start_time, 2)
        print(f"{process_name}: {elapsed_time} s")

    def load_city_data(self, city_folder: str, city_name: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
        """Load city data"""
        place_file = os.path.join(city_folder, f"{city_name}_place.geoparquet")
        segment_file = os.path.join(city_folder, f"{city_name}_segments_clipped.geoparquet")
        if os.path.exists(segment_file) and os.path.exists(place_file):
            places_gdf = gpd.read_parquet(place_file)
            segments_gdf = gpd.read_parquet(segment_file)
        else:
            raise FileNotFoundError(f"File does not exist: {place_file} or {segment_file}")
        # Project to the local UTM zone so buffer widths are in true metres
        # (the zone is estimated from the city's extent).
        utm_crs = segments_gdf.to_crs(epsg=4326).estimate_utm_crs()
        print(f"Projecting {city_name} to {utm_crs.to_string()}")
        places_gdf = places_gdf.to_crs(utm_crs)
        segments_gdf = segments_gdf.to_crs(utm_crs)
        
        # Process names dictionary
        def extract_names(names_dict):
            if pd.isna(names_dict):
                return {'primary': 'Null', 'common': 'Null', 'rules': 'Null'}
            try:
                names_dict = ast.literal_eval(names_dict) if isinstance(names_dict, str) else names_dict
                return {
                    'primary': names_dict.get('primary', 'Null'),
                    'common': names_dict.get('common', 'Null'),
                    'rules': names_dict.get('rules', 'Null')
                }
            except:
                return {'primary': 'Null', 'common': 'Null', 'rules': 'Null'}

        # Process categories dictionary
        def extract_categories(categories_dict):
            if pd.isna(categories_dict):
                return {'primary': 'Null', 'alternate': 'Null'}
            try:
                categories_dict = ast.literal_eval(categories_dict) if isinstance(categories_dict, str) else categories_dict
                alternate = categories_dict.get('alternate', [])
                if alternate:
                    alternate = '|'.join(alternate) if isinstance(alternate, list) else str(alternate)
                else:
                    alternate = 'Null'
                return {
                    'primary': categories_dict.get('primary', 'Null'),
                    'alternate': alternate
                }
            except:
                return {'primary': 'Null', 'alternate': 'Null'}

        # Expand names dictionary to new columns
        places_names_expanded = places_gdf['names'].apply(extract_names).apply(pd.Series)
        places_gdf['names_primary'] = places_names_expanded['primary']
        places_gdf['names_common'] = places_names_expanded['common']
        places_gdf['names_rules'] = places_names_expanded['rules']

        # Expand segments_gdf names dictionary to new columns (commented out)
        # segments_names_expanded = segments_gdf['names'].apply(extract_names).apply(pd.Series)
        # segments_gdf['names_primary'] = segments_names_expanded['primary']
        # segments_gdf['names_common'] = segments_names_expanded['common']
        # segments_gdf['names_rules'] = segments_names_expanded['rules']

        # places_gdf['names_primary'] = places_gdf['names.primary'].fillna('Null')
        # places_gdf['names_common'] = places_gdf['names.common'].fillna('Null')
        # places_gdf['names_rules'] = places_gdf['names.rules'].fillna('Null')

        # Expand categories dictionary to new columns
        places_categories_expanded = places_gdf['categories'].apply(extract_categories).apply(pd.Series)
        places_gdf['categories_primary'] = places_categories_expanded['primary']
        places_gdf['categories_alternate'] = places_categories_expanded['alternate']

        # places_gdf['categories_primary'] = places_gdf['categories.primary'].fillna('Null')
        # Special handling for categories.alternate array, only take first value
        def process_alternate(alt):
            # If is nan or None
            if isinstance(alt, (float, type(None))) and pd.isna(alt):
                return 'Null'
            
            # If is numpy array
            if isinstance(alt, np.ndarray):
                if alt.size > 0:
                    # Get first element value directly, remove array brackets
                    return str(alt[0]).strip("[]'\"")
                return 'Null'
            
            # If is Python list
            if isinstance(alt, list):
                if len(alt) > 0:
                    # Get first element value directly, remove array brackets
                    return str(alt[0]).strip("[]'\"")
                return 'Null'
            
            # Other cases, remove all possible array brackets and quotes
            return str(alt).strip("[]'\"")
        
        places_gdf['categories_alternate'] = places_gdf['categories_alternate'].apply(process_alternate)
        # places_gdf.to_csv('places_gdf.csv', index=False)
        self.time_count('Data loading completed')
        return places_gdf, segments_gdf


    def create_road_buffers(self, segments_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Create road buffers"""
        segments_gdf['buffer_width'] = segments_gdf['class'].map(
            lambda x: self.BUFFER_WIDTHS.get(x, self.DEFAULT_BUFFER)
        )
        
        # Use vectorized operations instead of apply
        segments_gdf['buffer_geometry'] = segments_gdf.geometry.buffer(
            segments_gdf['buffer_width']
        )
        
        buffer_gdf = gpd.GeoDataFrame(
            segments_gdf,
            geometry='buffer_geometry',
            crs=segments_gdf.crs
        )
        
        self.time_count('Buffer creation completed')
        return buffer_gdf
            

    @staticmethod
    def project_point_to_line(point: Point, line: LineString) -> Tuple[float, float]:
        """Calculate point projection position on line"""
        try:
            line_len = line.length
            proj_point = line.interpolate(line.project(point))
            line_pct = line.project(proj_point) / line_len
            return line_len, line_pct
        except Exception as e:
            raise Exception(f"Projection calculation failed: {str(e)}")

    def process_spatial_join(self, places_gdf: gpd.GeoDataFrame, 
                            buffer_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        # First create a base dataframe containing all roads
        all_roads = buffer_gdf[['id', 'class', 'subtype', 'geometry']].copy()
        all_roads.columns = ['id_right', 'class', 'subtype', 'geometry_right']
        
        """Process spatial join"""
        # Changed op='within' to predicate='within'
        poi_with_buffer = gpd.sjoin(places_gdf, buffer_gdf, predicate='within')

        # Calculate projection positions for roads with POIs
        if not poi_with_buffer.empty:
            poi_with_buffer[['road_len', 'road_pct']] = poi_with_buffer.apply(
                lambda row: pd.Series(self.project_point_to_line(
                    row['geometry'],
                    row['geometry_right']
                )),
                axis=1
            )
        
        # # Filter endpoint POIs
        # poi_with_buffer = poi_with_buffer[
        #     ~poi_with_buffer['road_pct'].isin([0, 1])
        # ]
        
        self.time_count('Spatial join completed')
        return poi_with_buffer, all_roads
            

    def aggregate_road_data(self, poi_with_buffer: gpd.GeoDataFrame, all_roads: gpd.GeoDataFrame) -> pd.DataFrame:
        """Aggregate road data"""
        def concat_ordered(x: pd.Series, separator: str='|') -> str:
            # Keep every POI (including repeated categories) in street order
            return separator.join(x.fillna('Null').astype(str))

        if not poi_with_buffer.empty:
            # Drop POIs without a primary category - they carry no functional information
            poi_with_buffer = poi_with_buffer[poi_with_buffer['categories_primary'] != 'Null']
            if poi_with_buffer.empty:
                return None
            # Order POIs along each street by their projected position (0 = start, 1 = end)
            poi_with_buffer = poi_with_buffer.sort_values(['id_right', 'road_pct'], kind='mergesort')
            grouped = poi_with_buffer.groupby('id_right', sort=False).agg({
                'names_primary': concat_ordered,
                'names_common': concat_ordered,
                'names_rules': concat_ordered,
                'categories_primary': concat_ordered,
                'categories_alternate': concat_ordered,
                'road_len': 'first',
                'class': 'first',
                'subtype': 'first',
                'geometry_right': 'first'
            }).reset_index()
            
            road_data = pd.DataFrame({
                'street_id': grouped['id_right'],
                'names_primary_chain': grouped['names_primary'],
                'names_common_chain': grouped['names_common'],
                'names_rules_chain': grouped['names_rules'],
                'categories_primary_chain': grouped['categories_primary'],
                'categories_alternate_chain': grouped['categories_alternate'],
                'street_length': grouped['road_len'],
                'street_class': grouped['class'],
                'street_subtype': grouped['subtype'],
                'geometry': grouped['geometry_right']
            })
        else:
            return None
            # Create empty DataFrame but include all necessary columns
            # road_data = pd.DataFrame(columns=[
            #     'street_id', 'names_primary_chain', 'names_common_chain', 
            #     'names_rules_chain', 'categories_primary_chain', 
            #     'categories_alternate_chain', 'street_length', 'street_class',
            #     'street_subtype', 'geometry'
            # ])

        # # Add roads without POIs
        # roads_without_poi = all_roads[~all_roads['id_right'].isin(road_data['street_id'])]
        # if not roads_without_poi.empty:
        #     no_poi_data = pd.DataFrame({
        #         'street_id': roads_without_poi['id_right'],
        #         'names_primary_chain': '',
        #         'names_common_chain': '',
        #         'names_rules_chain': '',
        #         'categories_primary_chain': '',
        #         'categories_alternate_chain': '',
        #         'street_length': roads_without_poi.geometry_right.length,
        #         'street_class': roads_without_poi['class'],
        #         'street_subtype': roads_without_poi['subtype'],
        #         'geometry': roads_without_poi['geometry_right']
        #     })
        #     road_data = pd.concat([road_data, no_poi_data], ignore_index=True)
        
        self.time_count('Data aggregation completed')
        return road_data

    def save_results(self, road_gdf: gpd.GeoDataFrame, output_path: str) -> None:
        """Save processing results"""
        
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        # Convert to EPSG:4326 coordinate system
        road_gdf_4326 = road_gdf.to_crs(epsg=4326)
        
        # Save CSV (without geometry information)
        road_gdf_4326.drop(columns=['geometry']).to_csv(
            f"{output_path}.csv",
            index=False
        )
        
        # Save GeoJSON (WGS84 coordinate system)
        road_gdf_4326.to_file(
            f"{output_path}.geojson", 
            driver='GeoJSON'
        )
        
        self.time_count('Results saving completed')

    def process_city(self, city_name: str) -> None:
        """Process single city"""
        print(f"\nStarting to process city: {city_name}")
        self.start_time = time.time()
        
        # Load data
        places_gdf, segments_gdf = self.load_city_data(
            os.path.join(self.cities_root, city_name), 
            city_name
        )
        
        # If data loading fails, return directly
        if places_gdf is None or segments_gdf is None:
            return
            
        try:
            # Continue processing...
            city_folder = os.path.join(self.cities_root, city_name)
            out_folder = os.path.join(self.out_dir, city_name)
            os.makedirs(out_folder, exist_ok=True)

            # Create buffers
            buffer_gdf = self.create_road_buffers(segments_gdf)
            # Spatial join
            poi_with_buffer, all_roads = self.process_spatial_join(places_gdf, buffer_gdf)
            # Data aggregation
            road_df = self.aggregate_road_data(poi_with_buffer, all_roads)
            
            # Add data statistics
            print(f"Original road count: {len(segments_gdf)}")
            print(f"Processed road count: {len(road_df)}")
            
            # Convert to GeoDataFrame and save
            road_gdf = gpd.GeoDataFrame(
                road_df,
                geometry='geometry',
                crs=segments_gdf.crs
            )
            
            output_path = os.path.join(
                out_folder,
                f"{city_name}_road_text_chain"
            )
            self.save_results(road_gdf, output_path)
            
            print(f"City {city_name} processing completed")
            
        except Exception as e:
            print(f"Error processing city {city_name}: {str(e)}")
            return
            
    def process_all_cities(self):
        """Process all cities"""
        cities = [d for d in os.listdir(self.cities_root) 
                if os.path.isdir(os.path.join(self.cities_root, d))]
        
        processed = 0
        skipped = 0
        failed = 0
        
        for city_name in cities:
            try:
                self.process_city(city_name)
                processed += 1
            except Exception as e:
                print(f"Error processing {city_name}: {str(e)}")
                failed += 1
                continue
        
        print("\nProcessing Summary:")
        print("=" * 50)
        print(f"Total cities: {len(cities)}")
        print(f"Successfully processed: {processed}")
        print(f"Skipped cities: {skipped}")
        print(f"Failed: {failed}")

if __name__ == "__main__":
    CITIES_ROOT = "data/input/city"
    OUT_DIR = "data/output/chainRawData"  
    processor = POIChainProcessor(CITIES_ROOT, OUT_DIR)
    processor.process_all_cities()