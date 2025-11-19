"""
Quick script to check database connection and tables.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

# Mirror the logic from app/database.py so the check script behaves the same.
use_sqlite = os.getenv("USE_SQLITE", "true").lower() == "true"
if use_sqlite:
    DATABASE_URL = "sqlite:///./bizgenie.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/bizgenie")

print(f"Connecting to database: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # Test connection (different probes for SQLite vs Postgres)
    with engine.connect() as conn:
        if DATABASE_URL.startswith("sqlite"):
            result = conn.execute(text("SELECT sqlite_version()"))
            version = result.fetchone()[0]
            print(f"[OK] SQLite database connected: {version}")
        else:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] Database connected: {version[:50]}...")
    
    # Check tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nTables found: {len(tables)}")
    for table in tables:
        print(f"  - {table}")
    
    # Check if required tables exist
    required_tables = ['businesses', 'documents', 'appointments', 'leads']
    missing = [t for t in required_tables if t not in tables]
    
    if missing:
        print(f"\n⚠ Missing tables: {missing}")
        print("Run: python -c 'from app.database import init_db; init_db()'")
    else:
        print("\n[OK] All required tables exist")
    
    # Count records
    if 'businesses' in tables:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM businesses"))
            count = result.fetchone()[0]
            print(f"\nBusinesses in database: {count}")
    
    if 'documents' in tables:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM documents"))
            count = result.fetchone()[0]
            print(f"Documents in database: {count}")
    
except Exception as e:
    print(f"\n[ERROR] Database error: {e}")
    print("\nTroubleshooting:")
    print("1. Check DATABASE_URL in .env file")
    print("2. Make sure PostgreSQL is running")
    print("3. Verify database exists: CREATE DATABASE bizgenie;")
    print("4. Check credentials are correct")

