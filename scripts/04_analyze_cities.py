import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))

from network_analysis import create_category_network, generate_network_report
from pattern_mining import analyze_poi_patterns_with_taxonomy
from topic_modeling import analyze_optimal_topics, analyze_poi_topics, TaxonomyMapper
import geopandas as gpd
import networkx as nx

class CityAnalyzer:
    def __init__(self, in_dir, out_dir, taxonomy_file):
        """
        Initialize city analyzer
        
        Args:
            base_dir: Base directory path containing all city folders
            taxonomy_file: Taxonomy file path
        """
        self.input_dir = in_dir
        self.out_dir = out_dir
        self.taxonomy_file = taxonomy_file
        self.taxonomy_mapper = TaxonomyMapper(taxonomy_file)
        
    def get_city_folders(self):
        """Get all city folders"""
        city_dir = self.input_dir
        return [d for d in os.listdir(city_dir) 
                if os.path.isdir(os.path.join(city_dir, d))]
    
    def get_city_geojson(self, city_name):
        """Get city GeoJSON file path"""
        results_dir = os.path.join(self.input_dir, city_name)
        geojson_files = [f for f in os.listdir(results_dir) 
                        if f.endswith('_chain.geojson')]
        if not geojson_files:
            raise FileNotFoundError(f"No geojson file found for {city_name}")
        return os.path.join(results_dir, geojson_files[0])
    
    def analyze_city(self, city_name, taxonomy_level=2):
        """Analyze single city data"""
        print(f"\n{'='*50}")
        print(f"Starting analysis for city: {city_name}")
        print(f"{'='*50}")
        
        # Set output directory
        out_dir = os.path.join(self.out_dir, city_name)
        os.makedirs(out_dir, exist_ok=True)
        
        # Get geojson file path
        geojson_file = self.get_city_geojson(city_name)
        
        try:
            # 1. Network analysis
            print("\n1. Executing network analysis...")
            original_gdf = gpd.read_file(geojson_file)
            gdf = original_gdf[original_gdf['street_subtype'] == 'road']
            category_network = create_category_network(gdf, 
                                                     self.taxonomy_mapper.category_hierarchy, 
                                                     taxonomy_level)
            
            network_report_file = os.path.join(out_dir, f'network_report_level_{taxonomy_level}.txt')
            generate_network_report(category_network, gdf, network_report_file)
            
            # Save network graph
            network_file = os.path.join(out_dir, f'category_network_level_{taxonomy_level}.graphml')
            nx.write_graphml(category_network, network_file)
            
            # 2. Pattern analysis
            print("\n2. Executing pattern analysis...")
            pattern_file = analyze_poi_patterns_with_taxonomy(
                geojson_file=geojson_file,
                taxonomy_file=self.taxonomy_file,
                taxonomy_level=taxonomy_level,
                min_length=3,
                max_length=10,
                min_freq=2,
                out_dir=out_dir
            )
            
            # # 3. Topic analysis
            # print("\n3. Executing topic analysis...")
            # # First evaluate optimal topic number
            # eval_results = analyze_optimal_topics(
            #     geojson_file=geojson_file,
            #     topic_range=range(2, 10),
            #     taxonomy_mapper=self.taxonomy_mapper,
            #     taxonomy_level=taxonomy_level,
            #     out_dir=out_dir
            # )
            
            # # Select topic number based on evaluation results (simply choose highest coherence)
            # optimal_topics = eval_results.loc[eval_results['coherence'].idxmax(), 'n_topics']
            # print(f"\nSelected optimal topic number: {optimal_topics}")
            
            optimal_topics = 6
            # Execute topic analysis
            topic_results = analyze_poi_topics(
                geojson_file=geojson_file,
                num_topics=int(optimal_topics),
                taxonomy_mapper=self.taxonomy_mapper,
                taxonomy_level=taxonomy_level,
                out_dir=out_dir
            )
            
            print(f"\n{city_name} analysis completed!")
            return True
            
        except Exception as e:
            print(f"Error analyzing {city_name}: {str(e)}")
            return False

    def analyze_all_cities(self, taxonomy_level=2):
        """Analyze all cities"""
        # Get all city folders
        all_cities = self.get_city_folders()
        
        # Filter valid cities (cities with required geojson files)
        valid_cities = []
        for city in all_cities:
            try:
                self.get_city_geojson(city)  # Test if geojson file can be obtained
                valid_cities.append(city)
            except FileNotFoundError:
                print(f"Skipping {city}: required geojson file not found")
                continue
        
        results = {}
        
        # Only process valid cities
        for city in valid_cities:
            success = self.analyze_city(city, taxonomy_level)
            results[city] = success
        
        # Print summary report
        print("\nAnalysis Summary:")
        print("=" * 50)
        print(f"Total cities: {len(all_cities)}")
        print(f"Valid cities: {len(valid_cities)}")
        print(f"Skipped cities: {len(all_cities) - len(valid_cities)}")
        print("\nProcessing results for each city:")
        for city, success in results.items():
            status = "Success" if success else "Failed"
            print(f"{city}: {status}")

def main():
    # Set base paths and taxonomy file path
    base_dir = 'data/output/chainRawData'
    out_dir = 'data/output/chainAnalysisData'
    taxonomy_file = 'data/input/overture_categories.csv'
    
    # Create analyzer instance
    analyzer = CityAnalyzer(base_dir, out_dir, taxonomy_file)
    
    # Analyze all cities
    analyzer.analyze_all_cities(taxonomy_level=2)

if __name__ == "__main__":
    main()