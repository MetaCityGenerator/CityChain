"""
Comprehensive City Analysis Pipeline
Main script that orchestrates detailed analysis using modular components
"""
import time
from pathlib import Path

# Import analysis modules
from detailed_pattern_counter import PatternCounter
from detailed_distribution_analyzer import DistributionAnalyzer
from detailed_function_fitter import FunctionFitter
from detailed_pattern_decoder import PatternDecoder
from detailed_cross_topic_analyzer import CrossTopicAnalyzer


class DetailedCityAnalyzer:
    """
    Comprehensive city analysis integrating multiple analytical approaches:
    - Pattern counting and frequency analysis
    - Chain length distribution analysis
    - Pattern decoding and topic mapping
    - Cross-topic pattern analysis
    - Function fitting for decay patterns
    """
    
    def __init__(self, chain_analysis_dir, output_dir, taxonomy_level=2):
        """
        Initialize the analyzer
        
        Args:
            chain_analysis_dir: Directory containing chain analysis data for all cities
            output_dir: Directory to save analysis results
            taxonomy_level: Taxonomy level to use (default: 2)
        """
        self.chain_analysis_dir = Path(chain_analysis_dir)
        self.output_dir = Path(output_dir)
        self.taxonomy_level = taxonomy_level
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize all analysis modules
        self.pattern_counter = PatternCounter(
            chain_analysis_dir, output_dir, taxonomy_level
        )
        self.distribution_analyzer = DistributionAnalyzer(output_dir)
        self.function_fitter = FunctionFitter(output_dir)
        self.pattern_decoder = PatternDecoder(
            chain_analysis_dir, output_dir, taxonomy_level
        )
        self.cross_topic_analyzer = CrossTopicAnalyzer(
            output_dir, taxonomy_level
        )
    
    def run_complete_analysis(self):
        """
        Run complete analysis pipeline
        """
        print("\n" + "="*60)
        print("Starting Comprehensive City Analysis")
        print("="*60)
        print(f"Input directory: {self.chain_analysis_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Taxonomy level: {self.taxonomy_level}")
        
        start_time = time.time()
        
        # Step 1: Pattern Counting
        df_patterns, df_frequencies = self.pattern_counter.process_pattern_counts()
        
        # Step 2: Pattern Distribution Analysis
        df_percentage = self.distribution_analyzer.analyze_pattern_distributions(df_frequencies)
        
        # Step 3: Decay Function Fitting
        fit_results = self.function_fitter.fit_decay_functions(df_percentage)
        
        # Step 4: Pattern Decoding and Topic Mapping
        decoding_results = self.pattern_decoder.decode_all_cities()
        
        # Step 5: Cross-Topic Pattern Analysis
        self.cross_topic_analyzer.analyze_cross_topics()
        
        total_time = time.time() - start_time
        
        print("\n" + "="*60)
        print("Complete Analysis Finished")
        print("="*60)
        print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"Results saved to: {self.output_dir}")
        
        return {
            'pattern_counts': df_patterns,
            'frequency_counts': df_frequencies,
            'percentage': df_percentage,
            'fit_results': fit_results,
            'decoding_results': decoding_results
        }


def main():
    # Set paths
    chain_analysis_dir = 'data/output/chainAnalysisData'
    output_dir = 'data/output/analysisResults'
    taxonomy_level = 2
    
    # Create analyzer
    analyzer = DetailedCityAnalyzer(
        chain_analysis_dir=chain_analysis_dir,
        output_dir=output_dir,
        taxonomy_level=taxonomy_level
    )
    
    # Run complete analysis
    results = analyzer.run_complete_analysis()
    
    print("\n" + "="*60)
    print("All analysis tasks completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
