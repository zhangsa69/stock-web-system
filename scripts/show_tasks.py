import asyncio
import asyncpg

async def q():
    c = await asyncpg.connect(host="stock-postgres", port=5432, user="stock_user", password="change_me_please", database="stock_analysis")
    rows = await c.fetch("SELECT id, stock_code, status FROM analysis_tasks ORDER BY created_at DESC LIMIT 3")
    for r in rows:
        print(f"{r['id']} | {r['stock_code']} | {r['status']}")
    await c.close()

asyncio.run(q())
