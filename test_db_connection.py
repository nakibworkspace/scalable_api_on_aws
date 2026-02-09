#!/usr/bin/env python3
"""
Test script to verify PostgreSQL database connection
Run this before deploying to AWS to ensure your database URL is correct
"""

import os
import sys
from sqlalchemy import create_engine, text

def test_connection():
    """Test database connection and basic operations"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nSet it with:")
        print('  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"')
        print("\nOr create a .env file with:")
        print('  DATABASE_URL=postgresql://user:pass@host:5432/dbname')
        sys.exit(1)
    
    print(f"🔍 Testing connection to database...")
    print(f"   Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'unknown'}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Connection successful!")
            
            # Test query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL version: {version.split(',')[0]}")
            
            # Test create table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY,
                    test_value TEXT
                )
            """))
            conn.commit()
            print("✅ Can create tables")
            
            # Test insert
            conn.execute(text("""
                INSERT INTO test_connection (test_value) 
                VALUES ('test')
            """))
            conn.commit()
            print("✅ Can insert data")
            
            # Test select
            result = conn.execute(text("SELECT COUNT(*) FROM test_connection"))
            count = result.fetchone()[0]
            print(f"✅ Can query data (found {count} rows)")
            
            # Cleanup
            conn.execute(text("DROP TABLE test_connection"))
            conn.commit()
            print("✅ Can drop tables")
            
        print("\n🎉 All tests passed! Your database is ready to use.")
        print("\nNext steps:")
        print("  1. cd infra")
        print("  2. pulumi config set --secret database-url \"$DATABASE_URL\"")
        print("  3. pulumi up")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nCommon issues:")
        print("  • Check username and password are correct")
        print("  • Verify database host is accessible")
        print("  • Ensure database allows connections from your IP")
        print("  • Check if SSL is required (add ?sslmode=require to URL)")
        print("  • Verify the database name exists")
        return False

if __name__ == "__main__":
    # Try to load from .env file if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    success = test_connection()
    sys.exit(0 if success else 1)
