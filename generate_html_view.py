import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import os
import datetime
import numpy as np

HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ace_market_companies_list.html')
OUTPUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

def generate_html():
    if not os.path.exists(HTML_FILE):
        print(f"Error: Could not find {HTML_FILE}")
        return
    else:
        html_path = HTML_FILE

    print(f"Reading HTML from: {html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    stocks = []
    tickers = []
    
    # 1. Parse HTML to get list of stocks
    for row in soup.find_all('tr'):
        # Code & Name
        link_name = row.find('a', class_='company-announcement-link')
        if link_name and 'stock_code=' in link_name['href']:
            code = link_name['href'].split('stock_code=')[1].split('&')[0]
            name = link_name.text.strip()
        else:
            continue

        # Website
        link_web = row.find('a', class_='company-website-link')
        website = link_web['href'] if link_web else '#'
        website_display = link_web.text.strip() if link_web else '-'

        stock_info = {
            'Code': code,
            'Name': name,
            'Website': website,
            'Website_Display': website_display,
            'Ticker': f"{code}.KL",
            'Has_6Y_Data': False,
            'Has_5Y_Data': False,
            'First_Date': '-',
            'Avg_Return': 0.0,
            'Avg_Return_Display': '-',
            'Today_Return': 0.0,
            'Today_Return_Display': '-',
            'YTD_Return': 0.0,
            'YTD_Return_Display': '-',
            '1Y_Return': 0.0,
            '1Y_Return_Display': '-'
        }
        stocks.append(stock_info)
        tickers.append(f"{code}.KL")

    # 2. Add Benchmark to tickers
    tickers.append('^KLSE')

    # 3. Check Data Availability & Calculate Returns (Batch Download)
    print(f"Downloading and analyzing data for {len(tickers)} tickers... (This may take a minute)")
    
    # Define 6 years ago
    today = datetime.date.today()
    six_years_ago = today - datetime.timedelta(days=365*6)
    five_years_ago = today - datetime.timedelta(days=365*5)
    start_date_check = six_years_ago - datetime.timedelta(days=30) # Buffer
    
    try:
        # Download Close prices
        # Use auto_adjust=False to get 'Adj Close' if possible
        data = yf.download(tickers, start=start_date_check, progress=True, auto_adjust=False, group_by='ticker')
        
        klse_data = None
        
        # Process each ticker
        for t in tickers:
            # Find matching stock info if it's a stock
            s = next((item for item in stocks if item["Ticker"] == t), None)
            
            # If it's KLSE, create a dummy dict
            if t == '^KLSE':
                s = {
                    'Code': '^KLSE',
                    'Name': 'FBMKLCI Benchmark',
                    'Ticker': '^KLSE',
                    'Website': '#',
                    'Website_Display': '-',
                    'Has_6Y_Data': False
                }
            
            if not s: continue

            try:
                # Handle multi-level columns
                if len(tickers) > 1:
                    if t in data.columns.levels[0]:
                        df_prices = data[t]
                    else:
                        continue
                else:
                    df_prices = data
                
                # Get Series
                if 'Adj Close' in df_prices.columns:
                    series = df_prices['Adj Close'].dropna()
                elif 'Close' in df_prices.columns:
                    series = df_prices['Close'].dropna()
                else:
                    continue
                    
                if len(series) > 0:
                    # 1. Check Date
                    first_date = series.index[0].date()
                    s['First_Date'] = first_date.strftime('%Y-%m-%d')
                    
                    if first_date <= six_years_ago:
                        s['Has_6Y_Data'] = True
                    
                    if first_date <= five_years_ago:
                        s['Has_5Y_Data'] = True
                    
                    # 2. Calculate Avg Daily Return
                    daily_returns = series.pct_change()
                    avg_ret = daily_returns.mean() * 100
                    
                    if not np.isnan(avg_ret):
                        s['Avg_Return'] = avg_ret
                        s['Avg_Return_Display'] = f"{avg_ret:.4f}%"
                        
                        # Get Last Price
                        last_price = series.iloc[-1]
                        s['Last_Price'] = last_price
                        
                        # Get Last Date
                        last_date = series.index[-1].date()
                        s['Last_Date'] = last_date.strftime('%Y-%m-%d')

                        # --- NEW METRICS ---
                        # 1. Today's Return
                        if len(daily_returns) > 0:
                            today_ret = daily_returns.iloc[-1]
                            if not np.isnan(today_ret):
                                s['Today_Return'] = today_ret * 100
                                s['Today_Return_Display'] = f"{today_ret*100:.2f}%"
                        
                        # 2. YTD Return
                        try:
                            current_year = series.index[-1].year
                            # Filter for current year
                            ytd_mask = series.index.year == current_year
                            if ytd_mask.any():
                                # Get the price at the start of the year (first available data point in current year)
                                # Or better: Price at end of last year (last data point of prev year)
                                # But for simplicity and robustness, let's use first data point of this year
                                start_price_ytd = series[ytd_mask].iloc[0]
                                ytd_ret = (last_price - start_price_ytd) / start_price_ytd
                                s['YTD_Return'] = ytd_ret * 100
                                s['YTD_Return_Display'] = f"{ytd_ret*100:.2f}%"
                        except Exception as e:
                            print(f"Error calc YTD for {t}: {e}")

                        # 3. 1 Year Return
                        try:
                            one_year_ago_date = series.index[-1] - datetime.timedelta(days=365)
                            # Find nearest index
                            # We need to ensure we don't go out of bounds if stock is young
                            if series.index[0] <= pd.Timestamp(one_year_ago_date):
                                idx = series.index.get_indexer([one_year_ago_date], method='nearest')[0]
                                if idx >= 0 and idx < len(series):
                                    price_1y = series.iloc[idx]
                                    one_y_ret = (last_price - price_1y) / price_1y
                                    s['1Y_Return'] = one_y_ret * 100
                                    s['1Y_Return_Display'] = f"{one_y_ret*100:.2f}%"
                        except Exception as e:
                            print(f"Error calc 1Y for {t}: {e}")
                        # -------------------
                        if t == '^KLSE':
                            s['Last_Price_Display'] = f"{last_price:.2f}"
                        else:
                            s['Last_Price_Display'] = f"RM {last_price:.3f}"
                        
                        # Yahoo Finance Link
                        s['Source_Link'] = f"https://finance.yahoo.com/quote/{s['Ticker']}"
                        
                        # 3. Generate Detail Page
                        output_dir = os.path.dirname(OUTPUT_HTML)
                        details_dir = os.path.join(output_dir, 'details')
                        if not os.path.exists(details_dir):
                            os.makedirs(details_dir)

                        if t == '^KLSE':
                            detail_filename = os.path.join(details_dir, "KLSE.html")
                            # Relative link for HTML
                            s['Detail_Link'] = "details/KLSE.html"
                        else:
                            detail_filename = os.path.join(details_dir, f"{s['Code']}.html")
                            # Relative link for HTML
                            s['Detail_Link'] = f"details/{s['Code']}.html"
                        
                        # Create DataFrame for display
                        df_detail = pd.DataFrame({
                            'Date': series.index,
                            'Adj Close': series.values,
                            'Daily Return': daily_returns.values
                        })
                        # Sort descending by date
                        df_detail = df_detail.sort_values('Date', ascending=False)
                        
                        # Find an example for the formula
                        example_html = ""
                        try:
                            if len(df_detail) >= 2:
                                row_today = df_detail.iloc[0]
                                row_yesterday = df_detail.iloc[1]
                                
                                price_today = row_today['Adj Close']
                                price_yesterday = row_yesterday['Adj Close']
                                return_val = row_today['Daily Return']
                                
                                if not np.isnan(return_val):
                                    example_html = f"""
                                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px dashed #bdc3c7;">
                                        <div class="formula-title">Example (Latest Data):</div>
                                        <p>
                                            <strong>Date:</strong> {row_today['Date'].strftime('%Y-%m-%d')}<br>
                                            <strong>Price Today:</strong> {price_today:.4f}<br>
                                            <strong>Price Yesterday:</strong> {price_yesterday:.4f}
                                        </p>
                                        <p style="font-family: monospace; background: #fff; padding: 10px; border-radius: 4px; border: 1px solid #ddd;">
                                            ({price_today:.4f} - {price_yesterday:.4f}) / {price_yesterday:.4f} = <strong>{return_val:.6f}</strong> ({return_val*100:.4f}%)
                                        </p>
                                    </div>
                                    """
                        except Exception as ex_calc:
                            print(f"Error creating example: {ex_calc}")

                        
                        # Get unique years for filter
                        years = sorted(df_detail['Date'].dt.year.unique(), reverse=True)
                        year_options = "".join([f'<option value="{y}">{y}</option>' for y in years])
                        
                        # Generate Detail HTML
                        detail_html = f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>{s['Name']} ({s['Code']}) - Data Details</title>
                            <style>
                                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; padding: 20px; margin: 0; }}
                                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                                h1 {{ color: #2c3e50; margin-bottom: 10px; }}
                                .header-info {{ margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
                                .back-link {{ display: inline-block; margin-bottom: 20px; color: #3498db; text-decoration: none; font-weight: 500; }}
                                .back-link:hover {{ text-decoration: underline; }}
                                
                                .formula-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #3498db; }}
                                .formula-title {{ font-weight: 600; margin-bottom: 5px; color: #2c3e50; }}
                                code {{ background-color: #e9ecef; padding: 2px 5px; border-radius: 4px; font-family: monospace; }}
                                
                                .controls {{ margin-bottom: 15px; text-align: right; }}
                                select {{ padding: 8px 12px; border-radius: 4px; border: 1px solid #ddd; font-size: 14px; }}
                                
                                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; }}
                                th, td {{ padding: 10px 15px; text-align: left; border-bottom: 1px solid #eee; }}
                                th {{ background-color: #f8f9fa; color: #2c3e50; font-weight: 600; position: sticky; top: 0; }}
                                .num {{ text-align: right; font-family: monospace; }}
                                .pos {{ color: #155724; }}
                                .neg {{ color: #721c24; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <a href="../ace_market_summary.html" class="back-link">&larr; Back to Summary</a>
                                
                                <div class="header-info">
                                    <h1>{s['Name']} ({s['Code']})</h1>
                                    <p><strong>Source:</strong> <a href="{s['Source_Link']}" target="_blank">Yahoo Finance ({s['Ticker']})</a></p>
                                    <p><strong>Last Price:</strong> {s['Last_Price_Display']}</p>
                                    <p><strong>First Data Date:</strong> {s['First_Date']}</p>
                                    <p><strong>Average Daily Return:</strong> {s['Avg_Return_Display']}</p>
                                </div>
                                
                                <div class="formula-box">
                                    <div class="formula-title">How is this calculated?</div>
                                    <p><strong>Daily Return</strong> = (Price<sub>Today</sub> - Price<sub>Yesterday</sub>) / Price<sub>Yesterday</sub></p>
                                    <p><strong>Avg Daily Return</strong> = Average of all "Daily Return" values shown below.</p>
                                    {example_html}
                                </div>

                                <div class="controls">
                                    <label for="yearFilter">Filter by Year: </label>
                                    <select id="yearFilter" onchange="filterByYear()">
                                        <option value="all">All Years</option>
                                        {year_options}
                                    </select>
                                </div>

                                <table id="dataTable">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th class="num">Adj Close Price</th>
                                            <th class="num">Daily Return</th>
                                            <th class="num">Daily Return %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                        """
                        
                        for _, row in df_detail.iterrows():
                            date_str = row['Date'].strftime('%Y-%m-%d')
                            year = row['Date'].year
                            price = row['Adj Close']
                            ret = row['Daily Return']
                            
                            if np.isnan(ret):
                                ret_str = "-"
                                ret_pct_str = "-"
                                color_class = ""
                            else:
                                ret_str = f"{ret:.6f}"
                                ret_pct_str = f"{ret*100:.4f}%"
                                color_class = "pos" if ret >= 0 else "neg"
                                
                            detail_html += f"""
                                        <tr data-year="{year}">
                                            <td>{date_str}</td>
                                            <td class="num">{price:.4f}</td>
                                            <td class="num {color_class}">{ret_str}</td>
                                            <td class="num {color_class}">{ret_pct_str}</td>
                                        </tr>
                            """
                            
                        detail_html += """
                                    </tbody>
                                </table>
                            </div>
                            
                            <script>
                                function filterByYear() {
                                    var filter = document.getElementById("yearFilter").value;
                                    var table = document.getElementById("dataTable");
                                    var tr = table.getElementsByTagName("tr");
                                    
                                    for (var i = 1; i < tr.length; i++) {
                                        var rowYear = tr[i].getAttribute("data-year");
                                        if (filter === "all" || rowYear === filter) {
                                            tr[i].style.display = "";
                                        } else {
                                            tr[i].style.display = "none";
                                        }
                                    }
                                }
                            </script>
                        </body>
                        </html>
                        """
                        
                        with open(detail_filename, 'w', encoding='utf-8') as f_detail:
                            f_detail.write(detail_html)
                            
                        if t == '^KLSE':
                            klse_data = s

            except Exception as e:
                print(f"Error processing {t}: {e}")
            
    except Exception as e:
        print(f"Error downloading data: {e}")

    # 3. Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ACE Market Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <div>
                    <h1>ACE Market Analytics</h1>
                    <div class="date">Last Updated: {datetime.date.today().strftime('%B %d, %Y')}</div>
                </div>
                <div>
                    <!-- Optional Header Actions -->
                </div>
            </div>

            <!-- Summary Cards -->
            <div class="summary-grid">
                <div class="card">
                    <div class="card-title">Market Benchmark (KLCI)</div>
                    <div class="card-value">
                        {klse_data['Last_Price_Display'] if klse_data else '-'}
                    </div>
                    <div class="card-sub">
                        Daily Return: <span class="{ 'text-green' if klse_data and klse_data.get('Today_Return', 0) >= 0 else 'text-red' }">
                            {klse_data['Today_Return_Display'] if klse_data and 'Today_Return_Display' in klse_data else '-'}
                        </span>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Risk Free Rate (10Y Bond)</div>
                    <div class="card-value">4.00%</div>
                    <div class="card-sub text-muted">Fixed Assumption</div>
                </div>
                <div class="card">
                    <div class="card-title">Total Companies</div>
                    <div class="card-value">{len(stocks)}</div>
                    <div class="card-sub text-muted">
                        {sum(1 for s in stocks if s['Has_6Y_Data'])} with 6Y Data
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Target Stocks (>0.25% Avg Ret)</div>
                    <div class="card-value">
                        {sum(1 for s in stocks if s['Has_6Y_Data'] and s['Avg_Return'] >= 0.25)}
                    </div>
                    <div class="card-sub text-green">High Potential</div>
                </div>
            </div>

            <!-- Controls -->
            <div class="controls-bar">
                <div class="search-wrapper">
                    <input type="text" id="searchInput" placeholder="Search company name or code..." onkeyup="filterTable()">
                </div>
                <div style="min-width: 200px;">
                    <select id="dataFilter" onchange="filterTable()">
                        <option value="target">Target Stocks (6Y Data & >0.25% Ret)</option>
                        <option value="qualified">Has > 6 Years Data</option>
                        <option value="has_5y">Has > 5 Years Data</option>
                        <option value="all">Show All Stocks</option>
                        <option value="unqualified">Less than 6Y Data</option>
                    </select>
                </div>
                
                <!-- View Options -->
                <div class="view-options">
                    <button class="view-btn" onclick="toggleViewMenu()">
                        <span>View Options</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 9l6 6 6-6"/>
                        </svg>
                    </button>
                    <div id="viewMenu" class="view-menu">
                        <label class="view-item">
                            <input type="checkbox" checked onchange="toggleColumnGroup('col-live', this.checked)"> Live Data
                        </label>
                        <label class="view-item">
                            <input type="checkbox" checked onchange="toggleColumnGroup('col-perf', this.checked)"> Performance
                        </label>
                        <label class="view-item">
                            <input type="checkbox" checked onchange="toggleColumnGroup('col-status', this.checked)"> Status
                        </label>
                    </div>
                </div>

                <!-- Export Button -->
                <button class="view-btn" onclick="exportTableToCSV('stock_summary.csv')" style="margin-left: auto;">
                    <span>Export to Excel</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </button>
            </div>

            <!-- Main Table -->
            <div class="table-container">
                <div class="table-responsive">
                    <table id="stockTable">
                        <thead>
                            <!-- Category Headers -->
                            <tr style="background: #f8fafc; border-bottom: 1px solid var(--border-color);">
                                <th colspan="3" style="text-align: center; color: var(--text-main); border-right: 1px solid var(--border-color);">Company Identity</th>
                                <th colspan="3" class="col-live" style="text-align: center; color: var(--text-main); border-right: 1px solid var(--border-color);">Live Data</th>
                                <th colspan="3" class="col-perf" style="text-align: center; color: var(--text-main); border-right: 1px solid var(--border-color);">Performance</th>
                                <th colspan="2" class="col-status" style="text-align: center; color: var(--text-main);">Status</th>
                                <th></th>
                            </tr>
                            <!-- Column Headers -->
                            <tr>
                                <th style="width: 50px;">#</th>
                                <th onclick="sortTable(1)">Code</th>
                                <th onclick="sortTable(2)" style="border-right: 1px solid var(--border-color);">Company</th>
                                
                                <th onclick="sortTable(3)" class="num col-live">Last Price</th>
                                <th onclick="sortTable(4)" class="col-live">Last Update</th>
                                <th onclick="sortTable(5)" class="num col-live" style="border-right: 1px solid var(--border-color);">
                                    <div class="tooltip">Today %
                                        <span class="tooltiptext">Change from previous close to last price</span>
                                    </div>
                                </th>
                                
                                <th onclick="sortTable(6)" class="num col-perf">YTD %</th>
                                <th onclick="sortTable(7)" class="num col-perf">1Y %</th>
                                <th onclick="sortTable(8)" class="num col-perf" style="border-right: 1px solid var(--border-color);">Avg Daily %</th>
                                
                                <th onclick="sortTable(9)" class="col-status">Data Since</th>
                                <th onclick="sortTable(10)" class="col-status">
                                    <div class="tooltip">Data Criteria
                                        <span class="tooltiptext">Requires >6 years of historical data</span>
                                    </div>
                                </th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for i, s in enumerate(stocks):
        if s['Code'] == '^KLSE': continue # Skip KLSE in main table
        
        # Determine Status
        if s['Has_6Y_Data']:
            status_html = '<span class="status-pill status-success">Has 6Y Data</span>'
            status_val = "qualified"
        elif s['Has_5Y_Data']:
            status_html = '<span class="status-pill status-warning">Has 5Y Data</span>'
            status_val = "has_5y"
        else:
            status_html = '<span class="status-pill status-error">< 5Y Data</span>'
            status_val = "unqualified"
            
        # High Return Flag
        is_high_return = "true" if s['Avg_Return'] >= 0.25 else "false"
        
        # Helper for color class
        def get_color(val):
            if val > 0: return "text-green"
            if val < 0: return "text-red"
            return ""
            
        # Data Links
        if 'Detail_Link' in s:
            btn_html = f'<a href="{s["Detail_Link"]}" class="btn-action" target="_blank">View</a>'
        else:
            btn_html = '<span class="btn-action btn-disabled">No Data</span>'
            
        html_content += f"""
                            <tr data-status="{status_val}" data-high-return="{is_high_return}">
                                <td>{i}</td>
                                <td><span class="badge">{s['Code']}</span></td>
                                <td style="border-right: 1px solid var(--border-color);">
                                    <div style="font-weight: 500;">{s['Name']}</div>
                                    <a href="{s['Website']}" target="_blank" style="font-size: 12px; color: #94a3b8; text-decoration: none;">{s['Website_Display']}</a>
                                </td>
                                
                                <td class="num col-live" data-sort="{s.get('Last_Price', 0)}">{s.get('Last_Price_Display', '-')}</td>
                                
                                <td class="col-live" data-sort="{s.get('Last_Date', '0000-00-00')}">{s.get('Last_Date', '-')}</td>
                                
                                <td class="num col-live {get_color(s.get('Today_Return', 0))}" data-sort="{s.get('Today_Return', 0)}" style="border-right: 1px solid var(--border-color);">
                                    {s.get('Today_Return_Display', '-')}
                                </td>
                                
                                <td class="num col-perf {get_color(s.get('YTD_Return', 0))}" data-sort="{s.get('YTD_Return', 0)}">
                                    {s.get('YTD_Return_Display', '-')}
                                </td>
                                
                                <td class="num col-perf {get_color(s.get('1Y_Return', 0))}" data-sort="{s.get('1Y_Return', 0)}">
                                    {s.get('1Y_Return_Display', '-')}
                                </td>
                                
                                <td class="num col-perf {get_color(s.get('Avg_Return', 0))}" data-sort="{s.get('Avg_Return', 0)}" style="border-right: 1px solid var(--border-color);">
                                    {s.get('Avg_Return_Display', '-')}
                                </td>
                                
                                <td class="col-status" data-sort="{s['First_Date']}">{s['First_Date']}</td>
                                <td class="col-status" data-sort="{status_val}">
                                    {status_html}
                                    <!-- Hidden data attributes for multi-filter logic -->
                                    <span style="display:none;" data-has-6y="{str(s['Has_6Y_Data']).lower()}" data-has-5y="{str(s['Has_5Y_Data']).lower()}"></span>
                                </td>
                                <td>
                                    {btn_html}
                                    <div style="margin-top: 4px;">
                                        <a href="{s.get('Source_Link', '#')}" target="_blank" class="source-link">Yahoo</a>
                                    </div>
                                </td>
                            </tr>
        """

    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            // Initialize with Target Stocks filter
            window.onload = function() {
                filterTable();
            };

            function toggleViewMenu() {
                document.getElementById('viewMenu').classList.toggle('show');
            }
            
            // Close menu when clicking outside
            window.onclick = function(event) {
                if (!event.target.matches('.view-btn') && !event.target.closest('.view-btn') && !event.target.closest('.view-menu')) {
                    var dropdowns = document.getElementsByClassName("view-menu");
                    for (var i = 0; i < dropdowns.length; i++) {
                        var openDropdown = dropdowns[i];
                        if (openDropdown.classList.contains('show')) {
                            openDropdown.classList.remove('show');
                        }
                    }
                }
            }

            function toggleColumnGroup(className, isVisible) {
                const elements = document.getElementsByClassName(className);
                for (let i = 0; i < elements.length; i++) {
                    elements[i].style.display = isVisible ? "" : "none";
                }
            }

            function filterTable() {
                const searchInput = document.getElementById('searchInput').value.toUpperCase();
                const filterValue = document.getElementById('dataFilter').value;
                const table = document.getElementById('stockTable');
                const tr = table.getElementsByTagName('tr');
                
                let visibleCount = 0;

                // Start from 2 to skip the two header rows
                for (let i = 2; i < tr.length; i++) {
                    let showRow = true;
                    const row = tr[i];
                    
                    // Safety check: ensure it's a data row
                    if (row.getElementsByTagName('td').length === 0) continue;
                    
                    // Search
                    const code = row.getElementsByTagName('td')[1].textContent || "";
                    const name = row.getElementsByTagName('td')[2].textContent || "";
                    
                    if (code.toUpperCase().indexOf(searchInput) === -1 && 
                        name.toUpperCase().indexOf(searchInput) === -1) {
                        showRow = false;
                    }
                    
                    // Filter
                    const status = row.getAttribute('data-status');
                    const isHighReturn = row.getAttribute('data-high-return');
                    
                    // Get hidden data attributes for more complex checks
                    const statusCell = row.getElementsByTagName('td')[10];
                    const metaSpan = statusCell.getElementsByTagName('span')[1]; // The hidden span
                    const has6Y = metaSpan ? metaSpan.getAttribute('data-has-6y') === 'true' : false;
                    const has5Y = metaSpan ? metaSpan.getAttribute('data-has-5y') === 'true' : false;

                    if (filterValue === 'target') {
                        if (!has6Y || isHighReturn !== 'true') showRow = false;
                    } else if (filterValue === 'qualified') {
                        if (!has6Y) showRow = false;
                    } else if (filterValue === 'has_5y') {
                        if (!has5Y) showRow = false;
                    } else if (filterValue === 'unqualified') {
                        // Show anything that doesn't have 6Y data
                        if (has6Y) showRow = false;
                    }
                    // 'all' shows everything (if search matches)
                    
                    row.style.display = showRow ? "" : "none";
                    if (showRow) visibleCount++;
                }
            }
            
            function sortTable(n) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("stockTable");
                switching = true;
                dir = "asc";
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    // Start from 2 to skip the two header rows
                    for (i = 2; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        
                        // Safety check
                        if (!x || !y) continue;
                        
                        var xVal = x.getAttribute('data-sort') || x.innerText.toLowerCase();
                        var yVal = y.getAttribute('data-sort') || y.innerText.toLowerCase();
                        
                        // Check if numeric
                        if (!isNaN(parseFloat(xVal)) && isFinite(xVal)) {
                            xVal = parseFloat(xVal);
                            yVal = parseFloat(yVal);
                        }

                        if (dir == "asc") {
                            if (xVal > yVal) { shouldSwitch = true; break; }
                        } else if (dir == "desc") {
                            if (xVal < yVal) { shouldSwitch = true; break; }
                        }
                    }
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount ++;
                    } else {
                        if (switchcount == 0 && dir == "asc") {
                            dir = "desc";
                            switching = true;
                        }
                    }
                }
            }

            function exportTableToCSV(filename) {
                var csv = [];
                var rows = document.querySelectorAll("table tr");
                
                // Get headers (skip first row which is categories)
                var headerRow = rows[1];
                var headers = [];
                var cols = headerRow.querySelectorAll("td, th");
                for (var j = 0; j < cols.length - 1; j++) { // Skip Actions column
                    headers.push('"' + cols[j].innerText.replace(/\\n/g, " ").trim() + '"');
                }
                csv.push(headers.join(","));

                // Get data
                for (var i = 2; i < rows.length; i++) {
                    var row = [], cols = rows[i].querySelectorAll("td, th");
                    
                    // Skip hidden rows
                    if (rows[i].style.display === 'none') continue;
                    
                    for (var j = 0; j < cols.length - 1; j++) { // Skip Actions column
                        var data = cols[j].innerText.replace(/(\\r\\n|\\n|\\r)/gm, "").replace(/\\s+/g, " ").trim();
                        row.push('"' + data + '"');
                    }
                    csv.push(row.join(","));
                }

                downloadCSV(csv.join("\\n"), filename);
            }

            function downloadCSV(csv, filename) {
                var csvFile;
                var downloadLink;

                csvFile = new Blob([csv], {type: "text/csv"});
                downloadLink = document.createElement("a");
                downloadLink.download = filename;
                downloadLink.href = window.URL.createObjectURL(csvFile);
                downloadLink.style.display = "none";
                document.body.appendChild(downloadLink);
                downloadLink.click();
            }
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html()
