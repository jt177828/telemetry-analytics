import sqlite3
import pandas as pd

# connect local database file
conn = sqlite3.connect('telemetry_analytics.db')
cursor = conn.cursor()

# enforce foreign keys
cursor.execute("PRAGMA foreign_keys = ON;")

# define Schema
cursor.executescript("""
DROP TABLE IF EXISTS fact_daily_activity;
DROP TABLE IF EXISTS dim_users;

CREATE TABLE dim_users (
    user_id TEXT PRIMARY KEY,
    signup_date DATE NOT NULL,
    user_persona TEXT NOT NULL
);

CREATE TABLE fact_daily_activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    activity_date DATE NOT NULL,
    steps INTEGER NOT NULL,
    active_minutes INTEGER NOT NULL,
    sleep_minutes INTEGER NOT NULL,
    sync_flag INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES dim_users(user_id)
);

CREATE INDEX idx_activity_lookup ON fact_daily_activity(user_id, activity_date);
CREATE INDEX idx_activity_sync ON fact_daily_activity(sync_flag, activity_date);
""")

# insert DataFrames generated in generate_data.py
# dim_users.to_sql('dim_users', conn, if_exists='append', index=False)
# fact_daily_activity.to_sql('fact_daily_activity', conn, if_exists='append', index=False)

conn.commit()
conn.close()
print("Database initialized and loaded successfully.")