import numpy as np
import pandas as pd

# elo/engine.py

K_FACTOR = 20  

def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that team A beats team B."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))

def update_ratings(
    rating_a: float,
    rating_b: float,
    score_a: float,
    goal_diff: int,
    off_a: int,
    off_b: int,
    fat_a: int,
    fat_b: int,
    k: float = K_FACTOR,
    hfa: int = 40 # Added Home Field Advantage parameter
) -> tuple[float, float]:
    """Return (new_rating_a, new_rating_b) after a match."""
    # Apply HFA to the home team's effective rating
    eff_a = rating_a + off_a + fat_a + hfa
    eff_b = rating_b + off_b + fat_b
    
    ea = expected_score(eff_a, eff_b)
    eb = 1.0 - ea
    score_b = 1.0 - score_a

    # Cap at 2.2: tighter than original (3.0) to prevent blowout inflation,
    # but fair enough to reward teams that win by 3+ goals consistently
    multiplier = min(2.2, np.log(goal_diff + 1) + 1)

    new_a = rating_a + k * multiplier * (score_a - ea)
    new_b = rating_b + k * multiplier * (score_b - eb)
    
    return round(new_a, 2), round(new_b, 2)