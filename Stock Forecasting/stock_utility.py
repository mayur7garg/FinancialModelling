import json
from pathlib import Path

class Config:
    def __init__(self, config_path: Path) -> None:
        with config_path.open('r', encoding = "utf-8") as f:
            conf_dict = json.load(f)

        self.NSE_DATA_DIR = Path(conf_dict['NSE_DATA_DIR'])
        print(
            f"{self.NSE_DATA_DIR = } | Valid: {self.NSE_DATA_DIR.exists() & self.NSE_DATA_DIR.is_dir()}"
        )

        self.EPS_DATA_DIR = Path(conf_dict['EPS_DATA_DIR'])
        print(
            f"{self.EPS_DATA_DIR = } | Valid: {self.EPS_DATA_DIR.exists() & self.EPS_DATA_DIR.is_dir()}"
        )

        self.PROCESSED_DATA_DIR = Path(conf_dict['PROCESSED_DATA_DIR'])
        print(
            f"{self.PROCESSED_DATA_DIR = } | Valid: {self.PROCESSED_DATA_DIR.exists() & self.PROCESSED_DATA_DIR.is_dir()}"
        )

        self.RANDOM_STATE = 7