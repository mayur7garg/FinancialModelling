from pathlib import Path

from data import StockSummary, StockData

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
    image_out_path: Path,
    stock_data: StockData
):
    with template_path.open('r', encoding = "utf-8") as f:
        report = f.read()

    report = report.format(symbol = stock_data.symbol)

    with page_out_path.joinpath(f"{stock_data.symbol}.html").open('w', encoding = 'utf-8') as f:
        f.write(report)