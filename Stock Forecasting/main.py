from pathlib import Path

from utility import Config
from data import StockSummary, StockData

CONFIG = Config(Path("config.json"))
STOCK_SYMBOLS = CONFIG.get_all_stock_symbols()

summaries = []

for symbol in STOCK_SYMBOLS:
    stock_data = StockData(
        symbol, 
        CONFIG.NSE_DATA_DIR, 
        CONFIG.EPS_DATA_DIR,
        CONFIG.RELOAD_DATA
    )
    summaries.append(stock_data.summary)
    print(stock_data.summary)