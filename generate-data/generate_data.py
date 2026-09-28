import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# set fixed random sequence, for reproducibility
np.random.seed(42)

# constants
NUM_USERS = 2500
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 1, 1)

PERSONAS = {
    'Power': {'weight': 0.20, 'step_mean': 11500, 'step_std': 2200, 'decay_lambda': 0.0010, 'base_p': 0.98},
    'Regular': {'weight': 0.55, 'step_mean': 7500, 'step_std': 1800, 'decay_lambda': 0.0035, 'base_p': 0.88},
    'At-Risk': {'weight': 0.25, 'step_mean': 4500, 'step_std': 1500, 'decay_lambda': 0.0090, 'base_p': 0.70}
}

# base_p: likelihood that an individual user will actually wear the device and use the app on the initial day
'''
power users: 20% of population, mean of 11500 daily steps, initial sync probability of 0.98
regular users: 55% of population, mean of 7500 daily steps, initial sync probability of 0.88
at-risk users: 25% of population, mean of 4500 daily steps, initial sync probability of 0.70

'''
DEVICE_MODELS = ['PulseFit Pro', 'VeloSync 2', 'AuraBand Slim', 'Apex SmartTrack']

# generate dimension table
persona_keys = list(PERSONAS.keys()) # ['Power', 'Regular', 'At-risk']
persona_probs = [PERSONAS[p]['weight'] for p in persona_keys] # ['0.20, 0.55, 0.25]
user_ids = [f"USR_{i:05d}" for i in range(1, NUM_USERS + 1)]
user_personas = np.random.choice(persona_keys, size=NUM_USERS, p=persona_probs)

signup_offsets = np.random.randint(0, 365, size=NUM_USERS)
signup_dates = [START_DATE + timedelta(days=int(offset)) for offset in signup_offsets]

dim_users = pd.DataFrame({
    'user_id': user_ids,
    'signup_date': signup_dates,
    'user_persona': user_personas
})

# generate fact table
records = []
for _, user in dim_users.iterrows():
    u_id = user['user_id']
    p_type = user['user_persona']
    p_meta = PERSONAS[p_type]

    u_signup = pd.Timestamp(user['signup_date']).to_pydatetime()
    days_active = (END_DATE - u_signup).days

    if days_active <= 0:
        continue

    tenures = np.arange(days_active)

    decay_probs = p_meta['base_p'] * np.exp(-p_meta['decay_lambda'] * tenures)
    decay_probs = np.clip(decay_probs, 0.05, 0.99)
    synced = np.random.rand(days_active) < decay_probs

    # day-level telemetry and weekend seasonality
    for t_idx, did_sync in enumerate(synced):
        curr_date = u_signup + timedelta(days=int(t_idx))
        is_weekend = curr_date.weekday() >= 5

        if did_sync:
            step_boost = 1.15 if (is_weekend and p_type == 'Power') else 1.0
            steps = int(np.clip(np.random.normal(p_meta['step_mean'] * step_boost, p_meta['step_std']), 800, 32000))
            active_mins = int(np.clip(steps / 110 + np.random.normal(0, 10), 10, 240))
            sleep_mins = int(np.clip(np.random.normal(425, 45), 200, 600))
            sync_flag = 1
        else:
            steps = 0
            active_mins = 0
            sleep_mins = 0
            sync_flag = 0

        records.append((u_id, curr_date, steps, active_mins, sleep_mins, sync_flag))

fact_daily_activity = pd.DataFrame(
    records, 
    columns=['user_id', 'activity_date', 'steps', 'active_minutes', 'sleep_minutes', 'sync_flag']
)

print(fact_daily_activity)
print(f"Generated {len(dim_users):,} users and {len(fact_daily_activity):,} activity logs.")

