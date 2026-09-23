"""
Cross-Topic Analysis Module
Identifies and analyzes patterns spanning multiple topics
"""
import pandas as pd
from pathlib import Path


class CrossTopicAnalyzer:
    """Analyze patterns that span multiple topics"""
    
    def __init__(self, output_dir, taxonomy_level):
        self.output_dir = Path(output_dir)
        self.taxonomy_level = taxonomy_level
    
    def analyze_cross_topic_patterns(self, df, length, output_file):
        """Analyze cross-topic patterns of specific length and write to file"""
        # Get all topic columns for this length
        topic_cols = [f'topic_{i+1}' for i in range(length)]
        
        # Calculate how many different topics each row has
        df['unique_topics'] = df[topic_cols].nunique(axis=1)
        
        # Calculate total frequency of all chains at this length
        total_frequency = df['frequency'].sum()
        
        # Count distribution of different cross-topic numbers (weighted by frequency)
        cross_topic_dist = df.groupby('unique_topics')['frequency'].sum().sort_index()
        
        output_file.write(f"\nChain Length {length} Analysis:\n")
        output_file.write("-" * 50 + "\n")
        output_file.write("Cross-topic distribution:\n")
        for n_topics, freq in cross_topic_dist.items():
            percentage = (freq / total_frequency) * 100
            output_file.write(f"Chains spanning {n_topics} topics: {int(freq)} chains ({percentage:.2f}%)\n")
        
        # For each cross-topic number, find specific patterns
        for n_topics in cross_topic_dist.index:
            if n_topics > 1:  # Only focus on cross-topic cases
                cross_patterns = df[df['unique_topics'] == n_topics]
                output_file.write(f"\nSpecific patterns spanning {n_topics} topics (top 10):\n")
                # Sort by frequency, get top 10
                pattern_counts = cross_patterns.nlargest(10, 'frequency')[['ori_series', 'frequency']]
                for _, row in pattern_counts.iterrows():
                    percentage = (row['frequency'] / total_frequency) * 100
                    output_file.write(f"{row['ori_series']}: {int(row['frequency'])} times ({percentage:.2f}%)\n")
    
    def analyze_cross_topics_for_city(self, city_name):
        """Analyze cross-topic patterns for a specific city"""
        try:
            # Create output folder
            out_dir = self.output_dir / city_name
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # Set output file path
            output_path = out_dir / 'cross_topic_analysis.txt'
            
            # Read pattern analysis file
            file_path = out_dir / f'pattern_analysis_{self.taxonomy_level}.xlsx'
            
            # Open output file
            with open(output_path, 'w', encoding='utf-8') as output_file:
                # Write city name as title
                output_file.write(f"City: {city_name}\n")
                output_file.write("=" * 50 + "\n")
                
                excel_file = pd.ExcelFile(file_path)
                
                # Analyze each sheet
                for sheet_name in excel_file.sheet_names:
                    # Get chain length
                    length = int(sheet_name.split('_')[1])
                    
                    # Read data
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Analyze cross-topic patterns of this length
                    self.analyze_cross_topic_patterns(df, length, output_file)
                
            print(f"Completed analysis for {city_name}, results saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error processing {city_name}: {str(e)}")
            return False
    
    def analyze_cross_topics(self):
        """
        Analyze cross-topic patterns for all cities
        """
        print("\n" + "="*50)
        print("Step 5: Cross-Topic Pattern Analysis")
        print("="*50)
        
        # Get all city folders
        cities = [d.name for d in self.output_dir.iterdir() 
                 if d.is_dir() and d.name != 'chainPattern']
        
        # Track failed cities
        failed_cities = []
        
        # Process each city
        for city_name in cities:
            success = self.analyze_cross_topics_for_city(city_name)
            if not success:
                failed_cities.append(city_name)
        
        # Output failure list after all cities are processed
        if failed_cities:
            print("\nThe following cities failed processing:")
            print("-" * 50)
            for city in failed_cities:
                print(f"City: {city}")
            
            # Save failure list to file
            error_log_path = self.output_dir / 'processing_errors.txt'
            with open(error_log_path, 'w', encoding='utf-8') as error_file:
                error_file.write("List of cities that failed processing:\n")
                error_file.write("=" * 50 + "\n")
                for city in failed_cities:
                    error_file.write(f"City: {city}\n")
            print(f"\nError log saved to: {error_log_path}")
        
        print(f"\nCross-topic analysis completed for {len(cities) - len(failed_cities)} cities")

