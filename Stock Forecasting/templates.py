from datetime import date
from pathlib import Path

from data_process import StockSummary, PerformanceReport, StockData

def create_index(
    template_path: Path,
    out_path: Path,
    summaries: list[StockSummary],
    perf_reports: list[list[PerformanceReport]],
    performance_periods: list[int],
    top_count: int = 5
):
    with template_path.open('r', encoding = "utf-8") as f:
        index = f.read()
    
    stock_summaries = []
    perf_results = {p: [] for p in performance_periods}

    for summ_i, (summary, stock_perfs) in enumerate(
        zip(summaries, perf_reports), start = 1
    ):
        change_color = 'color-green' if summary.last_change >= 0 else 'color-red'
        stock_summaries.append(
            f'''<tr>
    <th scope="row">#{summ_i}</th>
    <td><a href="web/pages/{summary.symbol}.html">{summary.symbol}</a></td>
    <td>{summary.start_date:%B %d, %Y}</td>
    <td>{summary.end_date:%B %d, %Y}</td>
    <td>{summary.num_records}</td>
    <td>{summary.last_close} <span class="{change_color} metric">({summary.last_change:.2%})</span></td>
    <td>{round(summary.last_PE, 2) if summary.has_PE else 'Not available'}</td>
</tr>'''
        )

        for perf_report in stock_perfs:
            if perf_report.period_size in performance_periods:
                perf_results[perf_report.period_size].append(
                    (perf_report.net_returns, summary.symbol)
                )

    perf_period_size = []
    top_gainers = []
    top_losers = []

    for period in performance_periods:
        perf_results[period] = sorted(perf_results[period])
        perf_period_size.append(f'<th scope="col">{period} Days</th>')

    for i in range(top_count):
        period_gainers = []
        period_losers = []

        for period in performance_periods:
            period_gainer = perf_results[period][-i - 1]
            change_color = 'color-green' if period_gainer[0] >= 0 else 'color-red'
            period_gainers.append(
                f'<td>{period_gainer[1]} <span class="{change_color} metric">({period_gainer[0]:.2%})</span></td>'
            )

            period_loser = perf_results[period][i]
            change_color = 'color-green' if period_loser[0] >= 0 else 'color-red'
            period_losers.append(
                f'<td>{period_loser[1]} <span class="{change_color} metric">({period_loser[0]:.2%})</span></td>'
            )
        
        top_gainers.append(
            f'<tr>\n<th scope="row">#{i + 1}</th>\n' +
            "\n".join(period_gainers) + 
            "\n</tr>"
        )

        top_losers.append(
            f'<tr>\n<th scope="row">#{i + 1}</th>\n' +
            "\n".join(period_losers) + 
            "\n</tr>"
        )
    
    index = index.format(
        stock_summaries = "\n".join(stock_summaries),
        perf_period_size = "\n".join(perf_period_size),
        top_gainers = "\n".join(top_gainers),
        top_losers = "\n".join(top_losers)
    )

    with out_path.open('w', encoding = 'utf-8') as f:
        f.write(index)

