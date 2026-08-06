"""Fix taskstatus enum: uppercase → lowercase"""
import asyncio
import asyncpg

async def fix():
    c = await asyncpg.connect(
        host="stock-postgres", port=5432,
        user="stock_user", password="change_me_please",
        database="stock_analysis"
    )
    
    renames = [
        ("PENDING", "pending"),
        ("RUNNING", "running"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
    ]
    
    for old, new in renames:
        try:
            await c.execute(f"ALTER TYPE taskstatus RENAME VALUE '{old}' TO '{new}'")
            print(f"  {old} → {new}  ✅")
        except Exception as e:
            if "already exists" in str(e) or "does not exist" in str(e):
                print(f"  {old} → {new}  ⏭️ (already done)")
            else:
                print(f"  {old} → {new}  ❌ {e}")
    
    # Verify
    rows = await c.fetch("SELECT unnest(enum_range(NULL::taskstatus))")
    print(f"\nEnum values now: {[r[0] for r in rows]}")
    await c.close()

asyncio.run(fix())
