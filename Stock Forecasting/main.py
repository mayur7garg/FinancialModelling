from argparse import ArgumentParser
from pathlib import Path

import templates
from utility import Config
from data_download import update_hist_eq_data
from data_process import StockData

parser = ArgumentParser(prog = "Financial Modelling")
parser.add_argument("-nu", "--no-update", action = "store_true")
args = parser.parse_args()

CONFIG = Config(Path("config.json"))
STOCK_SYMBOLS = CONFIG.get_all_stock_symbols()
PERF_PERIODS = [5, 15, 50, 200, 1000]

summaries = []
perf_reports = []

for symbol in STOCK_SYMBOLS:
    print(f"\n{symbol}")

    is_data_updated = False if args.no_update else update_hist_eq_data(symbol, CONFIG.NSE_DATA_DIR)

    stock_data = StockData(
        symbol, 
        CONFIG.NSE_DATA_DIR, 
        CONFIG.COMPANY_DATA_DIR,
        CONFIG.IMAGES_OUT_DIR,
        is_data_updated
    )
    stock_data.create_features(
        performance_periods = PERF_PERIODS,
        ma_periods = [15, 50, 200],
        sp_ma_periods = [list(range(1, 16)), list(range(5, 101, 5))]
    )
    templates.create_stock_report(
        CONFIG.STOCK_REPORT_TEMPLATE, 
        CONFIG.PAGES_OUT_DIR, 
        stock_data,
        ma_periods = [15, 50, 200]
    )

    summaries.append(stock_data.summary)
    perf_reports.append(stock_data.perf_reports)

templates.create_index(
    CONFIG.INDEX_TEMPLATE, 
    CONFIG.INDEX_PATH, 
    summaries,
    perf_reports,
    PERF_PERIODS[::2]
)