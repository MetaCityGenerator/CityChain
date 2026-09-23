"""
Pattern Decoding Module
Maps POI patterns to topics using LDA model
"""
import pandas as pd
import os
import re
import multiprocessing as mp
from functools import partial
import time
from pathlib import Path
import gensim


class PatternDecoder:
    """Decode patterns and map them to topics"""
    
    def __init__(self, chain_analysis_dir, output_dir, taxonomy_level):
        self.chain_analysis_dir = Path(chain_analysis_dir)
        self.output_dir = Path(output_dir)
        self.taxonomy_level = taxonomy_level
    
    def extract_patterns_from_txt(self, file_path):
        """Extract pattern information from text file"""
        patterns = []
        current_length = None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check if it's a length marker line
            if 'Pattern Analysis for Length' in line:
                current_length = int(re.search(r'Length (\d+)', line).group(1))
                i += 1
                continue
                
            # Check if it's a pattern line
            if line.startswith('Sequence:'):
                pattern = re.search(r'Sequence: (.+)', line).group(1).strip()
                # Get frequency line
                freq_line = lines[i + 1]
                frequency = int(re.search(r'appears in (\d+)', freq_line).group(1))
                # Get coverage line
                coverage_line = lines[i + 2]
                coverage = float(re.search(r'Coverage: ([\d.]+)%', coverage_line).group(1))
                
                patterns.append({
                    'length': current_length,
                    'ori_series': pattern,
                    'frequency': frequency,
                    'coverage': coverage
                })
                
                i += 3  # Skip processed frequency and coverage lines
            else:
                i += 1
        
        return patterns
    
    def process_length_group(self, length_group_df, term_topic_map):
        """Process pattern group of specific length"""
        # Split sequences into individual terms
        terms_series = length_group_df['ori_series'].str.split(' -> ')
        
        # Create a function to map terms to topics
        def map_terms_to_topics(terms):
            return [str(term_topic_map.get(term, ('-1', 0))[0]) for term in terms]
        
        # Vectorized processing of all sequences
        topics_list = terms_series.apply(map_terms_to_topics)
        
        # Add remapped sequence
        length_group_df['remap_series'] = topics_list.apply(lambda x: ' -> '.join(f'Topic{topic}' for topic in x))
        
        # Add topic for each position
        max_length = len(topics_list.iloc[0])
        for i in range(max_length):
            length_group_df[f'topic_{i+1}'] = topics_list.apply(lambda x: int(x[i]))
        
        return length_group_df
    
    def ensure_complete_topic_terms(self, model_path, taxonomy_level):
        """Ensure complete topic terms file exists, regenerate from model if not"""
        
        # Define file path
        topic_terms_file = model_path.parent / f'topicmodelling_{taxonomy_level}' / f'poi_topic_analysis_topic_terms_{taxonomy_level}.csv'
        
        # If file exists, return file path directly
        if topic_terms_file.exists():
            df = pd.read_csv(topic_terms_file)
            # Can add validation logic to ensure file content is complete
            if len(df) > 100:  # Assume we expect at least 100 terms
                print(f"Using existing topic terms file: {topic_terms_file}")
                return topic_terms_file
        
        print(f"Need to regenerate topic terms file...")
        
        # Load LDA model
        model_prefix = model_path / f'lda_model_poi_topic_analysis_{taxonomy_level}'
        if not (Path(str(model_prefix) + '.state')).exists():
            raise FileNotFoundError(f"Cannot find model file: {model_prefix}")
        
        lda_model = gensim.models.LdaModel.load(str(model_prefix))
        
        # Get dictionary
        dictionary = gensim.corpora.Dictionary.load(str(model_prefix) + '.id2word')
        
        # Generate complete topic terms data
        topic_terms = []
        for topic_id in range(lda_model.num_topics):
            # Get distribution of all words under this topic
            topic_dist = lda_model.get_topic_terms(topic_id, topn=len(dictionary))
            for term_id, probability in topic_dist:
                term = dictionary[term_id]
                topic_terms.append({
                    'topic': topic_id+1,
                    'term': term,
                    'probability': probability
                })
        
        # Convert to DataFrame and save
        topic_df = pd.DataFrame(topic_terms)
        topic_df.to_csv(topic_terms_file, index=False)
        print(f"Generated new topic terms file: {topic_terms_file}")
        
        return topic_terms_file
    
    def save_pattern_analysis(self, results, length_groups, out_dir, taxonomy_level):
        """Save original pattern analysis results"""
        t1 = time.time()
        output_file = out_dir / f'pattern_analysis_{taxonomy_level}.xlsx'
        
        with pd.ExcelWriter(output_file) as writer:
            for length_df, (length, _) in zip(results, length_groups.items()):
                pattern_columns = ['ori_series', 'frequency', 'coverage', 'remap_series'] + \
                                [f'topic_{i}' for i in range(1, length + 1)]
                pattern_df = length_df[pattern_columns]
                pattern_df.to_excel(writer, sheet_name=f'Length_{length}', index=False)
        
        print(f"Pattern analysis results saved: {output_file} (Time: {time.time() - t1:.2f}s)")
        return output_file
    
    def save_topic_analysis(self, poi_frequency_analysis, out_dir, taxonomy_level):
        """Save POI topic analysis results"""
        t1 = time.time()
        
        # Get all chain lengths that appear
        all_lengths = sorted(set(
            length 
            for data in poi_frequency_analysis.values() 
            for length in data['by_length'].keys()
        ))
        
        # Create POI analysis data
        poi_analysis_rows = []
        for poi, data in poi_frequency_analysis.items():
            row = {
                'POI': poi,
                'Topic': data['topic'],
                'Total_Frequency': data['total_frequency']
            }
            # Add frequency column for each length
            for length in all_lengths:
                row[f'Length_{length}'] = data['by_length'].get(length, 0)
            
            poi_analysis_rows.append(row)
        
        # Group POI frequency statistics by Topic
        topic_poi_analysis = {}
        for row in poi_analysis_rows:
            topic = row['Topic']
            if topic not in topic_poi_analysis:
                topic_poi_analysis[topic] = []
            topic_poi_analysis[topic].append(row)
        
        # Create output file
        output_file = out_dir / f'topic_analysis_{taxonomy_level}.xlsx'
        
        with pd.ExcelWriter(output_file) as writer:
            # 1. POI overall analysis table
            poi_analysis_df = pd.DataFrame(poi_analysis_rows)
            columns = ['POI', 'Topic', 'Total_Frequency'] + [f'Length_{length}' for length in all_lengths]
            poi_analysis_df = poi_analysis_df[columns]
            poi_analysis_df = poi_analysis_df.sort_values('Total_Frequency', ascending=False)
            poi_analysis_df.to_excel(writer, sheet_name='POI_Analysis', index=False)
            
            # 2. Top POIs analysis table for each Topic
            for topic, pois in topic_poi_analysis.items():
                top_pois = sorted(pois, key=lambda x: x['Total_Frequency'], reverse=True)[:10]
                topic_df = pd.DataFrame(top_pois)
                topic_df = topic_df[columns]
                topic_df.to_excel(writer, sheet_name=f'Topic_{topic}_Top10', index=False)
        
        print(f"Topic analysis results saved: {output_file} (Time: {time.time() - t1:.2f}s)")
        return output_file
    
    def process_city_decoding(self, city_name):
        """Process data decoding for each city"""
        print(f"\nProcessing city: {city_name}")
        start_time = time.time()
        
        # Set input/output paths
        base_path = self.chain_analysis_dir / city_name
        out_dir = self.output_dir / city_name
        out_dir.mkdir(exist_ok=True)
        
        # Build file paths
        pattern_file = base_path / f'poi_pattern_analysis_level_{self.taxonomy_level}.txt'
        topic_file = base_path / f'topicmodelling_{self.taxonomy_level}' / f'poi_topic_analysis_topic_terms_{self.taxonomy_level}.csv'
        
        # Check if necessary files exist
        if not pattern_file.exists():
            print(f"Warning: Pattern file does not exist for {city_name}: {pattern_file}")
            return None, None
            
        if not topic_file.exists():
            print(f"Warning: Topic file does not exist for {city_name}: {topic_file}")
            return None, None
        
        try:
            # Ensure complete topic terms file
            t1 = time.time()
            model_path = base_path / f'models_{self.taxonomy_level}'
            complete_topic_file = self.ensure_complete_topic_terms(model_path, self.taxonomy_level)
            print(f"Ensured topic terms completeness (Time: {time.time() - t1:.2f}s)")
            
            # Read pattern data
            t1 = time.time()
            patterns = self.extract_patterns_from_txt(pattern_file)
            patterns_df = pd.DataFrame(patterns)
            print(f"Found {len(patterns)} patterns (Time: {time.time() - t1:.2f}s)")
            
            # Read topic data and create mapping dictionary
            t1 = time.time()
            topic_df = pd.read_csv(complete_topic_file)
            print(f"Found {len(topic_df)} topic terms (Time: {time.time() - t1:.2f}s)")
            
            # Create term-to-topic mapping dictionary
            t1 = time.time()
            term_topic_map = {}
            for _, row in topic_df.iterrows():
                term = row['term']
                topic = row['topic']
                prob = row['probability']
                if term not in term_topic_map or prob > term_topic_map[term][1]:
                    term_topic_map[term] = (topic, prob)
            print(f"Created mapping dictionary (Time: {time.time() - t1:.2f}s)")
            
            # Group by length
            t1 = time.time()
            length_groups = dict(tuple(patterns_df.groupby('length')))
            print(f"Grouped by length, {len(length_groups)} different lengths (Time: {time.time() - t1:.2f}s)")
            
            # Use multiprocessing to handle groups of different lengths
            t1 = time.time()
            # Limit number of processes to min(CPU cores, 60) to ensure not exceeding Windows limits
            max_processes = min(mp.cpu_count(), 60)
            with mp.Pool(processes=max_processes) as pool:
                process_func = partial(self.process_length_group, term_topic_map=term_topic_map)
                results = pool.map(process_func, length_groups.values())
            print(f"Multiprocessing completed (Time: {time.time() - t1:.2f}s)")
            
            # Save original pattern analysis results
            pattern_file = self.save_pattern_analysis(results, length_groups, out_dir, self.taxonomy_level)
            
            # Create POI to Topic mapping
            poi_to_topic = {}
            for term, (topic_id, prob) in term_topic_map.items():
                poi_to_topic[term] = topic_id
            
            # Count POI frequency
            poi_frequency_analysis = {}
            for length_df in results:
                length = len([col for col in length_df.columns if col.startswith('topic_')])
                
                # Analyze each chain
                for _, row in length_df.iterrows():
                    chain_freq = row['frequency']
                    pois = row['ori_series'].split(' -> ')
                    
                    # Count each POI's appearance
                    for poi in pois:
                        if poi not in poi_frequency_analysis:
                            poi_frequency_analysis[poi] = {
                                'topic': poi_to_topic.get(poi, 'Unknown'),
                                'total_frequency': 0,
                                'by_length': {}
                            }
                        
                        # Update total frequency
                        poi_frequency_analysis[poi]['total_frequency'] += chain_freq
                        
                        # Update frequency by length
                        if length not in poi_frequency_analysis[poi]['by_length']:
                            poi_frequency_analysis[poi]['by_length'][length] = 0
                        poi_frequency_analysis[poi]['by_length'][length] += chain_freq
            
            # Save topic analysis results
            topic_file = self.save_topic_analysis(poi_frequency_analysis, out_dir, self.taxonomy_level)
            
            total_time = time.time() - start_time
            print(f"{city_name} analysis completed. Total time: {total_time:.2f}s")
            
            return pattern_file, topic_file
            
        except Exception as e:
            print(f"Error processing {city_name}: {str(e)}")
            return None, None
    
    def decode_all_cities(self):
        """
        Decode patterns for all cities
        """
        print("\n" + "="*50)
        print("Step 4: Pattern Decoding and Topic Mapping")
        print("="*50)
        
        # Get all city folders
        cities = [d.name for d in self.chain_analysis_dir.iterdir() if d.is_dir()]
        print(f"Found {len(cities)} cities to process")
        
        # Process each city
        results = {}
        for city in cities:
            pattern_file, topic_file = self.process_city_decoding(city)
            if pattern_file and topic_file:
                results[city] = {
                    'pattern_file': pattern_file,
                    'topic_file': topic_file
                }
        
        print(f"\nDecoding completed for {len(results)} cities")
        return results

