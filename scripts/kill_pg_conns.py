"""Terminate backend's PostgreSQL connections to force reload of enum mapping"""
import asyncio
import asyncpg

async def fix():
    c = await asyncpg.connect(
        host="stock-postgres", port=5432,
        user="stock_user", password="change_me_please",
        database="stock_analysis"
    )
    
    # Find backend connections
    rows = await c.fetch("""
        SELECT pid, usename, application_name, state
        FROM pg_stat_activity 
        WHERE datname = 'stock_analysis' 
          AND usename = 'stock_user'
          AND pid <> pg_backend_pid()
    """)
    
    print(f"Found {len(rows)} backend connections:")
    for r in rows:
        print(f"  pid={r['pid']} app={r['application_name']} state={r['state']}")
    
    # Terminate them
    for r in rows:
        try:
            await c.execute(f"SELECT pg_terminate_backend({r['pid']})")
            print(f"  Terminated pid={r['pid']}")
        except Exception as e:
            print(f"  Failed pid={r['pid']}: {e}")
    
    await c.close()

asyncio.run(fix())
