import sqlite3

# create 'telemetry_analytics.db' 
conn = sqlite3.connect('telemetry_analytics.db')
cursor = conn.cursor()

# enable Foreign Key enforcement 
cursor.execute("PRAGMA foreign_keys = ON;")

# build schema
cursor.executescript("""
-- Drop old tables if re-running
DROP TABLE IF EXISTS fact_daily_activity;
DROP TABLE IF EXISTS dim_users;

-- 1. Create Dimension Table
CREATE TABLE dim_users (
    user_id TEXT PRIMARY KEY,
    signup_date DATE NOT NULL,
    user_persona TEXT NOT NULL
);

-- 2. Create Fact Table with Foreign Key
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
""")
conn.commit()

dim_users.to_sql(
    name='dim_users',
    con=conn,
    if_exists='append',  # Appends to the table we created above
    index=False          # Don't write pandas row index (0, 1, 2...) as a column
)