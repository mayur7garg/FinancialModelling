from math import sqrt
from typing import List

from scipy.stats import spearmanr

def adam_momentum(
    gradients: List[float],
    beta_1: float = 0.9,
    beta_2: float = 0.999
) -> float:
    moment_1 = 0
    moment_2 = 0

    for grad in gradients:
        moment_1 = (beta_1 * moment_1) + ((1 - beta_1) * grad)
        moment_2 = (beta_2 * moment_2) + ((1 - beta_2) * grad * grad)
    
    moment_1 = moment_1 / (1 - beta_1)
    moment_2 = moment_2 / (1 - beta_2)
    return moment_1 / sqrt(moment_2)

def spearman_over_ma(
    data,
    min_window: int = 3,
    max_window: int = 15,
    short_window_default: float = 0.0
):
    spear_ma = []

    for i in range(len(data)):

        window_range = min(i + 1, max_window)

        if window_range <= min_window:
            spear_ma.append(short_window_default)
            continue

        rolling_means = []

        for window in range(min_window - 1, window_range):
            rolling_means.append(data[i - window: i + 1].mean())

        rho, p_val = spearmanr(rolling_means[::-1], range(len(rolling_means)))
        spear_ma.append(rho)
    
    return spear_ma