from pathlib import Path

from data_process import StockSummary, StockData

def create_index(
    template_path: Path,
    out_path: Path,
    summaries: list[StockSummary]
):
    with template_path.open('r', encoding = "utf-8") as f:
        index = f.read()
    
    stock_summaries = []
    for summary in summaries:
        stock_summaries.append(
            f'''<div>
    <p><a href="web/pages/{summary.symbol}.html">{summary.symbol}</a></p>
    <p>{summary.num_records} records from {summary.start_date} to {summary.end_date}</p>
    <p>PE data: {'Available' if summary.has_PE else 'Not available'}</p>
</div>'''
        )
    
    stock_summaries = "\n".join(stock_summaries)
    index = index.format(stock_summaries = stock_summaries)

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

    report = report.format(
        symbol = stock_data.symbol,
        last_candle = last_candle,
        last_candle_color = last_candle.lower(),
        candle_streak = stock_data.candle_streak,
        streak_cont_prob = f"{stock_data.streak_cont_prob:.1%}"
    )

    with page_out_path.joinpath(f"{stock_data.symbol}.html").open('w', encoding = 'utf-8') as f:
        f.write(report)