import data_manager
import portfolio_optimizer
import html_generator
import pandas as pd
import numpy as np
import os

# Configuration
HTML_FILE = 'ace_market_companies_list.html'
OUTPUT_HTML = 'index.html'
RISK_FREE_RATE = 0.04

def main():
    print("--- RBA Robo-Advisor Generator ---")
    
    # 1. Data Fetching
    print("Step 1: Fetching Data...")
    try:
        stocks = data_manager.get_stock_list(HTML_FILE)
        # For testing, we can limit stocks if needed, but let's do all
        processed_stocks, klse_data = data_manager.download_and_process_data(stocks, '2018-01-01', '2024-12-31')
    except Exception as e:
        print(f"Error in data fetching: {e}")
        return

    # 2. Portfolio Optimization Prep
    print("Step 2: Preparing for Optimization...")
    top_stocks, df_prices = data_manager.prepare_optimization_data(processed_stocks)
    print(f"Selected {len(top_stocks)} stocks for optimization.")
    
    # Calculate Mean Returns and Covariance Matrix
    daily_returns = df_prices.pct_change().dropna()
    mean_returns = daily_returns.mean()
    cov_matrix = daily_returns.cov()
    
    # 3. Run Optimization Scenarios
    print("Step 3: Running Optimization Scenarios...")
    results_html = ""
    
    # Scenario 1: Volatility Caps
    results_html += "<h3>Scenario 1: Volatility Caps</h3><table class='opt-table'><tr><th>Cap</th><th>Return</th><th>Volatility</th><th>Sharpe</th><th>VaR (Daily)</th><th>Details</th></tr>"
    vol_caps = [0.05, 0.10, 0.20]
    min_vol = portfolio_optimizer.get_min_volatility(mean_returns, cov_matrix)
    print(f"Minimum Achievable Volatility: {min_vol*100:.2f}%")
    
    for v_cap in vol_caps:
        if v_cap < min_vol:
            results_html += f"<tr><td>{v_cap*100}%</td><td colspan='4'>Infeasible (Min Vol: {min_vol*100:.2f}%)</td><td>-</td></tr>"
        else:
            res, msg = portfolio_optimizer.run_optimization(f"Vol Cap {v_cap*100}%", mean_returns, cov_matrix, RISK_FREE_RATE, vol_cap=v_cap)
            if res and res.success:
                ret, vol = portfolio_optimizer.portfolio_performance(res.x, mean_returns, cov_matrix)
                sharpe = (ret - RISK_FREE_RATE) / vol
                var = portfolio_optimizer.calculate_var(res.x, mean_returns, cov_matrix)
                link = html_generator.generate_scenario_html(f"Vol Cap {v_cap*100}%", res.x, mean_returns, cov_matrix, ret, vol, sharpe, var, top_stocks[0]['Ticker'], processed_stocks) # Need tickers list
                results_html += f"<tr><td>{v_cap*100}%</td><td>{ret*100:.2f}%</td><td>{vol*100:.2f}%</td><td>{sharpe:.2f}</td><td>{var*100:.2f}%</td><td><a href='{link}'>View Calculation</a></td></tr>"
            else:
                results_html += f"<tr><td>{v_cap*100}%</td><td colspan='4'>Failed: {msg}</td><td>-</td></tr>"
    results_html += "</table>"
    
    # Scenario 2: Weight Caps
    results_html += "<h3>Scenario 2: Weight Caps</h3><table class='opt-table'><tr><th>Cap</th><th>Return</th><th>Volatility</th><th>Sharpe</th><th>VaR (Daily)</th><th>Details</th></tr>"
    weight_caps = [0.10, 0.20, 0.30]
    
    # Prepare tickers list for detail page generation
    tickers_list = [s['Ticker'] for s in top_stocks]
    
    for w_cap in weight_caps:
        res, msg = portfolio_optimizer.run_optimization(f"Weight Cap {w_cap*100}%", mean_returns, cov_matrix, RISK_FREE_RATE, weight_cap=w_cap)
        if res and res.success:
            ret, vol = portfolio_optimizer.portfolio_performance(res.x, mean_returns, cov_matrix)
            sharpe = (ret - RISK_FREE_RATE) / vol
            var = portfolio_optimizer.calculate_var(res.x, mean_returns, cov_matrix)
            
            link = html_generator.generate_scenario_html(
                f"Weight Cap {w_cap*100}%", 
                res.x, 
                mean_returns, 
                cov_matrix, 
                ret, vol, sharpe, var, 
                tickers_list, 
                processed_stocks
            )
            
            results_html += f"<tr><td>{w_cap*100}%</td><td>{ret*100:.2f}%</td><td>{vol*100:.2f}%</td><td>{sharpe:.2f}</td><td>{var*100:.2f}%</td><td><a href='{link}'>View Calculation</a></td></tr>"
        else:
             results_html += f"<tr><td>{w_cap*100}%</td><td colspan='4'>Failed: {msg}</td><td>-</td></tr>"
    results_html += "</table>"

    # 4. Generate Main HTML
    print("Step 4: Generating Dashboard...")
    
    # Calculate Market Metrics
    market_return_str = "-"
    market_color = "text-muted"
    market_arrow = ""
    if klse_data:
        m_ret = klse_data.get('1Y_Return', 0)
        market_return_str = f"{m_ret:.2f}%"
        if m_ret >= 0:
            market_color = "text-green"
            market_arrow = "▲"
        else:
            market_color = "text-red"
            market_arrow = "▼"
            
    valid_performers = [s for s in processed_stocks if s.get('Has_6Y_Data')]
    if valid_performers:
        top_performer = max(valid_performers, key=lambda x: x.get('1Y_Return', -999))
        avg_daily = sum(s['Avg_Return'] for s in valid_performers) / len(valid_performers)
    else:
        top_performer = {'Ticker': '-', '1Y_Return': 0}
        avg_daily = 0
        
    market_metrics = {
        'return_str': market_return_str,
        'color': market_color,
        'arrow': market_arrow,
        'top_ticker': top_performer['Ticker'],
        'top_return': top_performer.get('1Y_Return', 0),
        'avg_daily': avg_daily,
        'coverage': f"{len(valid_performers)}/{len(processed_stocks)}"
    }
    
    # Generate Table Rows
    table_rows = ""
    for s in processed_stocks:
        # Determine status
        # Target: >6Y Data AND Avg Daily Return >= 0.25% (0.0025)
        is_target = s.get('Has_6Y_Data', False) and s.get('Avg_Return', 0) >= 0.0025
        is_qualified = s.get('Has_6Y_Data', False)
        has_5y = True # Simplified for now
        
        status_class = "status-unqualified"
        status_text = "Unqualified"
        if is_target:
            status_class = "status-target"
            status_text = "Target"
        elif is_qualified:
            status_class = "status-qualified"
            status_text = "Qualified"
            
        # Color for changes
        # Use text-green / text-red from style.css
        last_price = s.get('Last_Price', 0)
        # We don't have 'Change' or 'Today_Return' calculated in data_manager yet, 
        # but let's assume if we did, or just use 1Y Return for color demo if needed.
        # For now, let's color 1Y Return and Avg Daily Return.
        
        avg_ret = s.get('Avg_Return', 0)
        avg_ret_class = "text-green" if avg_ret >= 0 else "text-red"
        
        one_y_ret = s.get('1Y_Return')
        if one_y_ret is not None:
            one_y_ret_str = f"{one_y_ret:.2f}%"
            one_y_ret_class = "text-green" if one_y_ret >= 0 else "text-red"
        else:
            one_y_ret_str = "-"
            one_y_ret_class = ""
        
        row = f"""
        <tr data-target="{str(is_target).lower()}" data-qualified="{str(is_qualified).lower()}" data-has5y="true">
            <td>{s['Code']}</td>
            <td>{s['Name']}</td>
            <td class="num col-live">{last_price:.3f}</td>
            <td class="num col-live">-</td>
            <td class="num col-live">-</td>
            <td class="num col-perf {avg_ret_class}">{avg_ret:.4f}</td>
            <td class="num col-perf">{s.get('Std_Dev', 0):.4f}</td>
            <td class="num col-perf {one_y_ret_class}">{one_y_ret_str}</td>
            <td class="num col-perf">{(avg_ret*252 - 0.04)/(s.get('Std_Dev', 1)*np.sqrt(252)):.2f}</td>
            <td class="col-status"><span class="status-badge {status_class}">{status_text}</span></td>
            <td class="col-status"><a href="https://finance.yahoo.com/quote/{s['Ticker']}" target="_blank">Yahoo</a></td>
        </tr>
        """
        table_rows += row

    html_content = html_generator.generate_main_html(processed_stocks, market_metrics, results_html, table_rows)
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
