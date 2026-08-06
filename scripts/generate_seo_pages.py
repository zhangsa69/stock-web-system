#!/usr/bin/env python3
"""从 sample_reports.db 生成 SEO 静态页面"""
import sqlite3, os, re, datetime

DB_PATH = "/opt/data/stock-web-system/docker-data/sample_reports.db"
OUT_DIR = "/opt/data/stock-web-system/frontend/dist/seo"

STOCK_META = {
    "000858": {"name": "五粮液", "keywords": "五粮液,000858,白酒股,五粮液财报,五粮液基本面分析"},
    "00700":  {"name": "腾讯控股", "keywords": "腾讯控股,00700,港股,腾讯财报,腾讯基本面分析"},
    "002342": {"name": "巨力索具", "keywords": "巨力索具,002342,索具,巨力财报,巨力索具基本面"},
    "300903": {"name": "科翔股份", "keywords": "科翔股份,300903,PCB,科翔财报,科翔基本面"},
}

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://miaoousc.xyz/seo/{filename}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://miaoousc.xyz/seo/{filename}">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<script type="application/ld+json">{ld_json}</script>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;max-width:760px;margin:0 auto;padding:24px 20px 60px;line-height:1.8;color:#1d1d1f;background:#fff}}
  h1{{font-size:26px;font-weight:700;margin:0 0 6px}}
  h2{{font-size:20px;font-weight:600;margin:28px 0 10px;color:#0071e3;border-bottom:2px solid #f0f0f0;padding-bottom:6px}}
  h3{{font-size:17px;font-weight:600;margin:20px 0 8px}}
  p{{margin:8px 0}}
  strong{{color:#1d1d1f}}
  table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}}
  th,td{{border:1px solid #d2d2d7;padding:8px 12px;text-align:left}}
  th{{background:#f5f5f7;font-weight:600}}
  td{{font-size:13px}}
  code{{background:rgba(0,113,227,0.08);padding:2px 6px;border-radius:4px;font-size:13px}}
  blockquote{{border-left:3px solid #0071e3;margin:12px 0;padding:8px 16px;background:#f5f5f7;color:#6e6e73;font-size:14px}}
  hr{{border:none;border-top:1px solid #e5e5e5;margin:20px 0}}
  .breadcrumb{{font-size:13px;color:#86868b;margin-bottom:20px}}
  .breadcrumb a{{color:#0071e3;text-decoration:none}}
  .cta{{display:inline-block;margin-top:32px;padding:12px 28px;background:#0071e3;color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:15px}}
  .cta:hover{{background:#005bb5}}
  .related{{margin-top:40px;padding:20px;background:#f5f5f7;border-radius:12px}}
  .related h3{{margin:0 0 12px;font-size:16px}}
  .related ul{{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px}}
  .related a{{color:#0071e3;text-decoration:none;font-size:14px;padding:6px 14px;background:#fff;border-radius:6px;border:1px solid #d2d2d7}}
  .related a:hover{{border-color:#0071e3}}
  .disclaimer{{margin-top:32px;padding:16px;background:#f5f5f7;border-radius:8px;font-size:13px;color:#86868b}}
  .subtitle{{font-size:14px;color:#86868b;margin-bottom:20px}}
</style>
</head>
<body>
<div class="breadcrumb">
  <a href="https://miaoousc.xyz/">元基鉴股</a> &rsaquo; {stock_name} 财报深度分析
</div>
<h1>{stock_name}（{stock_code}）财报深度分析</h1>
<p class="subtitle">分析日期：{date} | 数据来源：元基鉴股 AI 分析引擎 | 巨潮资讯网 + NotebookLM AI分析</p>
<hr>
<div id="report-content">
{report_html}
</div>
<a class="cta" href="https://miaoousc.xyz/">🚀 免费分析你的股票 →</a>
<div class="related">
  <h3>📊 更多示例报告</h3>
  <ul>
    {related_links}
  </ul>
</div>
<div class="disclaimer">
  ⚠️ 免责声明：本报告由 AI 自动生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。数据来源包括巨潮资讯网、新浪财经、同花顺等公开信息。
</div>
</body>
</html>'''


def md_to_html(md):
    """简易 Markdown → HTML"""
    md = md.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    md = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md, flags=re.M)
    md = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md, flags=re.M)
    md = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md, flags=re.M)
    md = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md)
    md = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md)
    md = re.sub(r'`([^`]+)`', r'<code>\1</code>', md)
    md = re.sub(r'^---$', '<hr>', md, flags=re.M)
    md = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', md, flags=re.M)

    lines = md.split('\n')
    result = []
    in_table = False
    for line in lines:
        if line.startswith('|') and line.rstrip().endswith('|'):
            cells = [c.strip() for c in line[1:-1].split('|')]
            if all(re.match(r'^:?-{3,}:?$', c) for c in cells):
                continue
            if not in_table:
                result.append('<table>')
                in_table = True
                tag = 'th'
            else:
                tag = 'td'
            result.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
        else:
            if in_table:
                result.append('</table>')
                in_table = False
            if line.strip():
                result.append(f'<p>{line}</p>')
            else:
                result.append('')
    if in_table:
        result.append('</table>')
    return '\n'.join(result)


os.makedirs(OUT_DIR, exist_ok=True)
conn = sqlite3.connect(DB_PATH)
today = datetime.date.today().isoformat()
codes = ["000858", "00700", "002342", "300903"]

all_links = []
for code in codes:
    meta = STOCK_META[code]
    row = conn.execute(
        "SELECT stock_name, report FROM sample_reports WHERE stock_code=?", (code,)
    ).fetchone()
    if not row:
        print(f"SKIP {code}: not in DB")
        continue

    name = meta["name"]
    report_html = md_to_html(row[1])

    # Build related links (all except self)
    other_links = []
    for oc in codes:
        if oc != code:
            om = STOCK_META[oc]
            other_links.append(
                f'<li><a href="/seo/{oc}-{om["name"]}.html">{om["name"]}（{oc}）</a></li>'
            )

    ld_json = (
        '{"@context":"https://schema.org","@type":"Article",'
        f'"headline":"{name}（{code}）财报深度分析 - 元基鉴股",'
        f'"description":"AI驱动的{name}财报深度分析报告。涵盖实时行情、基本面、财务指标等关键数据。",'
        f'"datePublished":"{today}",'
        '"author":{"@type":"Organization","name":"元基鉴股"},'
        '"publisher":{"@type":"Organization","name":"元基鉴股","url":"https://miaoousc.xyz/"}'
        '}'
    )

    filename = f"{code}-{name}.html"
    html = HTML_TEMPLATE.format(
        title=f"{name}（{code}）财报深度分析 - 元基鉴股",
        description=f"AI驱动的{name}（{code}）财报深度分析报告。涵盖实时行情、基本面分析、财务指标、估值分析等。元基鉴股 — 几分钟获得机构级分析。",
        keywords=meta["keywords"],
        filename=filename,
        ld_json=ld_json,
        stock_name=name,
        stock_code=code,
        date=today,
        report_html=report_html,
        related_links='\n    '.join(other_links),
    )

    out_path = os.path.join(OUT_DIR, filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"GENERATED: {filename} ({len(html)} bytes)")
    all_links.append(f"https://miaoousc.xyz/seo/{filename}")

conn.close()
print(f"\nDONE: {len(all_links)} pages → {OUT_DIR}")
for link in all_links:
    print(f"  {link}")
