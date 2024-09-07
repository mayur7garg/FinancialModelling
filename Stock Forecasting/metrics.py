import warnings

import pandas as pd
from scipy.stats import spearmanr, ConstantInputWarning

warnings.filterwarnings(
    action = "ignore",
    category = ConstantInputWarning
)

def spearman_over_ma(
    ordered_data: pd.Series,
    windows: list[int],
    short_window_default: float = 0.0
 ) -> pd.Series:
    ma_df = pd.DataFrame()

    for win in windows:
        ma_df[f'{win} MA'] = ordered_data.rolling(window = win, min_periods = 1).mean()
    
    sp_ma_df = ma_df.apply(
        spearmanr, 
        axis = "columns", 
        args = (windows,), 
        result_type = "expand"
    ).iloc[:, 0].mul(-1).fillna(short_window_default)

    return sp_ma_df