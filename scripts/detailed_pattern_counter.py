"""
Pattern Counting Module
Extracts pattern counts and frequencies from analysis files
"""
import pandas as pd
import os
import re
from pathlib import Path


class PatternCounter:
    """Extract and count patterns from analysis files"""
    
    def __init__(self, chain_analysis_dir, output_dir, taxonomy_level):
        self.chain_analysis_dir = Path(chain_analysis_dir)
        self.output_dir = Path(output_dir)
        self.taxonomy_level = taxonomy_level
    
    def extract_pattern_info(self, file_path):
        """
        Extract pattern length, pattern count, and total frequency from file
        Returns two dictionaries:
        1. {length: pattern_count}
        2. {length: total_frequency}
        """
        pattern_counts = {}
        frequency_counts = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split into different length sections
            length_sections = content.split('Pattern Analysis for Length')
            
            for section in length_sections[1:]:  # Skip first empty part
                # Extract length
                length_match = re.search(r'(\d+)', section)
                if length_match:
                    length = int(length_match.group(1))
                    
                    # Extract pattern count
                    count_match = re.search(r'Found\s+(\d+)\s+patterns', section)
                    if count_match:
                        pattern_counts[length] = int(count_match.group(1))
                    
                    # Extract all frequency data
                    frequency_matches = re.finditer(r'appears in\s+(\d+)\s+chains', section)
                    total_frequency = 0
                    for freq_match in frequency_matches:
                        frequency = int(freq_match.group(1))
                        total_frequency += frequency
                    
                    frequency_counts[length] = total_frequency
                    
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            
        return pattern_counts, frequency_counts
    
    def process_pattern_counts(self):
        """
        Process pattern counts for all cities
        Returns two DataFrames: pattern counts and frequency counts
        """
        print("\n" + "="*50)
        print("Step 1: Pattern Counting")
        print("="*50)
        
        city_pattern_data = {}
        city_frequency_data = {}
        all_lengths = set()
        
        # Traverse all city folders
        for city in os.listdir(self.chain_analysis_dir):
            city_path = self.chain_analysis_dir / city
            if city_path.is_dir():
                file_path = city_path / f'poi_pattern_analysis_level_{self.taxonomy_level}.txt'
                
                if file_path.exists():
                    pattern_counts, frequency_counts = self.extract_pattern_info(file_path)
                    city_pattern_data[city] = pattern_counts
                    city_frequency_data[city] = frequency_counts
                    all_lengths.update(pattern_counts.keys())
        
        # Create DataFrames
        df_patterns = pd.DataFrame(city_pattern_data).T
        df_frequencies = pd.DataFrame(city_frequency_data).T
        
        # Ensure all lengths are included and rename columns
        sorted_lengths = sorted(all_lengths)
        df_patterns = df_patterns.reindex(columns=sorted_lengths)
        df_frequencies = df_frequencies.reindex(columns=sorted_lengths)
        
        # Rename columns to chain_X format
        new_columns = [f'chain_{length}' for length in sorted_lengths]
        df_patterns.columns = new_columns
        df_frequencies.columns = new_columns
        
        df_patterns = df_patterns.fillna(0).astype(int)
        df_frequencies = df_frequencies.fillna(0).astype(int)
        
        # Save results
        pattern_dir = self.output_dir / 'chainPattern'
        pattern_dir.mkdir(exist_ok=True)
        
        df_patterns.to_csv(pattern_dir / 'pattern_counts.csv')
        df_frequencies.to_csv(pattern_dir / 'frequency_counts.csv')
        
        print(f"Pattern counts saved to: {pattern_dir / 'pattern_counts.csv'}")
        print(f"Frequency counts saved to: {pattern_dir / 'frequency_counts.csv'}")
        
        return df_patterns, df_frequencies

