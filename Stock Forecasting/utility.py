import json
from pathlib import Path

class Config:
    def __init__(self, config_path: Path) -> None:
        with config_path.open('r', encoding = "utf-8") as f:
            conf_dict = json.load(f)

        self.NSE_DATA_DIR = Path(conf_dict['nse_data_dir'])
        print(
            f"{self.NSE_DATA_DIR = } | Valid: {self.NSE_DATA_DIR.exists() & self.NSE_DATA_DIR.is_dir()}"
        )

        self.COMPANY_DATA_DIR = Path(conf_dict['company_data_dir'])
        print(
            f"{self.COMPANY_DATA_DIR = } | Valid: {self.COMPANY_DATA_DIR.exists() & self.COMPANY_DATA_DIR.is_dir()}"
        )

        self.INDEX_TEMPLATE = Path(conf_dict['index_template'])
        print(
            f"{self.INDEX_TEMPLATE = } | Valid: {self.INDEX_TEMPLATE.exists() & self.INDEX_TEMPLATE.is_file()}"
        )

        self.STOCK_REPORT_TEMPLATE = Path(conf_dict['stock_report_template'])
        print(
            f"{self.STOCK_REPORT_TEMPLATE = } | Valid: {self.STOCK_REPORT_TEMPLATE.exists() & self.STOCK_REPORT_TEMPLATE.is_file()}"
        )

        self.INDEX_PATH = Path(conf_dict['index_path']).joinpath("index.html")
        print(
            f"{self.INDEX_PATH = } | Valid: {self.INDEX_PATH.exists() & self.INDEX_PATH.is_file()}"
        )

        self.PAGES_OUT_DIR = Path(conf_dict['index_path']).joinpath("web", "pages")
        print(
            f"{self.PAGES_OUT_DIR = } | Valid: {self.PAGES_OUT_DIR.exists() & self.PAGES_OUT_DIR.is_dir()}"
        )

        self.IMAGES_OUT_DIR = Path(conf_dict['index_path']).joinpath("web", "images")
        print(
            f"{self.IMAGES_OUT_DIR = } | Valid: {self.IMAGES_OUT_DIR.exists() & self.IMAGES_OUT_DIR.is_dir()}"
        )

        self.RANDOM_STATE = 7

    def get_all_stock_symbols(self):
        return sorted([
            f.stem for f in self.NSE_DATA_DIR.glob("*") if f.is_dir()
        ])