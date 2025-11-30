import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import os
import datetime
import numpy as np

HTML_FILE = '../ace_market_companies_list.html'
OUTPUT_HTML = 'ace_market_summary.html'

def generate_html():
    if not os.path.exists(HTML_FILE):
        html_path = 'C:/Users/teowz/OneDrive/Documents/GitHub/rba_g2/ace_market_companies_list.html'
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
            'Has_5Y_Data': False,
            'First_Date': '-',
            'Avg_Return': 0.0,
            'Avg_Return_Display': '-'
        }
        stocks.append(stock_info)
        tickers.append(f"{code}.KL")

    # 2. Add Benchmark to tickers
    tickers.append('^KLSE')

    # 3. Check Data Availability & Calculate Returns (Batch Download)
    print(f"Downloading and analyzing data for {len(tickers)} tickers... (This may take a minute)")
    
    # Define 5 years ago
    today = datetime.date.today()
    five_years_ago = today - datetime.timedelta(days=365*5)
    start_date_check = five_years_ago - datetime.timedelta(days=30) # Buffer
    
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
                    'Has_5Y_Data': False
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
                        if t == '^KLSE':
                            s['Last_Price_Display'] = f"{last_price:.2f}"
                        else:
                            s['Last_Price_Display'] = f"RM {last_price:.3f}"
                        
                        # Yahoo Finance Link
                        s['Source_Link'] = f"https://finance.yahoo.com/quote/{s['Ticker']}"
                        
                        # 3. Generate Detail Page
                        if t == '^KLSE':
                            detail_filename = "details/KLSE.html"
                        else:
                            detail_filename = f"details/{s['Code']}.html"
                            
                        s['Detail_Link'] = detail_filename
                        
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
        <title>ACE Market Stocks Summary</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; padding: 20px; margin: 0; }}
            .container {{ max-width: 1500px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ text-align: center; color: #2c3e50; margin-bottom: 30px; font-weight: 600; }}
            .section-title {{ font-size: 1.2em; font-weight: 600; color: #2c3e50; margin: 30px 0 15px 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            
            .controls {{ display: flex; gap: 15px; margin-bottom: 25px; align-items: center; }}
            .search-box {{ flex: 1; position: relative; }}
            #searchInput {{ 
                width: 100%; padding: 15px 20px; 
                border: 2px solid #eef2f7; border-radius: 8px; 
                font-size: 16px; transition: border-color 0.3s;
                box-sizing: border-box;
            }}
            #searchInput:focus {{ outline: none; border-color: #3498db; }}
            
            .filter-box select {{
                padding: 15px 20px;
                border: 2px solid #eef2f7; border-radius: 8px;
                font-size: 16px; background-color: white; cursor: pointer;
            }}
            .filter-box select:focus {{ outline: none; border-color: #3498db; }}

            .table-wrapper {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ 
                background-color: #f8f9fa; color: #2c3e50; 
                font-weight: 600; cursor: pointer; user-select: none;
                position: sticky; top: 0; white-space: nowrap;
            }}
            th:hover {{ background-color: #e9ecef; }}
            tr:hover {{ background-color: #f8f9fa; transition: background-color 0.2s; }}
            
            a {{ color: #3498db; text-decoration: none; font-weight: 500; }}
            a:hover {{ text-decoration: underline; color: #2980b9; }}
            
            .count {{ text-align: right; color: #7f8c8d; margin-bottom: 15px; font-size: 0.9em; }}
            .badge {{ 
                background-color: #e1ecf4; color: #2c3e50; 
                padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 0.95em;
            }}
            .status-badge {{
                padding: 5px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 600;
            }}
            .status-yes {{ background-color: #d4edda; color: #155724; }}
            .status-no {{ background-color: #f8d7da; color: #721c24; }}
            
            .num-col {{ font-family: monospace; text-align: right; }}
            th.num-col {{ text-align: right; }}
            
            .action-btn {{
                background-color: #3498db; color: white; padding: 5px 10px; 
                border-radius: 4px; font-size: 0.85em; text-decoration: none;
            }}
            .action-btn:hover {{ background-color: #2980b9; color: white; text-decoration: none; }}
            .action-btn.disabled {{ background-color: #bdc3c7; pointer-events: none; }}
            
            .source-link {{ font-size: 0.85em; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ACE Market Stocks Summary</h1>
            
            <div class="section-title">Market Benchmarks & Rates</div>
            <table>
                <thead>
                    <tr><th>Name</th><th>Code</th><th>Last Price / Rate</th><th>Avg Daily Return</th><th>Data</th><th>Source</th></tr>
                </thead>
                <tbody>
    """
    
    # Add KLSE
    if klse_data:
        html_content += f"""
        <tr>
            <td>FBMKLCI Benchmark</td>
            <td><span class="badge">^KLSE</span></td>
            <td class="num-col">{klse_data['Last_Price_Display']}</td>
            <td class="num-col">{klse_data['Avg_Return_Display']}</td>
            <td><a href="{klse_data['Detail_Link']}" class="action-btn" target="_blank">View Data</a></td>
            <td><a href="{klse_data['Source_Link']}" class="source-link" target="_blank">Yahoo</a></td>
        </tr>
        """
    else:
        html_content += """
        <tr>
            <td>FBMKLCI Benchmark</td>
            <td><span class="badge">^KLSE</span></td>
            <td class="num-col">-</td>
            <td class="num-col">-</td>
            <td><span class="action-btn disabled">No Data</span></td>
            <td><span class="source-link">Yahoo</span></td>
        </tr>
        """
    
    # Add Bond (Constant)
    html_content += """
        <tr>
            <td>Malaysia 10-Year Gov Bond</td>
            <td><span class="badge">MGS 10Y</span></td>
            <td class="num-col">4.00% (Fixed)</td>
            <td class="num-col">-</td>
            <td><span class="action-btn disabled">Assumption</span></td>
            <td><span class="source-link">Bank Negara / Market Approx</span></td>
        </tr>
    """
    
    html_content += f"""
                </tbody>
            </table>

            <div class="section-title">Stock List</div>
            <div class="controls">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search by Company Name or Code..." onkeyup="filterTable()">
                </div>
                <div class="filter-box">
                    <select id="dataFilter" onchange="filterTable()">
                        <option value="all">Show All Stocks</option>
                        <option value="target">Target Stocks (5Y Data & > 0.25% Return)</option>
                        <option value="yes">Has 5Y Data Only</option>
                        <option value="no">Incomplete Data Only</option>
                        <option value="high_return">Avg Return >= 0.25%</option>
                    </select>
                </div>
            </div>

            <div class="count">Total Companies: <span id="rowCount">{len(stocks)}</span></div>
            <div class="table-wrapper">
                <table id="stockTable">
                    <thead>
                        <tr>
                            <th style="width: 50px;">#</th>
                            <th onclick="sortTable(1)">Code &#8597;</th>
                            <th onclick="sortTable(2)">Company Name &#8597;</th>
                            <th onclick="sortTable(3)">Has 5Y Data &#8597;</th>
                            <th onclick="sortTable(4)">Start Date &#8597;</th>
                            <th onclick="sortTable(5)" class="num-col">Last Price &#8597;</th>
                            <th onclick="sortTable(6)" class="num-col">Avg Daily Return % &#8597;</th>
                            <th>Data</th>
                            <th>Source</th>
                            <th>Website</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for i, s in enumerate(stocks):
        web_link = f'<a href="{s["Website"]}" target="_blank">{s["Website_Display"]}</a>' if s["Website"] != '#' else '<span style="color:#999">-</span>'
        
        if s['Has_5Y_Data']:
            status_html = '<span class="status-badge status-yes">Yes</span>'
            sort_val = "1"
            data_status = "yes"
        else:
            status_html = '<span class="status-badge status-no">No</span>'
            sort_val = "0"
            data_status = "no"
        
        # Check high return status for filter
        if s['Avg_Return'] >= 0.25:
            high_return = "true"
        else:
            high_return = "false"
            
        # Data Link
        if 'Detail_Link' in s:
            data_link = f'<a href="{s["Detail_Link"]}" class="action-btn" target="_blank">View Data</a>'
            source_link = f'<a href="{s["Source_Link"]}" class="source-link" target="_blank">Yahoo</a>'
            last_price_disp = s.get('Last_Price_Display', '-')
            last_price_val = s.get('Last_Price', 0)
        else:
            data_link = '<span class="action-btn disabled">No Data</span>'
            source_link = '<span style="color:#ccc">Yahoo</span>'
            last_price_disp = '-'
            last_price_val = 0
            
        html_content += f"""
                    <tr data-status="{data_status}" data-high-return="{high_return}">
                        <td>{i + 1}</td>
                        <td><span class="badge">{s['Code']}</span></td>
                        <td>{s['Name']}</td>
                        <td data-sort="{sort_val}">{status_html}</td>
                        <td>{s['First_Date']}</td>
                        <td class="num-col" data-sort="{last_price_val}">{last_price_disp}</td>
                        <td class="num-col" data-sort="{s['Avg_Return']}">{s['Avg_Return_Display']}</td>
                        <td>{data_link}</td>
                        <td>{source_link}</td>
                        <td>{web_link}</td>
                    </tr>
        """

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            function filterTable() {
                var input, filter, table, tr, td, i, txtValue;
                var statusFilter = document.getElementById("dataFilter").value;
                
                input = document.getElementById("searchInput");
                filter = input.value.toUpperCase();
                table = document.getElementById("stockTable");
                tr = table.getElementsByTagName("tr");
                
                var visibleCount = 0;

                for (i = 1; i < tr.length; i++) {
                    var showRow = true;
                    
                    // 1. Check Search Text
                    td1 = tr[i].getElementsByTagName("td")[1]; // Code
                    td2 = tr[i].getElementsByTagName("td")[2]; // Name
                    if (td1 || td2) {
                        txtValue1 = td1.textContent || td1.innerText;
                        txtValue2 = td2.textContent || td2.innerText;
                        if (txtValue1.toUpperCase().indexOf(filter) > -1 || txtValue2.toUpperCase().indexOf(filter) > -1) {
                            // Matches search
                        } else {
                            showRow = false;
                        }
                    }
                    
                    // 2. Check Status Filter
                    var rowStatus = tr[i].getAttribute('data-status');
                    var isHighReturn = tr[i].getAttribute('data-high-return');
                    
                    if (statusFilter === 'yes' && rowStatus !== 'yes') {
                        showRow = false;
                    } else if (statusFilter === 'no' && rowStatus !== 'no') {
                        showRow = false;
                    } else if (statusFilter === 'high_return') {
                         if (isHighReturn !== 'true') showRow = false;
                    } else if (statusFilter === 'target') {
                        // Combined: Has 5Y Data AND High Return
                        if (rowStatus !== 'yes' || isHighReturn !== 'true') {
                            showRow = false;
                        }
                    }

                    if (showRow) {
                        tr[i].style.display = "";
                        visibleCount++;
                    } else {
                        tr[i].style.display = "none";
                    }
                }
                
                document.getElementById("rowCount").innerText = visibleCount;
            }

            function sortTable(n) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("stockTable");
                switching = true;
                dir = "asc";
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        
                        var xVal = x.getAttribute('data-sort') || x.innerText.toLowerCase();
                        var yVal = y.getAttribute('data-sort') || y.innerText.toLowerCase();
                        
                        // Handle numeric sort
                        if (n == 0 || n == 5 || n == 6) { // Index, Last Price, Avg Return
                            xVal = parseFloat(xVal);
                            yVal = parseFloat(yVal);
                        }

                        if (dir == "asc") {
                            if (xVal > yVal) {
                                shouldSwitch = true;
                                break;
                            }
                        } else if (dir == "desc") {
                            if (xVal < yVal) {
                                shouldSwitch = true;
                                break;
                            }
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
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html()
