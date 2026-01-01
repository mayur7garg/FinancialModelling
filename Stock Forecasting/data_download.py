import re
import requests
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime, date, timedelta

START_DATE = date(2020, 1, 1)
RUN_DATE = datetime.now(tz = ZoneInfo("Asia/Calcutta"))

if RUN_DATE.hour >= 20:
    END_DATE = RUN_DATE.date()
else:
    END_DATE = RUN_DATE.date() - timedelta(days = 1)

print(f'Downloading data till {END_DATE:%d-%m-%Y}')

DATA_YEARS = range(START_DATE.year, END_DATE.year + 1)
FILENAME_PTRN = "filename=(.+)"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
}

def _download_hist_eq_data(
    sess: requests.Session,
    symbol: str, 
    start_date: date, 
    end_date: date
):
    req = sess.prepare_request(
        requests.Request(
            'GET',
            r'https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi', 
            headers = HEADERS, 
            params = f"functionName=getHistoricalTradeData&symbol={symbol}&series=EQ&fromDate={start_date:%d-%m-%Y}&toDate={end_date:%d-%m-%Y}&csv=true",
            auth = ('user', 'pass'),
        )
    )

    req.prepare_cookies(sess.cookies)
    response = sess.send(req, allow_redirects = False)

    if response.status_code == 200:
        filename = f'{symbol}_{start_date:%d-%m-%Y}_{end_date:%d-%m-%Y}.json'
        print(f"> Downloaded '{filename}' from '{response.url}'.")
        return filename, response.content.decode('utf-8')
    else:
        print(f"> Unable to get response from API. Code: {response.status_code}")
    return None, None

def update_hist_eq_data(
    symbol: str,
    stock_data_dir: Path
):
    stock_data_dir = stock_data_dir.joinpath(symbol)
    symbol_files = list(stock_data_dir.glob(f"*{symbol}*.json"))
    completed_years = set()
    last_date_ptrn = r"[0-9]{2}-[0-9]{2}-[0-9]{4}"
    data_updated = False

    for c_f in symbol_files:
        c_f_last_date = datetime.strptime(re.findall(last_date_ptrn, c_f.stem)[-1], "%d-%m-%Y").date()
        
        if ((c_f_last_date.day == 31) and (c_f_last_date.month == 12)) or (c_f_last_date == END_DATE):
            completed_years.add(c_f_last_date.year)
        else:
            print(f"> Removing file: {c_f}")
            c_f.unlink()

    with requests.Session() as sess:
        sess.get(f'https://www.nseindia.com/', headers = HEADERS)
        sess.get(f'https://www.nseindia.com/get-quotes/equity?symbol={symbol}', headers = HEADERS)

        for dy in DATA_YEARS:
            if dy not in completed_years:
                filename, data = _download_hist_eq_data(
                    sess, 
                    symbol, 
                    date(dy, 1, 1), 
                    min(date(dy, 12, 31), END_DATE)
                )

                if data is not None:
                    if len(data) > 0:
                        with stock_data_dir.joinpath(filename).open('w', encoding = "utf-8") as f:
                            f.write(data)
                            data_updated = True
                    else:
                        print("> Downloaded data was ignored since it was empty.")
    
    print(f"> Data updated: {data_updated}")
    return data_updated