"""
History proxy server — serves /api/analysis/history directly from PostgreSQL.
Runs inside Hermes container, bypasses the broken backend endpoint.
"""
import json
import asyncio
import asyncpg
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_CONFIG = {
    "host": "stock-postgres",
    "port": 5432,
    "user": "stock_user",
    "password": "change_me_please",
    "database": "stock_analysis",
}

async def query_history(page: int, page_size: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        total = await conn.fetchval("SELECT COUNT(*) FROM analysis_tasks")
        offset = (page - 1) * page_size
        rows = await conn.fetch("""
            SELECT id AS task_id, stock_code, stock_name, status,
                   created_at
            FROM analysis_tasks
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """, page_size, offset)

        items = []
        for r in rows:
            items.append({
                "task_id": r["task_id"],
                "stock_code": r["stock_code"],
                "stock_name": r["stock_name"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    finally:
        await conn.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/analysis/history":
            params = parse_qs(parsed.query)
            page = max(1, int(params.get("page", [1])[0]))
            page_size = min(100, max(1, int(params.get("page_size", [20])[0])))

            try:
                data = asyncio.run(query_history(page, page_size))
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        elif parsed.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # silent


if __name__ == "__main__":
    PORT = 8180
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"History proxy listening on :{PORT}")
    server.serve_forever()
