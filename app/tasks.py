from celery import Celery
import random

# Initialize Celery - pointing to your Redis "Rail"
app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@app.task
def simulate_match_task(home_stats, away_stats):
    home_elo = home_stats['elo']
    away_elo = away_stats['elo']
    
    # 1. Calculate Win Probabilities (Basic Elo Math)
    # A 400 point difference means the stronger team is 10x more likely to win
    exponent = (away_elo - home_elo) / 400
    prob_home_wins = 1 / (1 + 10**exponent)
    
    # 2. Run 10,000 Simulations
    results = {"home_wins": 0, "away_wins": 0, "draws": 0}
    
    for _ in range(10000):
        # We add a 5% margin for a draw
        roll = random.random()
        if roll < (prob_home_wins - 0.025):
            results["home_wins"] += 1
        elif roll > (prob_home_wins + 0.025):
            results["away_wins"] += 1
        else:
            results["draws"] += 1
            
    # 3. Calculate Percentages
    return {
        "home_win_chance": f"{(results['home_wins'] / 10000) * 100:.2f}%",
        "away_win_chance": f"{(results['away_wins'] / 10000) * 100:.2f}%",
        "draw_chance": f"{(results['draws'] / 10000) * 100:.2f}%",
        "raw_results": results
    }