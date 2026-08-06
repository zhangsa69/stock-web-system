import asyncio
import asyncpg

async def q():
    c = await asyncpg.connect(host="stock-postgres", port=5432, user="stock_user", password="change_me_please", database="stock_analysis")
    
    # Check all columns for any anomalies
    rows = await c.fetch("""
        SELECT id, stock_code, stock_name, skill_name, status, progress, 
               LENGTH(report) as report_len, LENGTH(html_report) as html_len,
               LENGTH(error) as error_len, user_email, celery_task_id,
               created_at, updated_at
        FROM analysis_tasks 
        ORDER BY created_at DESC
    """)
    
    print(f"Total: {len(rows)}")
    for r in rows:
        # Check for any None in unexpected places
        issues = []
        if r['stock_code'] is None: issues.append('stock_code=None')
        if r['skill_name'] is None: issues.append('skill_name=None')
        if r['status'] is None: issues.append('status=None')
        if r['progress'] is None: issues.append('progress=None')
        if r['created_at'] is None: issues.append('created_at=None')
        
        status = r['status']
        print(f"  {r['id'][:8]}... | {r['stock_code']} | {status} | user={r['user_email'] or '-'} | created={r['created_at']} | issues={issues}")
    
    await c.close()

asyncio.run(q())
