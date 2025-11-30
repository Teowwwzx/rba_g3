import pandas as pd
import numpy as np
import scipy.optimize as sco
from scipy.stats import norm

# --- CONFIGURATION ---
DATA_FILE = 'cleaned_dataset.csv'
BENCHMARK_TICKER = '^KLSE'
RISK_FREE_RATE_ANNUAL = 0.04
TRADING_DAYS = 252

def load_data():
    df = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
    # Separate Stocks and Benchmark
    # Benchmark is '^KLSE', Risk Free is 'MGS_10Y'
    # Stocks are the rest
    
    # Identify stock columns (exclude benchmark and risk free)
    stock_cols = [c for c in df.columns if c not in [BENCHMARK_TICKER, 'MGS_10Y']]
    
    df_stocks = df[stock_cols]
    df_benchmark = df[BENCHMARK_TICKER]
    
    return df_stocks, df_benchmark

def get_portfolio_metrics(weights, mean_returns, cov_matrix, risk_free_rate=0.04/252):
    weights = np.array(weights)
    # Annualized Return
    ret = np.sum(mean_returns * weights) * TRADING_DAYS
    # Annualized Volatility
    vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(TRADING_DAYS)
    # Sharpe Ratio
    sharpe = (ret - risk_free_rate * TRADING_DAYS) / vol if vol > 0 else 0
    
    # Daily VaR (95%)
    # Parametric VaR: Mean - 1.65 * Vol
    # We need Daily Mean and Daily Vol for Daily VaR
    daily_ret = np.sum(mean_returns * weights)
    daily_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    var_95 = daily_ret - 1.65 * daily_vol
    
    return ret, vol, sharpe, var_95

def negative_sharpe(weights, mean_returns, cov_matrix, risk_free_rate):
    return -get_portfolio_metrics(weights, mean_returns, cov_matrix, risk_free_rate)[2]

def portfolio_volatility(weights, mean_returns, cov_matrix, risk_free_rate):
    return get_portfolio_metrics(weights, mean_returns, cov_matrix, risk_free_rate)[1]

def negative_return(weights, mean_returns, cov_matrix, risk_free_rate):
    return -get_portfolio_metrics(weights, mean_returns, cov_matrix, risk_free_rate)[0]

def optimize_portfolio(mean_returns, cov_matrix, constraint_type='max_sharpe', target_vol=None, max_weight=1.0):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, RISK_FREE_RATE_ANNUAL/TRADING_DAYS)
    
    # Constraints
    # Sum of weights = 1
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    
    # Bounds (0 <= w <= max_weight)
    bounds = tuple((0.0, max_weight) for _ in range(num_assets))
    
    # Initial Guess
    init_guess = num_assets * [1. / num_assets,]
    
    if constraint_type == 'max_sharpe':
        result = sco.minimize(negative_sharpe, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
                              
    elif constraint_type == 'min_vol':
        result = sco.minimize(portfolio_volatility, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
                              
    elif constraint_type == 'target_vol':
        # Maximize Return subject to Vol <= target_vol
        # Add inequality constraint: target_vol - vol >= 0
        constraints.append({'type': 'ineq', 
                            'fun': lambda x: target_vol - portfolio_volatility(x, *args)})
        result = sco.minimize(negative_return, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result

def run_analysis():
    print("--- Starting Portfolio Optimization ---")
    df_stocks, df_benchmark = load_data()
    
    # Calculate Returns
    returns = df_stocks.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    print(f"Number of assets: {len(mean_returns)}")
    
    results = []
    
    # --- SCENARIO 1: Volatility Caps (5%, 10%, 20%) ---
    # We assume standard weight constraint (0 to 1) for this, or maybe small cap?
    # The mandate says "based on the annual volatility capped at 5%, 10% and 20%"
    # So we find Max Return for these Vol caps.
    
    vol_caps = [0.05, 0.10, 0.20]
    
    for v_cap in vol_caps:
        print(f"Optimizing for Volatility Cap: {v_cap*100}%...")
        res = optimize_portfolio(mean_returns, cov_matrix, constraint_type='target_vol', target_vol=v_cap)
        
        if res.success:
            ret, vol, sharpe, var = get_portfolio_metrics(res.x, mean_returns, cov_matrix)
            results.append({
                'Scenario': f'Vol Cap {v_cap*100}%',
                'Return': ret,
                'Volatility': vol,
                'Sharpe': sharpe,
                'VaR_95': var,
                'Weights': res.x
            })
        else:
            print(f"Failed to optimize for Vol Cap {v_cap}")

    # --- SCENARIO 2: Weight Caps (10%, 20%, 30%) ---
    # "based on the maximum component weights of 10%, 20% and 30%"
    # Usually we Maximize Sharpe for these weight caps.
    
    weight_caps = [0.10, 0.20, 0.30]
    
    for w_cap in weight_caps:
        print(f"Optimizing for Weight Cap: {w_cap*100}% (Max Sharpe)...")
        res = optimize_portfolio(mean_returns, cov_matrix, constraint_type='max_sharpe', max_weight=w_cap)
        
        if res.success:
            ret, vol, sharpe, var = get_portfolio_metrics(res.x, mean_returns, cov_matrix)
            results.append({
                'Scenario': f'Weight Cap {w_cap*100}%',
                'Return': ret,
                'Volatility': vol,
                'Sharpe': sharpe,
                'VaR_95': var,
                'Weights': res.x
            })
        else:
            print(f"Failed to optimize for Weight Cap {w_cap}")

    # --- BASE CASE: Unconstrained Max Sharpe (Weight <= 1.0) ---
    print("Optimizing Base Case (Max Sharpe)...")
    res = optimize_portfolio(mean_returns, cov_matrix, constraint_type='max_sharpe')
    if res.success:
        ret, vol, sharpe, var = get_portfolio_metrics(res.x, mean_returns, cov_matrix)
        results.append({
            'Scenario': 'Base Case (Max Sharpe)',
            'Return': ret,
            'Volatility': vol,
            'Sharpe': sharpe,
            'VaR_95': var,
            'Weights': res.x
        })

    # --- MIN VOLATILITY ---
    print("Optimizing Min Volatility...")
    res = optimize_portfolio(mean_returns, cov_matrix, constraint_type='min_vol')
    if res.success:
        ret, vol, sharpe, var = get_portfolio_metrics(res.x, mean_returns, cov_matrix)
        results.append({
            'Scenario': 'Min Volatility',
            'Return': ret,
            'Volatility': vol,
            'Sharpe': sharpe,
            'VaR_95': var,
            'Weights': res.x
        })

    # Save Results
    df_res = pd.DataFrame(results)
    # Drop weights column for summary CSV, save separately
    df_summary = df_res.drop(columns=['Weights'])
    df_summary.to_csv('optimization_results_summary.csv', index=False)
    
    # Save Weights
    weights_dict = {}
    for i, row in df_res.iterrows():
        weights_dict[row['Scenario']] = row['Weights']
    
    df_weights = pd.DataFrame(weights_dict, index=df_stocks.columns)
    df_weights.to_csv('optimization_weights.csv')
    
    print("\n--- OPTIMIZATION RESULTS ---")
    print(df_summary)
    print("\nSaved results to 'optimization_results_summary.csv' and 'optimization_weights.csv'")

if __name__ == "__main__":
    run_analysis()
