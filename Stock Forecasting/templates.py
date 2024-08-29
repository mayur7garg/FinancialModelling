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
    <td>{'Available' if summary.has_PE else 'Not available'}</td>
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
    stock_data: StockData
):
    with template_path.open('r', encoding = "utf-8") as f:
        report = f.read()

    last_candle = "Green" if stock_data.last_candle == 1 else "Red"

    if stock_data.total_hits_of_last_close > 0:
        first_hit_info = f'{stock_data.symbol} first closed above this last close price on <span class="metric">{stock_data.first_hit_of_last_close:%A, %B %d, %Y}</span> which was <span class="metric">{(date.today() - stock_data.first_hit_of_last_close).days}</span> days ago.'
    else:
        first_hit_info = f"This is the first time {stock_data.symbol} has closed at this high a price."

    report = report.format(
        symbol = stock_data.symbol,
        num_records = stock_data.summary.num_records,
        start_date = f"{stock_data.summary.start_date:%B %d, %Y}",
        end_date = f"{stock_data.summary.end_date:%B %d, %Y}",
        last_close = stock_data.last_close,
        last_candle = last_candle,
        last_candle_color = f"color-{last_candle.lower()}",
        first_hit_info = first_hit_info,
        total_hits_of_last_close = stock_data.total_hits_of_last_close,
        pcnt_hits_of_last_close = f"{stock_data.pcnt_hit_of_last_close:.1%}",
        last_candle_overall_pcnt = f"{stock_data.last_candle_overall_pcnt:.1%}",
        candle_streak = stock_data.candle_streak,
        streak_cont_prob = f"{stock_data.streak_cont_prob:.1%}"
    )

    with page_out_path.joinpath(f"{stock_data.symbol}.html").open('w', encoding = 'utf-8') as f:
        f.write(report)