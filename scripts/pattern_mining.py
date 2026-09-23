import json
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from datetime import datetime
import csv
import ast
import os

class TaxonomyMapper:
    def __init__(self, taxonomy_file: str):
        self.category_hierarchy = {}
        self.load_taxonomy(taxonomy_file)
        
    def load_taxonomy(self, filepath: str):
        """Load taxonomy hierarchy"""
        with open(filepath, 'r', encoding='utf-8') as f:
            # Skip header line
            next(f)
            for line in f:
                if ';' in line:
                    category, taxonomy = line.strip().split(';')
                    category = category.strip()
                    # Convert string to list, process taxonomy string
                    taxonomy = taxonomy.strip()
                    # Remove brackets and split string
                    taxonomy = taxonomy.strip('[]').split(',')
                    # Clean each element
                    taxonomy = [item.strip() for item in taxonomy]
                    self.category_hierarchy[category] = taxonomy
    
    def get_level_category(self, category: str, level: int) -> str:
        """Get category name at specified level"""
        if category not in self.category_hierarchy:
            return category
            
        hierarchy = self.category_hierarchy[category]
        if level <= len(hierarchy):
            return hierarchy[level - 1]
        return hierarchy[-1]

class GeoJSONPOIAnalyzer:
    def __init__(self, taxonomy_mapper: TaxonomyMapper, min_frequency=2, taxonomy_level=1):
        self.min_frequency = min_frequency
        self.taxonomy_mapper = taxonomy_mapper
        self.taxonomy_level = taxonomy_level
        
    def load_geojson(self, filepath: str) -> dict:
        """Load and parse GeoJSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def extract_poi_chains(self, geojson_data: dict) -> tuple[list[str], list[str]]:
        """Extract all POI chains from GeoJSON, map to specified level, and save street_id"""
        poi_chains = []
        street_ids = []  # Save street_id
        
        if geojson_data['type'] == 'FeatureCollection':
            features = geojson_data['features']
        else:
            features = [geojson_data]
            
        for feature in features:
            if 'properties' in feature and 'categories_primary_chain' in feature['properties']:
                chain = feature['properties']['categories_primary_chain']
                if isinstance(chain, str):
                    # Map each POI to specified level
                    mapped_chain = self.map_chain_to_level(chain)
                    poi_chains.append(mapped_chain)
                    # Save street_id, use 'unknown' if not exists
                    street_id = feature['properties'].get('street_id', 'unknown')
                    street_ids.append(street_id)
                    
        return poi_chains, street_ids
    
    def map_chain_to_level(self, chain: str) -> str:
        """Map each category in POI chain to specified level"""
        categories = chain.split('|')
        mapped_categories = [
            self.taxonomy_mapper.get_level_category(cat, self.taxonomy_level)
            for cat in categories
        ]
        return '|'.join(mapped_categories)
        
    def find_patterns_by_length(self, poi_chains: List[str], street_ids: List[str], pattern_length: int) -> Dict[Tuple, Dict[int, tuple[List[int], str]]]:
        """Find patterns of specific length and save corresponding street_id"""
        processed_chains = [chain.split('|') for chain in poi_chains]
        patterns = defaultdict(lambda: defaultdict(lambda: ([], None)))  # Modified default value type
        
        for chain_idx, (chain, street_id) in enumerate(zip(processed_chains, street_ids)):
            n = len(chain)
            if n >= pattern_length:
                for i in range(n - pattern_length + 1):
                    pattern = tuple(chain[i:i+pattern_length])
                    positions, _ = patterns[pattern][chain_idx]
                    positions.append(i)
                    patterns[pattern][chain_idx] = (positions, street_id)  # Save positions and street_id
                    
        # Filter frequent patterns
        frequent_patterns = {
            pattern: positions 
            for pattern, positions in patterns.items() 
            if len(positions) >= self.min_frequency
        }
        
        return frequent_patterns

    def analyze_pattern_statistics(self, patterns: Dict[Tuple, Dict[int, List[int]]], total_chains: int) -> List[dict]:
        """Analyze pattern statistics"""
        stats = []
        for pattern, positions in patterns.items():
            stats.append({
                'pattern': ' -> '.join(pattern),
                'length': len(pattern),
                'frequency': len(positions),
                'coverage': len(positions) / total_chains * 100,
                'total_occurrences': sum(len(pos) for pos in positions.values()),
                'avg_occurrences_per_chain': sum(len(pos) for pos in positions.values()) / len(positions),
                'chains': positions
            })
        
        return sorted(stats, key=lambda x: (-x['frequency'], -x['length'], -x['total_occurrences']))

def analyze_poi_patterns_with_taxonomy(
    geojson_file: str,
    taxonomy_file: str,
    taxonomy_level: int,
    min_length: int = 3,
    max_length: int = 10,
    min_freq: int = 2,
    out_dir: str = None
):
    """Main analysis function"""
    output_file = os.path.join(out_dir, f'poi_pattern_analysis_level_{taxonomy_level}.txt')
    
    # Initialize taxonomy mapper
    taxonomy_mapper = TaxonomyMapper(taxonomy_file)
    
    # Initialize analyzer
    analyzer = GeoJSONPOIAnalyzer(
        taxonomy_mapper=taxonomy_mapper,
        min_frequency=min_freq,
        taxonomy_level=taxonomy_level
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("POI Chain Pattern Analysis Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Analysis Parameters:\n")
        f.write(f"- Taxonomy Level: {taxonomy_level}\n")
        f.write(f"- Minimum Pattern Length: {min_length}\n")
        f.write(f"- Maximum Pattern Length: {max_length}\n")
        f.write(f"- Minimum Frequency: {min_freq}\n\n")
        
        # Load and process data
        f.write("Loading data...\n")
        geojson_data = analyzer.load_geojson(geojson_file)
        poi_chains, street_ids = analyzer.extract_poi_chains(geojson_data)
        
        # Save mapped chain examples
        f.write("\nMapped POI Chain Examples (first 5):\n")
        for i, chain in enumerate(poi_chains[:5]):
            f.write(f"{i+1}. {chain}\n")
        
        total_chains = len(poi_chains)
        f.write(f"\nTotal {total_chains} POI chains found and processed\n\n")
        
        # Analyze patterns for each length
        for length in range(min_length, max_length + 1):
            f.write(f"\nPattern Analysis for Length {length}\n")
            f.write("-" * 50 + "\n")
            
            patterns = analyzer.find_patterns_by_length(poi_chains, street_ids, length)
            
            if not patterns:
                f.write(f"No repeated patterns of length {length} found\n")
                continue
                
            stats = analyzer.analyze_pattern_statistics(patterns, total_chains)
            
            f.write(f"Found {len(patterns)} patterns:\n\n")
            
            for idx, stat in enumerate(stats, 1):
                f.write(f"Pattern {idx}:\n")
                f.write(f"Sequence: {stat['pattern']}\n")
                f.write(f"Frequency: appears in {stat['frequency']} chains\n")
                f.write(f"Coverage: {stat['coverage']:.2f}%\n")
                f.write(f"Total Occurrences: {stat['total_occurrences']}\n")
                f.write("Positions:\n")
                for chain_idx, (positions, street_id) in stat['chains'].items():
                    f.write(f"  Chain {chain_idx + 1} (street_id: {street_id}): positions {positions}\n")
                f.write("\n")
    
    print(f"Analysis results saved to: {output_file}")
    return output_file

# Usage example
if __name__ == "__main__":
    # Taxonomy file format:
    # Category code; Overture Taxonomy
    # eat_and_drink; [eat_and_drink]
    # restaurant; [eat_and_drink,restaurant]
    # ...
    
    os.makedirs('data/output/chainAnalysisData/amsterdam', exist_ok=True)
    output_file = analyze_poi_patterns_with_taxonomy(
        geojson_file='data/output/chainRawData/amsterdam/amsterdam_road_text_chain.geojson',
        taxonomy_file='data/input/overture_categories.csv',
        taxonomy_level=2,  # Use level 2
        min_length=3,
        max_length=8,
        min_freq=2,
        out_dir='data/output/chainAnalysisData/amsterdam'
    )