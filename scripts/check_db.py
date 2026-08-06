import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        host="stock-postgres",
        port=5432,
        user="stock_user",
        password="change_me_please",
        database="stock_analysis"
    )
    
    # Check table exists
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print("Tables:", [t['table_name'] for t in tables])
    
    # Try count query
    result = await conn.fetchrow("SELECT COUNT(*) FROM analysis_tasks")
    print(f"analysis_tasks count: {result[0]}")
    
    # Try history query
    rows = await conn.fetch("SELECT id, stock_code, status, created_at FROM analysis_tasks ORDER BY created_at DESC LIMIT 3")
    for r in rows:
        print(f"  {r['id'][:8]}... {r['stock_code']} {r['status']} {r['created_at']}")
    
    await conn.close()

asyncio.run(check())
