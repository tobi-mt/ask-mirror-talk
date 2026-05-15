"""
Migration: Add device_id column to product_events table
"""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import os

DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

def run_migration(engine: Engine):
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='product_events' AND column_name='device_id';
        """))
        if result.fetchone():
            print("device_id column already exists in product_events.")
            return
        print("Adding device_id column to product_events...")
        conn.execute(text("""
            ALTER TABLE product_events ADD COLUMN device_id VARCHAR(64);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_product_events_device_id ON product_events(device_id);
        """))
        print("Migration complete.")

if __name__ == "__main__":
    engine = create_engine(DB_URL)
    run_migration(engine)
