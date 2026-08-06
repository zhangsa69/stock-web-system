import asyncio
import asyncpg

async def q():
    c = await asyncpg.connect(host="stock-postgres", port=5432, user="stock_user", password="change_me_please", database="stock_analysis")
    # Check enum values
    rows = await c.fetch("SELECT unnest(enum_range(NULL::taskstatus))")
    print("Enum values:", [r[0] for r in rows])
    await c.close()

asyncio.run(q())
