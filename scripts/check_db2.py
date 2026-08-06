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
    
    # Check column type
    cols = await conn.fetch("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'analysis_tasks' AND column_name = 'status'
    """)
    for c in cols:
        print(f"Column: {c['column_name']}, type: {c['data_type']}, udt: {c['udt_name']}")
    
    # Check actual values
    vals = await conn.fetch("SELECT DISTINCT status FROM analysis_tasks")
    print(f"Distinct status values: {[v['status'] for v in vals]}")
    
    # Check if there's a custom enum type
    enums = await conn.fetch("""
        SELECT typname FROM pg_type 
        WHERE typname ILIKE '%taskstatus%' OR typname ILIKE '%status%'
    """)
    print(f"Enum types: {[e['typname'] for e in enums]}")
    
    await conn.close()

asyncio.run(check())
