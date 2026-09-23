"""
Distribution Analysis Module
Calculates normalizations, correlations, and creates visualizations
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


class DistributionAnalyzer:
    """Analyze pattern distributions and create visualizations"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
    
    def calculate_normalizations(self, df):
        """Calculate various normalization results"""
        # 1. Calculate proportion of total chains per city (by row)
        df_percentage = df.div(df.sum(axis=1), axis=0) * 100
        
        # 2. Calculate proportion relative to each city's maximum value (by row)
        df_relative = df.div(df.max(axis=1), axis=0)
        
        # 3. Z-score standardization (by row)
        df_zscore = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)
        
        # 4. Min-Max normalization (by row)
        df_minmax = df.sub(df.min(axis=1), axis=0).div(df.max(axis=1) - df.min(axis=1), axis=0)
        
        return df_percentage, df_relative, df_zscore, df_minmax
    
    def plot_correlations(self, df_percentage, output_dir):
        """Plot correlation heatmap"""
        plt.figure(figsize=(12, 10))
        correlation = df_percentage.T.corr()
        
        sns.heatmap(correlation, 
                    annot=True, 
                    cmap='coolwarm', 
                    center=0,
                    fmt='.2f',
                    square=True)
        
        plt.title('Correlation Heatmap of Chain Length Distribution (Based on Percentage)',
                 pad=20)
        plt.tight_layout()
        plt.savefig(output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_distributions(self, df_percentage, output_dir):
        """Plot chain length distribution"""
        plt.figure(figsize=(12, 6))
        
        for city in df_percentage.index:
            plt.plot(df_percentage.columns, df_percentage.loc[city], marker='o', label=city, alpha=0.7)
        
        plt.xlabel('Chain Length')
        plt.ylabel('Percentage (%)')
        plt.title('Chain Length Distribution Across Cities')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(output_dir / 'length_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_boxplot(self, df_percentage, output_dir):
        """Plot boxplot"""
        plt.figure(figsize=(12, 6))
        
        df_percentage.T.boxplot()
        plt.xticks(rotation=45)
        plt.xlabel('Chain Length')
        plt.ylabel('Percentage (%)')
        plt.title('Distribution of Chain Lengths by City')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(output_dir / 'distribution_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_heatmap_raw(self, df, output_dir):
        """Plot raw data heatmap"""
        plt.figure(figsize=(12, 8))
        
        sns.heatmap(df, 
                    annot=True, 
                    fmt='.0f',
                    cmap='YlOrRd')
        
        plt.title('Pattern Counts Heatmap')
        plt.xlabel('Chain Length')
        plt.ylabel('Cities')
        plt.tight_layout()
        plt.savefig(output_dir / 'pattern_counts_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def analyze_pattern_distributions(self, df_frequencies):
        """
        Analyze pattern distributions and create visualizations
        """
        print("\n" + "="*50)
        print("Step 2: Pattern Distribution Analysis")
        print("="*50)
        
        pattern_dir = self.output_dir / 'chainPattern'
        
        # Calculate normalizations
        df_percentage, df_relative, df_zscore, df_minmax = self.calculate_normalizations(df_frequencies)
        
        # Save results
        round_num = 5
        df_percentage.round(round_num).to_csv(pattern_dir / 'chain_percentage.csv')
        df_relative.round(round_num).to_csv(pattern_dir / 'chain_relative.csv')
        df_zscore.round(round_num).to_csv(pattern_dir / 'chain_zscore.csv')
        df_minmax.round(round_num).to_csv(pattern_dir / 'chain_minmax.csv')
        
        # Calculate and save correlations
        correlation = df_percentage.T.corr()
        correlation.round(round_num).to_csv(pattern_dir / 'chain_correlation.csv')
        
        # Create visualizations
        self.plot_correlations(df_percentage, pattern_dir)
        self.plot_distributions(df_percentage, pattern_dir)
        self.plot_boxplot(df_percentage, pattern_dir)
        self.plot_heatmap_raw(df_frequencies, pattern_dir)
        
        print(f"Pattern distribution analysis completed. Results saved to: {pattern_dir}")
        
        return df_percentage

