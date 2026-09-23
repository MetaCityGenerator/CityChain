import json
from collections import defaultdict
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from gensim.corpora import Dictionary
from gensim.models import LdaModel, CoherenceModel

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))
from pattern_mining import TaxonomyMapper

class POITopicAnalyzer:
    def __init__(self, taxonomy_mapper=None, taxonomy_level=1):
        self.taxonomy_mapper = taxonomy_mapper
        self.taxonomy_level = taxonomy_level
        self.dictionary = None
        self.corpus = None
        self.lda_model = None
        self.poi_chains = None
        self.texts = None  # Store processed document list
        
    def load_geojson(self, filepath: str) -> List[List[str]]:
        """Load GeoJSON and extract POI chains"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        poi_chains = []
        if data['type'] == 'FeatureCollection':
            features = data['features']
        else:
            features = [data]
            
        for feature in features:
            if 'properties' in feature and 'categories_primary_chain' in feature['properties']:
                chain = feature['properties']['categories_primary_chain']
                if isinstance(chain, str):
                    if self.taxonomy_mapper:
                        chain = self.map_chain_to_level(chain)
                    poi_chains.append(chain.split('|'))
                    
        self.poi_chains = poi_chains
        return poi_chains
    
    def map_chain_to_level(self, chain: str) -> str:
        """Map POI chain to specified level"""
        categories = chain.split('|')
        mapped_categories = [
            self.taxonomy_mapper.get_level_category(cat, self.taxonomy_level)
            for cat in categories
        ]
        return '|'.join(mapped_categories)
    
    def prepare_corpus(self, texts: List[List[str]]):
        """Prepare corpus"""
        self.texts = texts
        self.dictionary = Dictionary(texts)
        self.corpus = [self.dictionary.doc2bow(text) for text in texts]
        return self.corpus
    
    def train_lda(self, num_topics: int, passes: int = 20) -> LdaModel:
        """Train LDA model"""
        self.lda_model = LdaModel(
            corpus=self.corpus,
            id2word=self.dictionary,
            num_topics=num_topics,
            random_state=42,
            passes=passes
        )
        return self.lda_model
    
    def evaluate_num_topics(self, topic_range: range) -> pd.DataFrame:
        """Evaluate model performance with different topic numbers"""
        results = []
        
        for num_topics in topic_range:
            print(f"Evaluating topic number: {num_topics}")
            
            # Train LDA model
            lda = LdaModel(
                corpus=self.corpus,
                id2word=self.dictionary,
                num_topics=num_topics,
                random_state=42,
                passes=20
            )
            
            # Calculate coherence score
            coherence_model = CoherenceModel(
                model=lda,
                texts=self.texts,
                dictionary=self.dictionary,
                coherence='c_v'
            )
            coherence_score = coherence_model.get_coherence()
            
            # Calculate perplexity
            perplexity = lda.log_perplexity(self.corpus)
            print(f"coherence: {coherence_score}, perplexity: {perplexity}")
            results.append({
                'n_topics': num_topics,
                'coherence': coherence_score,
                'perplexity': perplexity
            })
            
        return pd.DataFrame(results)
    
    def analyze_topic_terms(self, top_n: int = 50) -> pd.DataFrame:
        """Analyze topic terms and their probabilities"""
        topics_df = []
        
        for topic_id in range(self.lda_model.num_topics):
            topic_terms = self.lda_model.show_topic(topic_id, topn=top_n)
            for term, prob in topic_terms:
                topics_df.append({
                    'topic': topic_id + 1,
                    'term': term,
                    'probability': prob
                })
        
        return pd.DataFrame(topics_df)
    
    def analyze_poi_connections(self) -> pd.DataFrame:
        """Analyze connections between POIs"""
        connections = defaultdict(lambda: defaultdict(int))
        
        # Count occurrences of adjacent POIs
        for chain in self.poi_chains:
            for i in range(len(chain) - 1):
                poi1, poi2 = chain[i], chain[i + 1]
                connections[poi1][poi2] += 1
        
        # Convert to DataFrame
        connections_df = []
        for poi1 in connections:
            for poi2, count in connections[poi1].items():
                connections_df.append({
                    'source_poi': poi1,
                    'target_poi': poi2,
                    'connection_count': count
                })
                
        return pd.DataFrame(connections_df)
    
    def analyze_topic_interactions(self) -> pd.DataFrame:
        """Analyze interactions between topics"""
        # Get most likely topic for each POI
        poi_topics = {}
        
        # Assign topic for each POI
        for chain in self.poi_chains:
            for poi in chain:
                # Convert POI to bow format
                bow = self.dictionary.doc2bow([poi])
                if bow:  # Ensure POI is in dictionary
                    # Get topic distribution
                    topic_dist = self.lda_model.get_document_topics(bow)
                    # Get most likely topic
                    main_topic = max(topic_dist, key=lambda x: x[1])[0]
                    poi_topics[poi] = main_topic
        
        # Analyze connections between topics
        topic_connections = defaultdict(lambda: defaultdict(int))
        for chain in self.poi_chains:
            for i in range(len(chain) - 1):
                poi1, poi2 = chain[i], chain[i + 1]
                if poi1 in poi_topics and poi2 in poi_topics:
                    topic1 = poi_topics[poi1]
                    topic2 = poi_topics[poi2]
                    topic_connections[topic1][topic2] += 1
        
        # Convert to DataFrame
        connections_df = []
        for topic1 in topic_connections:
            for topic2, count in topic_connections[topic1].items():
                connections_df.append({
                    'source_topic': topic1 + 1,  # Topic numbering starts from 1
                    'target_topic': topic2 + 1,
                    'connection_count': count
                })
        
        return pd.DataFrame(connections_df)

    def export_topic_modelling_file(self, geojson_file: str, out_dir: str, taxonomy_level: int) -> None:
        """Add topic distribution information to GeoJSON"""
        # Read original GeoJSON data
        gdf = gpd.read_file(geojson_file)
        
        # Ensure correct coordinate system
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        
        # Calculate topic distribution
        topic_probs = []
        dominant_topics = []
        
        for chain in gdf['categories_primary_chain']:
            if isinstance(chain, str):
                if self.taxonomy_mapper:
                    chain = self.map_chain_to_level(chain)
                tokens = chain.split('|')
                bow = self.dictionary.doc2bow(tokens)
                topic_dist = self.lda_model.get_document_topics(bow)
                
                full_dist = [0] * self.lda_model.num_topics
                for topic_id, prob in topic_dist:
                    full_dist[topic_id] = prob
                
                topic_probs.append(full_dist)
                dominant_topic = max(topic_dist, key=lambda x: x[1])[0] if topic_dist else -1
                dominant_topics.append(dominant_topic + 1)
            else:
                topic_probs.append([0] * self.lda_model.num_topics)
                dominant_topics.append(-1)
        
        # Add topic probabilities to GeoDataFrame
        topic_prob_columns = [f'topic_{i+1}_prob' for i in range(self.lda_model.num_topics)]
        for i, col in enumerate(topic_prob_columns):
            gdf[col] = [probs[i] if len(probs) > i else 0 for probs in topic_probs]
        
        # Select specific results for output
        gdf = gdf.drop(columns=['names_primary_chain', 'names_common_chain', 'names_rules_chain', 'categories_primary_chain', 'categories_alternate_chain'])
        gdf['dominant_topic'] = dominant_topics
        
        # Create output directory
        vis_dir = os.path.join(out_dir, f'spatial_visualization_{taxonomy_level}')
        os.makedirs(vis_dir, exist_ok=True)
        
        # Save GeoJSON with topic information
        output_geojson = os.path.join(vis_dir, f'road_topics_{taxonomy_level}.geojson')
        gdf.to_file(output_geojson, driver='GeoJSON')
        
        print(f"GeoJSON with topic information saved to: {output_geojson}")

def output_lda_results(
    lda_model,
    analyzer,
    out_dir: str = None,
    output_prefix: str = None,
    save_model: bool = True,
    save_vis: bool = True,
    taxonomy_level: int = 1
) -> None:
    """Output detailed LDA model results
    
    Args:
        lda_model: Trained LDA model
        analyzer: POITopicAnalyzer instance containing dictionary and corpus
        out_dir: Output directory
        output_prefix: Output file prefix, defaults to timestamp
        save_model: Whether to save model files
        save_vis: Whether to generate interactive visualization
    """
    # Generate output prefix
    if output_prefix is None:
        output_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    # Console output
    print("\n=== LDA Model Results ===")
    print(f"Number of topics: {lda_model.num_topics}")
    print("\nTopic-word distribution:")
    for topic_id in range(lda_model.num_topics):
        topic_words = lda_model.show_topic(topic_id, topn=10)
        print(f"\nTopic {topic_id + 1}:")
        for word, prob in topic_words:
            print(f"  - {word}: {prob:.4f}")
            
    # If output directory is specified
    if out_dir:
        # Save detailed results to text file
        result_file = os.path.join(out_dir, f'lda_results_{output_prefix}_{taxonomy_level}.txt')
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"LDA Model Results\n")
            f.write("=" * 50 + "\n\n")
            
            # Write basic information
            f.write(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Number of topics: {lda_model.num_topics}\n")
            f.write(f"Dictionary size: {len(analyzer.dictionary)}\n")
            f.write(f"Number of documents: {len(analyzer.corpus)}\n")
            
            # Write perplexity
            perplexity = lda_model.log_perplexity(analyzer.corpus)
            f.write(f"Model perplexity: {perplexity:.4f}\n\n")

            # Calculate and write coherence score
            coherence_model = CoherenceModel(
                model=lda_model,
                texts=analyzer.texts,
                dictionary=analyzer.dictionary,
                coherence='c_v'
            )
            coherence_score = coherence_model.get_coherence()
            f.write(f"Topic Coherence: {coherence_score:.4f}\n\n")
            
            # Write topic-word distribution
            f.write("Topic-word distribution details:\n")
            for topic_id in range(lda_model.num_topics):
                topic_words = lda_model.show_topic(topic_id, topn=20)
                f.write(f"\nTopic {topic_id + 1}:\n")
                for word, prob in topic_words:
                    f.write(f"  - {word}: {prob:.4f}\n")
                    
        print(f"\nDetailed results saved to: {result_file}")
        
        # Save model file
        if save_model:
            model_dir = os.path.join(out_dir, f"models_{taxonomy_level}")
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            model_file = os.path.join(model_dir, f'lda_model_{output_prefix}_{taxonomy_level}')
            lda_model.save(model_file)
            print(f"Model saved to: {model_file}")
        
        # Generate interactive visualization
        if save_vis:
            try:
                import pyLDAvis
                import pyLDAvis.gensim_models as gensimvis
                
                vis_data = gensimvis.prepare(lda_model, analyzer.corpus, analyzer.dictionary)
                vis_file = os.path.join(model_dir, f'lda_vis_{output_prefix}_{taxonomy_level}.html')
                pyLDAvis.save_html(vis_data, vis_file)
                print(f"Interactive visualization saved to: {vis_file}")
            except ImportError:
                print("Note: Install pyLDAvis package to generate interactive visualization")

def analyze_optimal_topics(
    geojson_file: str,
    topic_range: range,
    taxonomy_mapper=None,
    taxonomy_level=1,
    out_dir: str = None,
):
    """Analyze optimal topic number and generate evaluation plots"""
    import matplotlib.pyplot as plt
    
    # Initialize analyzer
    analyzer = POITopicAnalyzer(taxonomy_mapper, taxonomy_level)
    
    # Load data
    print("Loading GeoJSON data...")
    texts = analyzer.load_geojson(geojson_file)
    
    # Prepare corpus
    print("Preparing corpus...")
    analyzer.prepare_corpus(texts)
    
    # Evaluate different topic numbers
    print("Evaluating different topic numbers...")
    eval_results = analyzer.evaluate_num_topics(topic_range)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    # Coherence plot (higher is better)
    ax1.plot(eval_results['n_topics'], eval_results['coherence'], 'bo-')
    ax1.set_xlabel('topic number')
    ax1.set_ylabel('topic coherence')
    ax1.set_title('topic number vs coherence')
    ax1.grid(True)
    
    # Perplexity plot (lower is better)
    ax2.plot(eval_results['n_topics'], eval_results['perplexity'], 'ro-')
    ax2.set_xlabel('topic number')
    ax2.set_ylabel('perplexity')
    ax2.set_title('topic number vs perplexity')
    ax2.grid(True)
    
    plt.tight_layout()
    out_topic_dir = os.path.join(out_dir, f"topicmodelling_{taxonomy_level}")
    if not os.path.exists(out_topic_dir):
        os.makedirs(out_topic_dir)
    # Save plot
    plot_file = os.path.join(out_topic_dir, f'topic_evaluation_{taxonomy_level}.png')
    plt.savefig(plot_file)
    print(f"Evaluation plot saved to: {plot_file}")
    
    return eval_results

def analyze_poi_topics(
        geojson_file: str,
        num_topics: int,
        taxonomy_mapper=None,
        taxonomy_level=1,
        output_prefix: str = None,
        out_dir: str = None,
    ):
        """Main analysis function"""
        # Create output file prefix
        if output_prefix is None:
            output_prefix = f'poi_topic_analysis'
            
        # Initialize analyzer
        analyzer = POITopicAnalyzer(taxonomy_mapper, taxonomy_level)
        
        # Load data
        print("Loading GeoJSON data...")
        poi_chains = analyzer.load_geojson(geojson_file)
        print(f"Loaded {len(poi_chains)} POI chains")
        
        # Prepare corpus
        print("Preparing corpus...")
        analyzer.prepare_corpus(poi_chains)
        
        # Train LDA model
        print(f"Training LDA model (topics: {num_topics})...")
        lda_model = analyzer.train_lda(num_topics)
        
        # Output model results
        output_lda_results(
            lda_model=lda_model,
            analyzer=analyzer,
            out_dir=out_dir,
            output_prefix=output_prefix,
            taxonomy_level=taxonomy_level
        )

        out_topic_dir = os.path.join(out_dir, f"topicmodelling_{taxonomy_level}")
        if not os.path.exists(out_topic_dir):
            os.makedirs(out_topic_dir)

        # Analyze topic terms
        print("Analyzing topic terms...")
        topic_terms_df = analyzer.analyze_topic_terms()
        topic_terms_file = os.path.join(out_topic_dir, f'{output_prefix}_topic_terms_{taxonomy_level}.csv')
        topic_terms_df.to_csv(topic_terms_file, index=False)
        print(f"Topic terms analysis results saved to: {topic_terms_file}")
        
        # Analyze POI connections
        print("Analyzing POI connections...")
        connections_df = analyzer.analyze_poi_connections()
        connections_file = os.path.join(out_topic_dir, f'{output_prefix}_poi_connections_{taxonomy_level}.csv')
        connections_df.to_csv(connections_file, index=False)
        print(f"POI connection analysis results saved to: {connections_file}")
        
        # Analyze topic interactions
        print("Analyzing topic interactions...")
        topic_interactions_df = analyzer.analyze_topic_interactions()
        interactions_file = os.path.join(out_topic_dir, f'{output_prefix}_topic_interactions_{taxonomy_level}.csv')
        topic_interactions_df.to_csv(interactions_file, index=False)
        print(f"Topic interaction analysis results saved to: {interactions_file}")

        # Add spatial visualization
        print("\nGenerating spatial visualization...")
        analyzer.export_topic_modelling_file(geojson_file, out_dir, taxonomy_level)
        
        # Create a summary file
        summary_file = os.path.join(out_topic_dir, f'{output_prefix}_{taxonomy_level}_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("POI Topic Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            
            # Write basic information
            f.write(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data file: {geojson_file}\n")
            f.write(f"Number of POI chains: {len(poi_chains)}\n")
            f.write(f"Number of topics: {num_topics}\n\n")
            
            # Write main POIs for each topic
            f.write("Topic Overview:\n")
            for topic in range(num_topics):
                topic_terms = topic_terms_df[topic_terms_df['topic'] == topic + 1]
                top_terms = topic_terms.head(10)['term'].tolist()
                f.write(f"\nTopic {topic + 1} Main POI Types:\n")
                for term in top_terms:
                    prob = topic_terms[topic_terms['term'] == term]['probability'].iloc[0]
                    f.write(f"- {term}: {prob:.4f}\n")
                    
        print(f"Analysis summary saved to: {summary_file}")
        
        return {
            'topic_terms': topic_terms_df,
            'poi_connections': connections_df,
            'topic_interactions': topic_interactions_df
        }

# Usage example
if __name__ == "__main__":
    # Standalone example for a single city (run 03_generate_chains.py first)
    geojson_file = 'data/output/chainRawData/amsterdam/amsterdam_road_text_chain.geojson'
    out_dir = 'data/output/chainAnalysisData/amsterdam'
    os.makedirs(out_dir, exist_ok=True)
    taxonomy_file = 'data/input/overture_categories.csv'
    taxonomy_mapper = TaxonomyMapper(taxonomy_file)

    level = 2

    # First evaluate optimal topic number
    eval_results = analyze_optimal_topics(
        geojson_file=geojson_file,
        topic_range=range(2, 10),  # Test 2 to 10 topics
        taxonomy_mapper=taxonomy_mapper,
        taxonomy_level=level,
        out_dir=out_dir,
    )
    
    # View evaluation results
    print("\nEvaluation results:")
    print(eval_results)

    results = analyze_poi_topics(
        geojson_file=geojson_file,
        num_topics=6,  # Set desired number of topics
        taxonomy_mapper=taxonomy_mapper,  # Pass TaxonomyMapper instance if using taxonomy mapping
        taxonomy_level=level,
        out_dir=out_dir,
    )