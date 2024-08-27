from pathlib import Path

import templates
from utility import Config
from data_process import StockData

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
    stock_data.create_features()
    summaries.append(stock_data.summary)
    
    templates.create_stock_report(CONFIG.STOCK_REPORT_TEMPLATE, CONFIG.PAGES_OUT_DIR, CONFIG.IMAGES_OUT_DIR, stock_data)

templates.create_index(CONFIG.INDEX_TEMPLATE, CONFIG.INDEX_PATH, summaries)