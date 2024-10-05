from datetime import date
from pathlib import Path

from data_process import StockSummary, StockData, CorrelationReport

def create_index(
    template_path: Path,
    out_path: Path,
    summaries: list[StockSummary],
    corr_report: CorrelationReport
):
    with template_path.open('r', encoding = "utf-8") as f:
        index = f.read()
    
    stock_summaries = []
    corr_summaries = []

    for summ_i, summary in enumerate(summaries, start = 1):
        stock_summaries.append(
            f'''<tr>
    <th scope="row">#{summ_i}</th>
    <td><a href="web/pages/{summary.symbol}.html">{summary.symbol}</a></td>
    <td>{summary.start_date:%B %d, %Y}</td>
    <td>{summary.end_date:%B %d, %Y}</td>
    <td>{summary.num_records}</td>
    <td>{summary.last_close}</td>
    <td>{round(summary.last_PE, 2) if summary.has_PE else 'Not available'}</td>
</tr>'''
        )
        corr_summaries.append(
            f'''<tr>
    <th scope="row">#{summ_i}</th>
    <td><a href="web/pages/{summary.symbol}.html">{summary.symbol}</a></td>
    <td>{corr_report.min_corrs[summary.symbol][0]} <span class="color-red metric">({corr_report.min_corrs[summary.symbol][1]:.1%})</span></td>
    <td>{corr_report.max_corrs[summary.symbol][0]} <span class="color-green metric">({corr_report.max_corrs[summary.symbol][1]:.1%})</span></td>
</tr>'''
        )
    
    index = index.format(
        stock_summaries = "\n".join(stock_summaries),
        corr_num_records = corr_report.num_records,
        corr_start_date  = f"{corr_report.start_date:%B %d, %Y}",
        corr_end_date  = f"{corr_report.end_date:%B %d, %Y}",
        corr_summaries = "\n".join(corr_summaries)
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

    if stock_data.total_hits_of_last_close > 0:
        first_hit_info = f'{stock_data.symbol} first closed above its last close price on <span class="metric">{stock_data.first_hit_of_last_close:%A, %B %d, %Y}</span> which was <span class="metric">{(date.today() - stock_data.first_hit_of_last_close).days}</span> days ago.'
    else:
        first_hit_info = f"This is the first time {stock_data.symbol} has closed at this high a price."

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
        total_hits_of_last_close = stock_data.total_hits_of_last_close,
        pcnt_hits_of_last_close = f"{stock_data.pcnt_hit_of_last_close:.1%}",
        last_candle = last_candle,
        last_candle_color = f"color-{last_candle.lower()}",
        last_candle_overall_pcnt = f"{stock_data.last_candle_overall_pcnt:.1%}",
        candle_streak = stock_data.candle_streak,
        curr_streak_returns = f"{stock_data.curr_streak_returns:.2%}",
        streak_cont_prob = f"{stock_data.streak_cont_prob:.1%}",
        curr_pcnt_down_ath = f"{stock_data.raw_data['% Down from ATH'].iloc[-1]:.2f}%",
        max_pcnt_down_ath = f"{stock_data.raw_data['% Down from ATH'].min():.2f}%",
        ath_hits_1000_days = stock_data.ath_hits_1000_days,
        last_ath_date = f"{stock_data.last_ath_date:%A, %B %d, %Y}"
    )

    with page_out_path.joinpath(f"{stock_data.symbol}.html").open('w', encoding = 'utf-8') as f:
        f.write(report)