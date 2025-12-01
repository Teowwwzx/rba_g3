import numpy as np
import scipy.optimize as sco
from scipy.stats import norm

def portfolio_performance(weights, mean_returns, cov_matrix):
    """Calculates portfolio return and volatility."""
    returns = np.sum(mean_returns * weights) * 252
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
    return returns, std

def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
    """Negative Sharpe Ratio for minimization."""
    p_ret, p_var = portfolio_performance(weights, mean_returns, cov_matrix)
    return -(p_ret - risk_free_rate) / p_var

def minimize_volatility(weights, mean_returns, cov_matrix):
    """Returns volatility for minimization."""
    p_ret, p_var = portfolio_performance(weights, mean_returns, cov_matrix)
    return p_var

def calculate_var(weights, mean_returns, cov_matrix, confidence_level=0.05):
    """Calculates Parametric VaR (Daily)."""
    # Daily metrics
    p_ret_daily = np.sum(mean_returns * weights)
    p_std_daily = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    # Z-score for confidence level (e.g. 1.645 for 95%)
    z_score = norm.ppf(1 - confidence_level)
    
    # VaR = Mean - (Z * Std)
    # But usually VaR is expressed as a loss (negative number) or positive loss amount.
    # Assignment says "capped at -1.5% maximum", implying VaR is a negative return.
    # So we want the 5th percentile return.
    
    var_return = p_ret_daily - (z_score * p_std_daily)
    return var_return

def run_optimization(name, mean_returns, cov_matrix, risk_free_rate, vol_cap=None, weight_cap=None, var_limit=-0.015):
    """Runs the optimization for a specific scenario."""
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
    
    # Constraints
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}] # Sum of weights = 1
    
    if vol_cap:
        # Annual Volatility <= vol_cap
        constraints.append({'type': 'ineq', 'fun': lambda x: vol_cap - portfolio_performance(x, mean_returns, cov_matrix)[1]})
        
    # VaR Constraint (Daily VaR >= -1.5%)
    # Note: Optimization with VaR constraint can be unstable.
    # constraints.append({'type': 'ineq', 'fun': lambda x: calculate_var(x, mean_returns, cov_matrix) - var_limit})

    # Bounds
    max_w = weight_cap if weight_cap else 1.0
    bounds = tuple((0, max_w) for asset in range(num_assets))
    
    # Initial Guess
    init_guess = num_assets * [1. / num_assets,]
    
    try:
        result = sco.minimize(neg_sharpe_ratio, init_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints,
                              options={'maxiter': 1000})
        return result, "Success"
    except Exception as e:
        return None, str(e)

def get_min_volatility(mean_returns, cov_matrix):
    """Finds the global minimum volatility portfolio."""
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for asset in range(num_assets))
    init_guess = num_assets * [1. / num_assets,]
    
    result = sco.minimize(minimize_volatility, init_guess, args=args,
                          method='SLSQP', bounds=bounds, constraints=constraints)
    
    return result.fun # Already annualized in minimize_volatility
