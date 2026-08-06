"""
Simulate the exact SQLAlchemy query from get_history()
to see if it would fail against the actual database.
"""
import asyncio
import asyncpg

async def q():
    c = await asyncpg.connect(host="stock-postgres", port=5432, user="stock_user", password="change_me_please", database="stock_analysis")
    
    # Simulate get_history_count()
    print("=== get_history_count() ===")
    try:
        r = await c.fetchrow("SELECT count(*) FROM analysis_tasks")
        print(f"OK: count={r[0]}")
    except Exception as e:
        print(f"FAIL: {e}")
    
    # Simulate get_history()  
    print("\n=== get_history() ===")
    try:
        rows = await c.fetch("""
            SELECT id, stock_code, stock_name, skill_name, status, progress, 
                   report, html_report, error, user_email, celery_task_id, 
                   created_at, updated_at 
            FROM analysis_tasks 
            ORDER BY created_at DESC 
            LIMIT 3 OFFSET 0
        """)
        for r in rows:
            print(f"  id={r['id'][:8]}... stock={r['stock_code']} status={r['status']} created={r['created_at']}")
        print(f"OK: {len(rows)} rows")
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
    
    await c.close()

asyncio.run(q())
