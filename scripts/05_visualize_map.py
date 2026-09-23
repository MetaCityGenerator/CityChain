import geopandas as gpd
import matplotlib.pyplot as plt
import os
from pathlib import Path
import numpy as np
import seaborn as sns
import math
import pandas as pd

class TopicMapVisualizer:
    def __init__(self, in_dir="data/output/chainAnalysisData", out_dir="data/output/chainPlotMap"):
        self.in_dir = Path(in_dir)
        self.out_dir = Path(out_dir)
    
    def generate_colors(self, n_topics: int) -> list:
        """Generate distinctive colors for specified number of topics"""
        if n_topics <= 10:
            # Use seaborn's husl color space
            colors = sns.color_palette("husl", n_topics)
        else:
            # For more topics, use larger color space
            colors = sns.color_palette("husl", n_topics)
        return colors
    
    def calculate_grid_size(self, n_topics: int) -> tuple:
        """Calculate optimal grid size"""
        # Calculate closest rectangular grid
        n_cols = math.ceil(math.sqrt(n_topics))
        n_rows = math.ceil(n_topics / n_cols)
        return n_rows, n_cols
    
    def load_topic_terms(self, city_name: str, taxonomy_level: int) -> pd.DataFrame:
        """Load and process topic terms data"""
        terms_file = os.path.join(self.in_dir, city_name, f"topicmodelling_{taxonomy_level}", f"poi_topic_analysis_topic_terms_{taxonomy_level}.csv")
        df = pd.read_csv(terms_file)
        return df
    
    def plot_topic_terms(self, ax, topic_df: pd.DataFrame, topic: int, color: str):
        """Plot top 10 terms for a specific topic"""
        # Filter for current topic and top 10 terms (excluding 'Null')
        topic_terms = topic_df[topic_df['topic'] == topic]
        topic_terms = topic_terms[topic_terms['term'] != 'Null'].head(10)
        
        # Create horizontal bar chart
        bars = ax.barh(topic_terms['term'], topic_terms['probability'], color=color, alpha=0.7)
        ax.set_title(f'Top 10 Terms - Topic {topic}')
        ax.set_xlabel('Probability')
        
        # Adjust layout
        ax.invert_yaxis()  # Show highest probability at top
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f'{width:.3f}', 
                   ha='left', va='center', fontsize=8)
    
    def plot_city_topics(self, city_name: str, taxonomy_level: int):
        """Plot topic maps for specified city"""
        # Build file path
        file_path = os.path.join(self.in_dir, city_name, f"spatial_visualization_{taxonomy_level}", f"road_topics_{taxonomy_level}.geojson")
        
        # Read data
        gdf = gpd.read_file(file_path)
        
        # Get unique topics count and colors
        unique_topics = sorted(gdf['dominant_topic'].unique())
        n_topics = len(unique_topics)
        colors = self.generate_colors(n_topics)
        
        # Calculate grid size
        n_rows, n_cols = self.calculate_grid_size(n_topics)
        
        # Create figure - separate view
        fig_separate = plt.figure(figsize=(n_cols * 16, n_rows * 12))
        fig_separate.suptitle(f'Road Network Topics in {city_name.title()} (Taxonomy Level {taxonomy_level})', 
                            fontsize=16, y=0.95)
        
        # Create combined overview
        fig_combined = plt.figure(figsize=(15, 15))
        ax_combined = fig_combined.add_subplot(111)
        
        # Set white background
        fig_separate.patch.set_facecolor('white')
        fig_combined.patch.set_facecolor('white')
        
        # Plot overview (fix deprecated warning)
        gdf.plot(column='dominant_topic',
                cmap=plt.colormaps['Set1'],
                legend=True,
                linewidth=0.8,
                ax=ax_combined)
        ax_combined.set_title(f'All Topics Combined - {city_name.title()}', fontsize=14)
        ax_combined.axis('equal')
        ax_combined.set_xticks([])
        ax_combined.set_yticks([])

        # Create output directory
        output_dir = self.out_dir / city_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load topic terms data
        topic_terms_df = self.load_topic_terms(city_name, taxonomy_level)
        
        # Plot all topics on fig_separate
        for i, topic in enumerate(unique_topics):
            # Create subplot - only one map subplot needed
            gs = plt.GridSpec(n_rows, n_cols, figure=fig_separate)
            row = i // n_cols
            col = i % n_cols
            
            # Map subplot
            ax_map = fig_separate.add_subplot(gs[row, col])
            other_topics = gdf[gdf['dominant_topic'] != topic]
            other_topics.plot(color='lightgray', alpha=0.2, ax=ax_map, linewidth=0.5)
            topic_data = gdf[gdf['dominant_topic'] == topic]
            topic_data.plot(color=colors[i], ax=ax_map, linewidth=1.2)
            ax_map.set_title(f'Topic {topic}', fontsize=12)
            ax_map.axis('equal')
            ax_map.set_xticks([])
            ax_map.set_yticks([])

        plt.figure(fig_separate.number)
        plt.tight_layout()
        
        # Create individual figure for each topic with map and bar chart
        for i, topic in enumerate(unique_topics):
            # Create new figure
            fig_individual = plt.figure(figsize=(20, 12))
            
            # Create subplot with top-bottom layout
            gs = plt.GridSpec(2, 1, height_ratios=[2, 1], figure=fig_individual)
            
            # Map subplot (top half)
            ax_map = fig_individual.add_subplot(gs[0])
            other_topics = gdf[gdf['dominant_topic'] != topic]
            other_topics.plot(color='lightgray', alpha=0.2, ax=ax_map, linewidth=0.5)
            topic_data = gdf[gdf['dominant_topic'] == topic]
            topic_data.plot(color=colors[i], ax=ax_map, linewidth=1.2)
            ax_map.set_title(f'Topic {topic} - {city_name.title()}', fontsize=14)
            ax_map.axis('equal')
            ax_map.set_xticks([])
            ax_map.set_yticks([])
            
            # Bar chart subplot (bottom half)
            ax_bar = fig_individual.add_subplot(gs[1])
            self.plot_topic_terms(ax_bar, topic_terms_df, topic, colors[i])
            
            plt.tight_layout()
            
            # Save individual topic figure
            fig_individual.savefig(
                output_dir / f"topic_{topic}_{city_name}.png",
                dpi=300,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            plt.close(fig_individual)
        
        # Create combined bar charts for all topics
        fig_bars = plt.figure(figsize=(15, n_topics * 2))
        for i, topic in enumerate(unique_topics):
            ax = fig_bars.add_subplot(n_topics, 1, i + 1)
            self.plot_topic_terms(ax, topic_terms_df, topic, colors[i])
        
        plt.tight_layout()
        
        # Save combined bar charts
        fig_bars.savefig(
            output_dir / f"topics_terms_{city_name}.png",
            dpi=300,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )

        # Save high resolution images
        fig_separate.savefig(
            output_dir / f"topics_separate_{city_name}.png",
            dpi=300,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        fig_combined.savefig(
            output_dir / f"topics_combined_{city_name}.png",
            dpi=300,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        
        plt.close('all')
        
    def process_all_cities(self, taxonomy_level: int):
        """Process data for all cities"""
        for city_dir in self.in_dir.iterdir():
            if city_dir.is_dir():
                try:
                    print(f"Processing {city_dir.name}...")
                    self.plot_city_topics(city_dir.name, taxonomy_level)
                    print(f"Completed {city_dir.name}")
                except Exception as e:
                    print(f"Error processing {city_dir.name}: {str(e)}")

def main():
    in_dir='data/output/chainAnalysisData'
    out_dir='data/output/chainPlotMap'
    visualizer = TopicMapVisualizer(in_dir, out_dir)
    taxonomy_level = 2
    visualizer.process_all_cities(taxonomy_level)

if __name__ == "__main__":
    main()