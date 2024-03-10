from math import sqrt
from typing import List

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