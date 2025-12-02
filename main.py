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
    print("Step 1: Fetching Data from Local Datasets...")
    try:
        # Load Data from Local Datasets
        # This returns processed_stocks (list of dicts) and klci_data (dict)
        processed_stocks, klci_data = data_manager.load_data_from_local_datasets('datasets')
        
        # Load Bond Yield
        # We use the processed bond dataset
        bond_yield_series = data_manager.get_bond_yield_data('datasets/dataset_bond_yield.csv')
        current_risk_free_rate = RISK_FREE_RATE
        if bond_yield_series is not None and not bond_yield_series.empty:
            current_risk_free_rate = bond_yield_series.iloc[-1]
            print(f"Using latest Bond Yield as Risk-Free Rate: {current_risk_free_rate*100:.2f}%")
        else:
            print(f"Using default Risk-Free Rate: {current_risk_free_rate*100:.2f}%")

    except Exception as e:
        print(f"Error in data fetching: {e}")
        return

    # 2. Portfolio Optimization Prep
    print("Step 2: Preparing for Optimization...")
    # We need to filter for stocks that have enough data for optimization (e.g. 6Y or just Qualified)
    # Let's use Qualified stocks for optimization candidates if they have enough history
    # Or stick to the original logic which used 'Has_6Y_Data'.
    # data_manager.load_data_from_local_datasets calculates metrics but maybe not 'Has_6Y_Data' explicitly?
    # Let's check data_manager.py again. It calculates metrics but didn't set 'Has_6Y_Data'.
    # We should probably add 'Has_6Y_Data' logic in data_manager or here.
    # For now, let's assume we use Qualified stocks for optimization or just top stocks by return.
    
    # Let's add Has_6Y_Data logic back if it's missing, or rely on what we have.
    # Actually, let's just use the 'Qualified' stocks for optimization as they are the "good" ones.
    
    # Update 'Has_6Y_Data' for compatibility with prepare_optimization_data
    for s in processed_stocks:
        if 'Series' in s:
            years = len(s['Series']) / 252.0
            s['Has_6Y_Data'] = years >= 6.0
            
    top_stocks, df_prices = data_manager.prepare_optimization_data(processed_stocks)
    print(f"Selected {len(top_stocks)} stocks for optimization.")
    
    # Calculate Mean Returns and Covariance Matrix
    daily_returns = df_prices.pct_change().dropna()
    mean_returns = daily_returns.mean()
    cov_matrix = daily_returns.cov()
    
    # Calculate Market Breakdown in Top 50
    ace_count = sum(1 for s in top_stocks if s.get('Market') == 'ACE')
    main_count = sum(1 for s in top_stocks if s.get('Market') == 'Main')
    breakdown_html = f"<div class='card-sub text-muted'>Selected 50 stocks: <strong>{ace_count} ACE</strong>, <strong>{main_count} Main</strong> Market</div>"

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
            res, msg = portfolio_optimizer.run_optimization(f"Vol Cap {v_cap*100}%", mean_returns, cov_matrix, current_risk_free_rate, vol_cap=v_cap)
            if res and res.success:
                ret, vol = portfolio_optimizer.portfolio_performance(res.x, mean_returns, cov_matrix)
                sharpe = (ret - current_risk_free_rate) / vol
                var = portfolio_optimizer.calculate_var(res.x, mean_returns, cov_matrix)
                link = html_generator.generate_scenario_html(f"Vol Cap {v_cap*100}%", res.x, mean_returns, cov_matrix, ret, vol, sharpe, var, top_stocks[0]['Ticker'], processed_stocks)
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
        res, msg = portfolio_optimizer.run_optimization(f"Weight Cap {w_cap*100}%", mean_returns, cov_matrix, current_risk_free_rate, weight_cap=w_cap)
        if res and res.success:
            ret, vol = portfolio_optimizer.portfolio_performance(res.x, mean_returns, cov_matrix)
            sharpe = (ret - current_risk_free_rate) / vol
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
    if klci_data:
        m_ret = klci_data.get('1Y_Return', 0)
        market_return_str = f"{m_ret:.2f}%"
        if m_ret >= 0:
            market_color = "text-green"
            market_arrow = "▲"
        else:
            market_color = "text-red"
            market_arrow = "▼"
            
    valid_performers = [s for s in processed_stocks if s.get('Has_6Y_Data')]
    
    # Calculate detailed coverage
    ace_coverage = sum(1 for s in valid_performers if s.get('Market') == 'ACE')
    main_coverage = sum(1 for s in valid_performers if s.get('Market') == 'Main')
    
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
        'coverage_count': f"{len(valid_performers)}/{len(processed_stocks)}",
        'coverage_detail': f"({ace_coverage} ACE, {main_coverage} Main) with 6Y data"
    }
    
    # Generate Table Rows
    table_rows = ""
    for s in processed_stocks:
        # Determine status
        # Qualified: Determined by data_manager based on cleaned datasets
        is_qualified = s.get('Qualified', False)
        
        status_class = "status-unqualified"
        status_text = "Unqualified"
        if is_qualified:
            status_class = "status-qualified"
            status_text = "Qualified"
            
        # Color for changes
        last_price = s.get('Last_Price', 0)
        
        avg_ret = s.get('Avg_Return', 0)
        avg_ret_class = "text-green" if avg_ret >= 0 else "text-red"
        
        one_y_ret = s.get('1Y_Return')
        if one_y_ret is not None:
            one_y_ret_str = f"{one_y_ret:.2f}%"
            one_y_ret_class = "text-green" if one_y_ret >= 0 else "text-red"
        else:
            one_y_ret_str = "-"
            one_y_ret_class = ""
        
        market_type = s.get('Market', 'ACE')
        badge_class = 'badge-ace' if market_type == 'ACE' else 'badge-main'
        market_badge = f"<span class='badge-market {badge_class}'>{market_type}</span>"
        
        # Generate Detail Page
        html_generator.generate_stock_detail_html(s, market_metrics, s.get('Series'))
        
        row = f"""
        <tr data-qualified="{str(is_qualified).lower()}">
            <td>{s['Code']}</td>
            <td>{s['Name']}</td>
            <td>{market_badge}</td>
            <td class="num col-live">{last_price:.3f}</td>
            <td class="num col-perf {avg_ret_class}">{avg_ret:.4f}</td>
            <td class="num col-perf">{s.get('Std_Dev', 0):.4f}</td>
            <td class="num col-perf {one_y_ret_class}">{one_y_ret_str}</td>
            <td class="num col-perf">{(avg_ret*252 - current_risk_free_rate)/(s.get('Std_Dev', 1)*np.sqrt(252)):.2f}</td>
            <td class="col-status"><span class="status-badge {status_class}">{status_text}</span></td>
            <td class="col-status"><a href="details/{s['Code']}.html" target="_blank">Details</a></td>
        </tr>
        """
        table_rows += row
    
    final_results_html = breakdown_html + results_html

    html_content = html_generator.generate_main_html(processed_stocks, market_metrics, final_results_html, table_rows)
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
