import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- CONFIGURATION ---
RESULTS_FILE = 'optimization_results_summary.csv'
WEIGHTS_FILE = 'optimization_weights.csv'
DATA_FILE = 'cleaned_dataset.csv'

def generate_plots():
    # Load Results
    df_res = pd.read_csv(RESULTS_FILE)
    df_weights = pd.read_csv(WEIGHTS_FILE, index_col=0)
    
    # 1. Risk-Return Scatter Plot (Efficient Frontier visualization)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_res, x='Volatility', y='Return', hue='Scenario', s=100, style='Scenario')
    
    # Add labels
    for i, row in df_res.iterrows():
        plt.text(row['Volatility']+0.002, row['Return'], row['Scenario'], fontsize=9)
        
    plt.title('Portfolio Optimization Results: Risk vs Return')
    plt.xlabel('Annualized Volatility')
    plt.ylabel('Annualized Return')
    plt.grid(True, alpha=0.3)
    plt.savefig('risk_return_plot.png')
    print("Saved risk_return_plot.png")
    
    # 2. Asset Allocation Plot (Top 10 weights for Base Case)
    # Let's plot allocation for "Base Case (Max Sharpe)"
    if 'Base Case (Max Sharpe)' in df_weights.columns:
        weights = df_weights['Base Case (Max Sharpe)'].sort_values(ascending=False)
        top_10 = weights.head(10)
        others = weights.iloc[10:].sum()
        if others > 0:
            top_10['Others'] = others
            
        plt.figure(figsize=(12, 6))
        top_10.plot(kind='bar', color='skyblue')
        plt.title('Asset Allocation - Base Case (Max Sharpe)')
        plt.ylabel('Weight')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('allocation_base_case.png')
        print("Saved allocation_base_case.png")
        
    # 3. Allocation Comparison (Stacked Bar for Scenarios)
    # We transpose df_weights to have Scenarios as rows (or keep columns)
    # We want Scenarios on X axis, Weights on Y (Stacked)
    # Filter for top assets across all scenarios to avoid clutter
    # Get top 5 assets by average weight across scenarios
    top_assets = df_weights.mean(axis=1).sort_values(ascending=False).head(7).index
    df_plot = df_weights.loc[top_assets].T
    
    df_plot.plot(kind='bar', stacked=True, figsize=(12, 6), colormap='tab20')
    plt.title('Top 7 Asset Allocations across Scenarios')
    plt.ylabel('Weight')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('allocation_comparison.png')
    print("Saved allocation_comparison.png")

if __name__ == "__main__":
    generate_plots()
