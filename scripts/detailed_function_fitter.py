"""
Function Fitting Module
Fits decay functions to chain length distributions
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from pathlib import Path


class FunctionFitter:
    """Fit decay functions to chain length distributions"""
    
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
    
    @staticmethod
    def exponential_decay(x, a, b):
        """Exponential decay: y = a * exp(-bx)"""
        return a * np.exp(-b * x)
    
    @staticmethod
    def power_law_decay(x, a, b):
        """Power law decay: y = a * x^(-b)"""
        return a * np.power(x, -b)
    
    @staticmethod
    def logarithmic_decay(x, a, b):
        """Logarithmic decay: y = a - b * ln(x)"""
        return a - b * np.log(x)
    
    @staticmethod
    def hyperbolic_decay(x, a, b):
        """Hyperbolic decay: y = a / (x + b)"""
        return a / (x + b)
    
    def plot_all_cities_with_fits(self, df, output_dir):
        """Plot all cities' curves and four types of fitting curves"""
        plt.figure(figsize=(15, 10))
        
        # Prepare X data
        x_data = np.array([int(col.split('_')[1]) for col in df.columns])
        
        # Plot all cities' curves (with higher transparency)
        for city in df.index:
            plt.plot(x_data, df.loc[city], 'gray', alpha=0.2, linewidth=1)
        
        # Calculate mean trend
        mean_trend = df.mean()
        std_trend = df.std()
        
        # Plot mean trend
        plt.plot(x_data, mean_trend, 'k-', linewidth=2, label='Mean Trend')
        plt.fill_between(x_data, mean_trend - std_trend, mean_trend + std_trend,
                        color='gray', alpha=0.2, label='±1 SD')
        
        # List of fitting functions
        fit_funcs = {
            'Exponential': (self.exponential_decay, [30, 0.3]),
            'Power Law': (self.power_law_decay, [50, 1]),
            'Logarithmic': (self.logarithmic_decay, [40, 10]),
            'Hyperbolic': (self.hyperbolic_decay, [100, 1])
        }
        
        # Color list
        colors = ['r', 'b', 'g', 'm']
        
        # Store fitting results
        fit_results = {}
        
        # Generate smooth x values for plotting fitted curves
        x_smooth = np.linspace(min(x_data), max(x_data), 100)
        
        # Fit each function
        for (name, (func, p0)), color in zip(fit_funcs.items(), colors):
            try:
                # Fit curve
                popt, _ = curve_fit(func, x_data, mean_trend, p0=p0)
                y_fit = func(x_data, *popt)
                r2 = r2_score(mean_trend, y_fit)
                
                # Generate smooth fitted curve
                y_smooth = func(x_smooth, *popt)
                
                # Plot fitted curve
                plt.plot(x_smooth, y_smooth, f'{color}-', linewidth=2,
                        label=f'{name} (R² = {r2:.3f})')
                
                # Store fitting results
                fit_results[name] = {
                    'params': popt,
                    'r2': r2,
                    'function': func
                }
                
            except Exception as e:
                print(f"Error fitting {name}: {str(e)}")
        
        plt.xlabel('Chain Length')
        plt.ylabel('Percentage (%)')
        plt.title('Chain Length Distribution Patterns with Different Decay Functions')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_dir / 'all_cities_fits.png', 
                    dpi=300, bbox_inches='tight')
        plt.close()
        
        return fit_results
    
    def print_equations(self, fit_results):
        """Print fitting equations"""
        print("\n=== Fitting Results ===")
        
        equations = {
            'Exponential': lambda p: f"y = {p[0]:.2f} * exp(-{p[1]:.3f}x)",
            'Power Law': lambda p: f"y = {p[0]:.2f} * x^(-{p[1]:.3f})",
            'Logarithmic': lambda p: f"y = {p[0]:.2f} - {p[1]:.3f} * ln(x)",
            'Hyperbolic': lambda p: f"y = {p[0]:.2f} / (x + {p[1]:.3f})"
        }
        
        for name, result in fit_results.items():
            print(f"\n{name} decay:")
            print(f"Equation: {equations[name](result['params'])}")
            print(f"R² = {result['r2']:.4f}")
    
    def fit_decay_functions(self, df_percentage):
        """
        Fit decay functions to chain length distributions
        """
        print("\n" + "="*50)
        print("Step 3: Decay Function Fitting")
        print("="*50)
        
        fit_dir = self.output_dir / 'chainPattern' / 'curve_fitting'
        fit_dir.mkdir(exist_ok=True)
        
        # Plot all cities with fits
        fit_results = self.plot_all_cities_with_fits(df_percentage, fit_dir)
        
        # Print fitting results
        self.print_equations(fit_results)
        
        # Save fitting results to CSV
        results_df = pd.DataFrame({
            name: {
                'R2': result['r2'],
                **{f'param_{i}': p for i, p in enumerate(result['params'])}
            }
            for name, result in fit_results.items()
        }).T
        
        results_df.to_csv(fit_dir / 'decay_fitting_results.csv')
        
        print(f"Function fitting completed. Results saved to: {fit_dir}")
        
        return fit_results

