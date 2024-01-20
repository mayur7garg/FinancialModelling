from pathlib import Path

RANDOM_STATE = 7

NSE_DATA_DIR = Path("..", "data", "NSE")
print(f"{NSE_DATA_DIR = } | Valid: {NSE_DATA_DIR.exists() & NSE_DATA_DIR.is_dir()}")

PROCESSED_DATA_DIR = Path("..", "data", "processed")
print(f"{PROCESSED_DATA_DIR = } | Valid: {PROCESSED_DATA_DIR.exists() & PROCESSED_DATA_DIR.is_dir()}")

ROLLING_WINDOWS = [3, 7, 15, 30]
TARGET_WINDOWS = [3, 7, 15, 30]