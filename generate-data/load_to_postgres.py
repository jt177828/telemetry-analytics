import pandas as pd
from sqlalchemy import create_engine, text

# --- PostgreSQL Configuration ---
DB_USER = "jt"
DB_PASSWORD = ""   # Replace with your actual Postgres password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "telemetry_analytics"

DB_URI = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URI)

print("Connecting to PostgreSQL...")

# 1. Create Schema and Constraints
with engine.connect() as conn:
    print("Resetting and initializing schema...")
    conn.execute(text("DROP TABLE IF EXISTS fact_daily_activity CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS dim_users CASCADE;"))
    
    conn.execute(text("""
    CREATE TABLE dim_users (
        user_id VARCHAR(16) PRIMARY KEY,
        signup_date DATE NOT NULL,
        user_persona VARCHAR(32) NOT NULL
    );

    CREATE TABLE fact_daily_activity (
        activity_id SERIAL PRIMARY KEY,
        user_id VARCHAR(16) NOT NULL REFERENCES dim_users(user_id),
        activity_date DATE NOT NULL,
        steps INT NOT NULL,
        active_minutes INT NOT NULL,
        sleep_minutes INT NOT NULL,
        sync_flag SMALLINT NOT NULL
    );
    """))
    conn.commit()

# 2. Read from CSVs
print("Reading generated CSV files...")
dim_users = pd.read_csv("data/dim_users.csv")
fact_daily_activity = pd.read_csv("data/fact_daily_activity.csv")

# 3. Ingest DataFrames into PostgreSQL
print(f"Loading {len(dim_users):,} users into dim_users...")
dim_users.to_sql(
    name='dim_users',
    con=engine,
    if_exists='append',
    index=False
)

print(f"Loading {len(fact_daily_activity):,} records into fact_daily_activity (chunked)...")
fact_daily_activity.to_sql(
    name='fact_daily_activity',
    con=engine,
    if_exists='append',
    index=False,
    chunksize=20000,
    method='multi'
)

# 4. Create Analytical Indexes
print("Building analytical B-Tree indexes...")
with engine.connect() as conn:
    conn.execute(text("CREATE INDEX idx_user_activity ON fact_daily_activity(user_id, activity_date);"))
    conn.execute(text("CREATE INDEX idx_sync_date ON fact_daily_activity(sync_flag, activity_date);"))
    conn.commit()

# 5. Sanity Check
with engine.connect() as conn:
    u_count = conn.execute(text("SELECT COUNT(*) FROM dim_users;")).scalar()
    f_count = conn.execute(text("SELECT COUNT(*) FROM fact_daily_activity;")).scalar()

print(f"\nLoad Complete!")
print(f"Verified counts in PostgreSQL -> dim_users: {u_count:,} | fact_daily_activity: {f_count:,}")