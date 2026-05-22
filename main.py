import pandas as pd
import numpy as np
import elo
import json
import os
from datetime import datetime

# Constants
MINOR_ELO_DEDUCT = -20
MAJOR_ELO_DEDUCT = -40
OFFSETS = {"GB1": 0, "IT1": -57, "ES1": -60, "L1": -64, "FR1": -64, "CL": -61}
# Base ELOs grounded in UEFA country coefficients (England 103.6, Italy 92.1, Spain 85.9, Germany 82.9, France 75.5)
# Sets the starting point for a *mid-table* club in each league
BASE_ELO_BY_LEAGUE = {"GB1": 1520, "ES1": 1510, "IT1": 1470, "L1": 1460, "FR1": 1450, "CL": 1550}
# CL-only clubs get a lower base — they must earn their rating without a domestic anchor
CL_ONLY_BASE_ELO = 1400

# Reduced K-factors: toned down 2nd leg rewards to avoid single-game spikes
K_LOOKUP = {
    "Group Stage": 22,
    "intermediate stage 1st leg": 22,
    "intermediate stage 2nd leg": 28,
    "Last 16 1st Leg": 22,
    "Last 16 2nd Leg": 28,
    "Quarter-Finals 1st Leg": 25,
    "Quarter-Finals 2nd Leg": 32,
    "Semi-Finals 1st Leg": 28,
    "Semi-Finals 2nd Leg": 35
}
REGULAR_K = 20

# 1. Load data
df = pd.read_csv('cleaned_games.csv')
scores = df['aggregate'].str.extract(r'(\d+):(\d+)').astype(float)
df['home_score'], df['away_score'] = scores[0], scores[1]
df['home_result'] = np.where(df['home_score'] > df['away_score'], 'W', np.where(df['home_score'] == df['away_score'], 'D', 'L'))

# 2. Setup Initial Stats
output_dict = {}
teams = pd.concat([df['home_club_name'], df['away_club_name']]).unique()
for team in teams:
    team_matches = df[(df['home_club_name'] == team) | (df['away_club_name'] == team)]
    primary_league = team_matches['competition_id'].mode()[0]
    # CL-only clubs start lower — no domestic data to anchor them
    base_elo = CL_ONLY_BASE_ELO if primary_league == 'CL' else BASE_ELO_BY_LEAGUE.get(primary_league, 1450)
    output_dict[team] = {
        "primary_league": primary_league,
        "elo": base_elo,
        "match_count": 0,
        "last_5_results": [],
        "last_5_home": [],
        "last_5_away": [],
        "last_match_date": None,
        "h2h_history": {},
        "is_top_five": primary_league != 'CL'
    }

# 3. Process Matches
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by='date')

for _, row in df.iterrows():
    h_team, a_team = row['home_club_name'], row['away_club_name']
    
    current_k = K_LOOKUP.get(row['round'], REGULAR_K) if row['competition_id'] == 'CL' else REGULAR_K
    
    h_elo_calc = output_dict[h_team]["elo"]
    a_elo_calc = output_dict[a_team]["elo"]

    h_offset, a_offset = OFFSETS.get(output_dict[h_team]["primary_league"], -60), OFFSETS.get(output_dict[a_team]["primary_league"], -60)
    
    score_h = 1.0 if row['home_result'] == "W" else (0.5 if row['home_result'] == "D" else 0.0)
    new_h, new_a = elo.update_ratings(
        h_elo_calc, a_elo_calc, score_h, abs(row['home_score'] - row['away_score']),
        h_offset, a_offset, 0, 0, k=current_k
    )

    output_dict[h_team]["elo"] = new_h
    output_dict[a_team]["elo"] = new_a
    
    output_dict[h_team]["match_count"] += 1
    output_dict[a_team]["match_count"] += 1
    output_dict[h_team]["last_match_date"] = row['date'].strftime('%Y-%m-%d')
    output_dict[a_team]["last_match_date"] = row['date'].strftime('%Y-%m-%d')

    # Update last 5 home/away records
    h_result = row['home_result']
    a_result = 'W' if h_result == 'L' else ('L' if h_result == 'W' else 'D')

    output_dict[h_team]["last_5_home"].append(h_result)
    if len(output_dict[h_team]["last_5_home"]) > 5:
        output_dict[h_team]["last_5_home"].pop(0)

    output_dict[a_team]["last_5_away"].append(a_result)
    if len(output_dict[a_team]["last_5_away"]) > 5:
        output_dict[a_team]["last_5_away"].pop(0)

# 4. File Management (Rename and Save)
if os.path.exists('club_stats.json'):
    if os.path.exists('club_stats_old.json'):
        os.remove('club_stats_old.json')
    os.rename('club_stats.json', 'club_stats_old.json')

with open('club_stats.json', 'w') as f:
    json.dump(output_dict, f, indent=2)

print("Process complete. Statistics updated and backed up.")