def create_stock_report(
    template_path: Path,
    page_out_path: Path,
    stock_data: StockData,
    ma_periods: list[int]
):
    with template_path.open('r', encoding = "utf-8") as f:
        report = f.read()

    perf_period_size = ['<th scope="col"></th>']
    perf_start_date = ['<th scope="row">Start Date</th>']
    perf_net_returns = ['<th scope="row">Net Return</th>']
    perf_avg_daily_returns = ['<th scope="row">Average Daily Return</th>']
    perf_median_close = ['<th scope="row">Median Close Price</th>']
    perf_lowest_close = ['<th scope="row">Lowest Close Price</th>']
    perf_highest_close = ['<th scope="row">Highest Close Price</th>']
    perf_median_PE = ['<th scope="row">Median PE</th>']

    for perf_report in stock_data.perf_reports:
        perf_period_size.append(f'<th scope="col">{perf_report.period_size} Days</th>')
        perf_start_date.append(f'<td>{perf_report.start_date:%B %d, %Y}</td>')

        perf_color = 'color-green' if perf_report.net_returns > 0 else 'color-red'
        perf_net_returns.append(
            f'<td><span class="{perf_color} metric">{perf_report.net_returns:.2%}</span></td>'
        )
        perf_avg_daily_returns.append(
            f'<td><span class="{perf_color} metric">{perf_report.avg_daily_returns:.3%}</span></td>'
        )
        
        perf_median_close.append(f'<td>{perf_report.median_close:.2f}</td>')
        perf_lowest_close.append(f'<td>{perf_report.lowest_close:.2f}</td>')
        perf_highest_close.append(f'<td>{perf_report.hightest_close:.2f}</td>')
        perf_median_PE.append(f'<td>{perf_report.median_PE:.2f}</td>')

    last_candle = "Green" if stock_data.last_candle == 1 else "Red"

    ma_values = []
    for period in ma_periods:
        col_name = f'MA {period} days'
        ma_values.append(
            f'<p>Average of last {period} days: <span class="metric">{stock_data.raw_data[col_name].iloc[-1]:.2f}</span></p>'
        )

    total_hits_of_last_close = stock_data.raw_data['Total hits of Close'].iloc[-1]

    if total_hits_of_last_close > 1:
        first_hit_info = f'{stock_data.symbol} first closed above its last close price on <span class="metric">{stock_data.raw_data["First hit of Close"].iloc[-1]:%A, %B %d, %Y}</span> which was <span class="metric">{(date.today() - stock_data.raw_data["First hit of Close"].iloc[-1]).days}</span> days ago.'
        last_hit_info = f'Previously, {stock_data.symbol} closed above its last close price on <span class="metric">{stock_data.raw_data["Last hit of Close"].iloc[-1]:%A, %B %d, %Y}</span> which was <span class="metric">{(date.today() - stock_data.raw_data["Last hit of Close"].iloc[-1]).days}</span> days ago.'
    else:
        first_hit_info = f"This is the first time {stock_data.symbol} has closed at this high a price."
        last_hit_info = ""

    report = report.format(
        symbol = stock_data.symbol,
        num_records = stock_data.summary.num_records,
        start_date = f"{stock_data.summary.start_date:%B %d, %Y}",
        end_date = f"{stock_data.summary.end_date:%B %d, %Y}",
        today_date = f"{date.today():%B %d, %Y}",
        perf_period_size = "\n".join(perf_period_size),
        perf_start_date = "\n".join(perf_start_date),
        perf_net_returns = "\n".join(perf_net_returns),
        perf_avg_daily_returns = "\n".join(perf_avg_daily_returns),
        perf_median_close = "\n".join(perf_median_close),
        perf_lowest_close = "\n".join(perf_lowest_close),
        perf_highest_close = "\n".join(perf_highest_close),
        perf_median_PE = "\n".join(perf_median_PE),
        PE_available = "" if stock_data.summary.has_PE else "no_PE",
        last_close = stock_data.last_close,
        ma_values = "\n".join(ma_values),
        first_hit_info = first_hit_info,
        is_ATH = "" if total_hits_of_last_close > 1 else "is_ATH",
        total_hits_of_last_close = total_hits_of_last_close,
        pcnt_hits_of_last_close = f"{stock_data.raw_data['Pcnt hits of Close'].iloc[-1]:.1%}",
        last_hit_info = last_hit_info,
        last_candle = last_candle,
        last_change = f"{stock_data.summary.last_change:.2%}",
        last_candle_color = f"color-{last_candle.lower()}",
        last_candle_overall_pcnt = f"{stock_data.last_candle_overall_pcnt:.1%}",
        candle_streak = stock_data.candle_streak,
        curr_streak_returns = f"{stock_data.curr_streak_returns:.2%}",
        streak_cont_prob = f"{stock_data.streak_cont_prob:.1%}",
        longest_candle_streak = stock_data.longest_candle_streak[0],
        longest_candle_streak_start = f"{stock_data.longest_candle_streak[1]:%B %d, %Y}",
        longest_candle_streak_end = f"{stock_data.longest_candle_streak[2]:%B %d, %Y}",
        curr_pcnt_down_ath = f"{stock_data.raw_data['% Down from ATH'].iloc[-1]:.2f}%",
        max_pcnt_down_ath = f"{stock_data.raw_data['% Down from ATH'].min():.2f}%",
        ath_hits_1000_days = stock_data.ath_hits_1000_days,
        last_ath_date = f"{stock_data.last_ath_date:%A, %B %d, %Y}"
    )

    with page_out_path.joinpath(f"{stock_data.symbol}.html").open('w', encoding = 'utf-8') as f:
        f.write(report)