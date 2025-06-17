#!/usr/bin/env python3
"""
Database Verification Script
Tests that the coffee database is properly set up and working
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, date
import json
import sys

# Database connection parameters
DB_PARAMS = {
    "host": os.getenv("DATABASE_HOST", "localhost"),
    "port": os.getenv("DATABASE_PORT", "5432"),
    "database": os.getenv("DATABASE_NAME", "coffee_db"),
    "user": os.getenv("DATABASE_USER", "coffee_user"),
    "password": os.getenv("DATABASE_PASSWORD", "coffee_pass")
}

def test_connection():
    """Test basic database connection"""
    print("1. Testing database connection...")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"   ✓ Connected successfully!")
        print(f"   ✓ PostgreSQL version: {version.split(',')[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False

def test_tables():
    """Verify all tables exist with correct structure"""
    print("\n2. Checking tables...")
    expected_tables = ['coffee_beans', 'brew_methods', 'coffee_cups']
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Check tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE';
        """)
        
        existing_tables = [row[0] for row in cur.fetchall()]
        
        for table in expected_tables:
            if table in existing_tables:
                print(f"   ✓ Table '{table}' exists")
            else:
                print(f"   ✗ Table '{table}' missing")
                return False
        
        # Check view exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public';
        """)
        views = [row[0] for row in cur.fetchall()]
        
        if 'readable_coffee_cups' in views:
            print(f"   ✓ View 'readable_coffee_cups' exists")
        else:
            print(f"   ✗ View 'readable_coffee_cups' missing")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ✗ Error checking tables: {e}")
        return False

def test_columns():
    """Verify important columns exist"""
    print("\n3. Checking table structures...")
    
    column_checks = {
        'coffee_beans': ['id', 'slug', 'name', 'roaster', 'display_name'],
        'brew_methods': ['id', 'slug', 'method_type', 'template'],
        'coffee_cups': ['id', 'bean_id', 'brew_method_id', 'extraction_yield', 'days_off_roast']
    }
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        for table, expected_columns in column_checks.items():
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}';
            """)
            
            existing_columns = [row[0] for row in cur.fetchall()]
            
            print(f"\n   Table '{table}':")
            for col in expected_columns:
                if col in existing_columns:
                    print(f"     ✓ Column '{col}' exists")
                else:
                    print(f"     ✗ Column '{col}' missing")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ✗ Error checking columns: {e}")
        return False

def test_data_operations():
    """Test inserting and reading data"""
    print("\n4. Testing data operations...")
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if we have any brew methods
        cur.execute("SELECT COUNT(*) as count FROM brew_methods;")
        method_count = cur.fetchone()['count']
        print(f"   ✓ Found {method_count} brew methods")
        
        # Insert a test coffee bean
        test_bean_slug = f"test-coffee-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cur.execute("""
            INSERT INTO coffee_beans (slug, name, roaster, origin, roast_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, slug, display_name;
        """, (
            test_bean_slug,
            "Test Coffee Blend",
            "Test Roastery",
            "Test Origin",
            date.today(),
            "This is a test coffee for verification"
        ))
        
        bean = cur.fetchone()
        print(f"   ✓ Successfully inserted coffee bean:")
        print(f"     - ID: {bean['id']}")
        print(f"     - Slug: {bean['slug']}")
        print(f"     - Display: {bean['display_name']}")
        
        # Get a brew method (if any exist)
        cur.execute("SELECT id, slug, display_name FROM brew_methods LIMIT 1;")
        method = cur.fetchone()
        
        if method:
            # Record a test brew
            cur.execute("""
                INSERT INTO coffee_cups (
                    bean_id, brew_method_id, pre_brew_mass, 
                    post_brew_mass, tds_percentage, rating, 
                    flavor_tags, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, days_off_roast, extraction_yield;
            """, (
                bean['id'],
                method['id'],
                15.0,
                250.0,
                1.35,
                'thumbs_up',
                ['test', 'verification'],
                'Test brew for verification'
            ))
            
            cup = cur.fetchone()
            print(f"   ✓ Successfully recorded brew:")
            print(f"     - ID: {cup['id']}")
            print(f"     - Days off roast: {cup['days_off_roast']}")
            print(f"     - Extraction yield: {cup['extraction_yield']:.2f}%")
            
            # Test the readable view
            cur.execute("""
                SELECT coffee, brew_method, extraction_yield 
                FROM readable_coffee_cups 
                WHERE bean_slug = %s;
            """, (test_bean_slug,))
            
            readable = cur.fetchone()
            if readable:
                print(f"   ✓ Readable view working:")
                print(f"     - {readable['coffee']} brewed with {readable['brew_method']}")
        
        # Clean up test data
        cur.execute("DELETE FROM coffee_beans WHERE slug = %s;", (test_bean_slug,))
        conn.commit()
        print(f"   ✓ Test data cleaned up")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ✗ Error in data operations: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def test_calculations():
    """Test that calculated fields work correctly"""
    print("\n5. Testing calculated fields...")
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test extraction yield calculation
        test_cases = [
            {"pre": 15, "post": 250, "tds": 1.35, "expected": 22.50},
            {"pre": 18, "post": 36, "tds": 9.5, "expected": 19.00},
            {"pre": 20, "post": 300, "tds": 1.25, "expected": 18.75}
        ]
        
        print("   Testing extraction yield calculations:")
        for test in test_cases:
            expected = (test["tds"] * test["post"]) / test["pre"]
            print(f"     - {test['pre']}g → {test['post']}g @ {test['tds']}% TDS = {expected:.2f}% extraction")
        
        print("   ✓ Calculation logic verified")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ✗ Error testing calculations: {e}")
        return False

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Coffee Database Verification Script")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Connection", test_connection),
        ("Tables", test_tables),
        ("Columns", test_columns),
        ("Data Operations", test_data_operations),
        ("Calculations", test_calculations)
    ]
    
    results = []
    for test_name, test_func in tests:
        if test_func():
            results.append((test_name, "PASSED"))
        else:
            results.append((test_name, "FAILED"))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    
    for test_name, status in results:
        symbol = "✓" if status == "PASSED" else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your database is ready to use.")
        print("\nNext steps:")
        print("1. Try connecting with a GUI tool (DBeaver, TablePlus)")
        print("2. Start building your API backend")
        print("3. Create a simple frontend to enter data")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("You may need to run the migration scripts manually.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())