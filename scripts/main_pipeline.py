"""
Main Analysis Pipeline
Orchestrates the complete urban functional chain analysis workflow
"""
import time
from datetime import datetime
import importlib.util
import sys
from pathlib import Path
import os

# ========== Configuration Constants ==========
# Data directories
DATA_INPUT_CITY = "data/input/city"
DATA_INPUT_TAXONOMY = "data/input/overture_categories.csv"
DATA_OUTPUT_CHAIN_RAW = "data/output/chainRawData"
DATA_OUTPUT_CHAIN_ANALYSIS = "data/output/chainAnalysisData"
DATA_OUTPUT_CHAIN_PLOT = "data/output/chainPlotMap"
DATA_OUTPUT_ANALYSIS_RESULTS = "data/output/analysisResults"

os.makedirs(DATA_OUTPUT_CHAIN_RAW, exist_ok=True)
os.makedirs(DATA_OUTPUT_CHAIN_ANALYSIS, exist_ok=True)
os.makedirs(DATA_OUTPUT_CHAIN_PLOT, exist_ok=True)
os.makedirs(DATA_OUTPUT_ANALYSIS_RESULTS, exist_ok=True)

# Analysis parameters
TAXONOMY_LEVEL = 2  # Taxonomy level for analysis (1-3, higher = more granular)


def load_module(script_name, module_name):
    """
    Dynamically load a Python module from a script file
    
    Args:
        script_name: Name of the script file (e.g., "03_generate_chains.py")
        module_name: Name to use for the module (e.g., "generate_chains")
    
    Returns:
        Loaded module
    """
    script_path = Path(__file__).parent / script_name
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_complete_pipeline():
    """
    Execute the complete analysis pipeline in sequence:
    1. Generate POI functional chains
    2. Analyze cities (network, patterns, topics)
    3. Visualize topic maps
    4. Detailed analysis (distributions, fitting, decoding, cross-topic)
    """
    
    print("\n" + "="*70)
    print("URBAN FUNCTIONAL CHAIN ANALYSIS PIPELINE")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    overall_start = time.time()
    
    # ========== Step 1: Generate POI Functional Chains ==========
    print("\n" + "="*70)
    print("STEP 1/4: Generating POI Functional Chains")
    print("="*70)
    step_start = time.time()
    
    try:
        # Load 03_generate_chains.py
        generate_chains = load_module("03_generate_chains.py", "generate_chains")
        
        processor = generate_chains.POIChainProcessor(DATA_INPUT_CITY, DATA_OUTPUT_CHAIN_RAW)
        processor.process_all_cities()
        
        step_time = time.time() - step_start
        print(f"\n✓ Step 1 completed in {step_time:.2f} seconds ({step_time/60:.2f} minutes)")
    except Exception as e:
        print(f"\n✗ Error in Step 1: {str(e)}")
        return False
    
    # ========== Step 2: Analyze Cities ==========
    print("\n" + "="*70)
    print("STEP 2/4: Analyzing Cities (Network + Patterns + Topics)")
    print("="*70)
    step_start = time.time()
    
    try:
        # Load 04_analyze_cities.py
        analyze_cities = load_module("04_analyze_cities.py", "analyze_cities")
        
        analyzer = analyze_cities.CityAnalyzer(
            DATA_OUTPUT_CHAIN_RAW, 
            DATA_OUTPUT_CHAIN_ANALYSIS, 
            DATA_INPUT_TAXONOMY
        )
        analyzer.analyze_all_cities(taxonomy_level=TAXONOMY_LEVEL)
        
        step_time = time.time() - step_start
        print(f"\n✓ Step 2 completed in {step_time:.2f} seconds ({step_time/60:.2f} minutes)")
    except Exception as e:
        print(f"\n✗ Error in Step 2: {str(e)}")
        return False
    
    # ========== Step 3: Visualize Topic Maps ==========
    print("\n" + "="*70)
    print("STEP 3/4: Visualizing Topic Maps")
    print("="*70)
    step_start = time.time()
    
    try:
        # Load 05_visualize_map.py
        visualize_map = load_module("05_visualize_map.py", "visualize_map")
        
        visualizer = visualize_map.TopicMapVisualizer(
            DATA_OUTPUT_CHAIN_ANALYSIS, 
            DATA_OUTPUT_CHAIN_PLOT
        )
        visualizer.process_all_cities(TAXONOMY_LEVEL)
        
        step_time = time.time() - step_start
        print(f"\n✓ Step 3 completed in {step_time:.2f} seconds ({step_time/60:.2f} minutes)")
    except Exception as e:
        print(f"\n✗ Error in Step 3: {str(e)}")
        return False
    
    # ========== Step 4: Detailed Analysis ==========
    print("\n" + "="*70)
    print("STEP 4/4: Running Detailed Analysis")
    print("="*70)
    step_start = time.time()
    
    try:
        # Load 06_detailed_analysis_cities.py
        detailed_analysis_cities = load_module("06_detailed_analysis_cities.py", "detailed_analysis_cities")
        
        analyzer = detailed_analysis_cities.DetailedCityAnalyzer(
            chain_analysis_dir=DATA_OUTPUT_CHAIN_ANALYSIS,
            output_dir=DATA_OUTPUT_ANALYSIS_RESULTS,
            taxonomy_level=TAXONOMY_LEVEL
        )
        results = analyzer.run_complete_analysis()
        
        step_time = time.time() - step_start
        print(f"\n✓ Step 4 completed in {step_time:.2f} seconds ({step_time/60:.2f} minutes)")
    except Exception as e:
        print(f"\n✗ Error in Step 4: {str(e)}")
        return False
    
    # ========== Summary ==========
    total_time = time.time() - overall_start
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETED SUCCESSFULLY! 🎉")
    print("="*70)
    print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nOutput directories:")
    print(f"  - Chain data:        {DATA_OUTPUT_CHAIN_RAW}")
    print(f"  - Analysis data:     {DATA_OUTPUT_CHAIN_ANALYSIS}")
    print(f"  - Topic maps:        {DATA_OUTPUT_CHAIN_PLOT}")
    print(f"  - Detailed results:  {DATA_OUTPUT_ANALYSIS_RESULTS}")
    print("="*70)
    
    return True


def main():
    """Main entry point"""
    success = run_complete_pipeline()
    
    if not success:
        print("\n" + "="*70)
        print("PIPELINE FAILED")
        print("="*70)
        print("Please check the error messages above and fix any issues.")
        exit(1)


if __name__ == "__main__":
    main()

