"""
财报 Markdown → HTML 邮件渲染器
将 NotebookLM 生成的 Markdown 报告转为专业 HTML 研报样式
"""

import re

CSS = """
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                 'Microsoft YaHei', 'Hiragino Sans GB', sans-serif;
    font-size: 15px; line-height: 1.8; color: #1a1a1a;
    max-width: 680px; margin: 0 auto; padding: 24px 20px;
    background: #fafafa;
  }
  .report-card {
    background: #fff; border-radius: 8px; padding: 32px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .report-header {
    text-align: center; padding-bottom: 20px; margin-bottom: 28px;
    border-bottom: 3px solid #1a56db;
  }
  .report-header h1 { font-size: 22px; color: #1a56db; margin: 0; }
  .report-header .stock-code { font-size: 14px; color: #6b7280; margin-top: 4px; }
  h2 {
    font-size: 18px; color: #1a56db; margin: 32px 0 12px;
    padding-left: 12px; border-left: 4px solid #1a56db;
  }
  h3 { font-size: 16px; color: #374151; margin: 20px 0 8px; }
  p { margin: 8px 0; }
  strong { color: #111827; }
  ul { padding-left: 20px; margin: 8px 0; }
  li { margin: 4px 0; }
  hr { border: none; border-top: 1px solid #e5e7eb; margin: 24px 0; }
  table {
    width: 100%; border-collapse: collapse; margin: 16px 0;
    font-size: 14px;
  }
  th {
    background: #1a56db; color: #fff; padding: 10px 12px;
    text-align: left; font-weight: 600;
  }
  td {
    padding: 8px 12px; border-bottom: 1px solid #e5e7eb;
  }
  tr:nth-child(even) td { background: #f8fafc; }
  .highlight-green { color: #059669; font-weight: 600; }
  .highlight-red { color: #dc2626; font-weight: 600; }
  .pass { color: #059669; }
  .fail { color: #dc2626; }
  .checklist td:first-child { width: 32px; text-align: center; font-size: 18px; }
  blockquote {
    margin: 12px 0; padding: 12px 16px; background: #eff6ff;
    border-left: 4px solid #1a56db; border-radius: 0 4px 4px 0;
    color: #374151;
  }
  .report-footer {
    margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb;
    text-align: center; font-size: 12px; color: #9ca3af;
  }
</style>
"""


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline_format(text: str) -> str:
    """Handle **bold**, * italic, inline `code`"""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    return text


def _parse_table(lines: list[str], start: int) -> tuple[str, int]:
    """Parse a markdown table, return (html, next_line_index)"""
    rows = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(lines[i])
        i += 1

    if len(rows) < 2:
        return "", start

    html = '<table>\n'
    for ri, row in enumerate(rows):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if ri == 1 and all(re.match(r"^[-: ]+$", c) for c in cells):
            continue  # skip separator row
        tag = "th" if ri == 0 else "td"
        html += "<tr>\n"
        for cell in cells:
            html += f"<{tag}>{_inline_format(_escape(cell))}</{tag}>\n"
        html += "</tr>\n"
    html += "</table>\n"
    return html, i


def md_to_html(md: str, stock_code: str = "") -> str:
    """Convert markdown report to styled HTML."""
    # Strip leading Unicode box-drawing table (notebook listing)
    md = re.sub(r"^[┏┓┗┛┃━┳┻┫┣┡┩┝┥┬┴┼╋╂╉╊╀╄┿\s\d\w\-\.：\u4e00-\u9fff]+\n", "", md, count=15)
    md = md.strip()

    lines = md.split("\n")
    html = CSS + '\n<div class="report-card">\n'

    # Extract title for header
    title = stock_code
    for line in lines[:5]:
        m = re.match(r"^# (.+)", line)
        if m:
            title = m.group(1)
            break

    html += '<div class="report-header">\n'
    html += f'<h1>{_escape(title)}</h1>\n'
    if stock_code and stock_code not in title:
        html += f'<div class="stock-code">{_escape(stock_code)}</div>\n'
    html += '</div>\n'

    i = 0
    in_list = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty
        if not stripped:
            if in_list:
                html += "</ul>\n"
                in_list = False
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}$", stripped):
            if in_list:
                html += "</ul>\n"
                in_list = False
            html += "<hr>\n"
            i += 1
            continue

        # Table
        if stripped.startswith("|") and "|" in stripped[1:]:
            if in_list:
                html += "</ul>\n"
                in_list = False
            table_html, next_i = _parse_table(lines, i)
            if table_html:
                html += table_html
                i = next_i
                continue

        # Blockquote
        if stripped.startswith(">"):
            if in_list:
                html += "</ul>\n"
                in_list = False
            content = stripped[1:].strip()
            html += f"<blockquote>{_inline_format(_escape(content))}</blockquote>\n"
            i += 1
            continue

        # Headings
        h = re.match(r"^(#{1,3})\s+(.+)", stripped)
        if h:
            if in_list:
                html += "</ul>\n"
                in_list = False
            level = len(h.group(1))
            text = _inline_format(_escape(h.group(2)))
            if level == 1:
                continue  # skip, already in header
            html += f"<h{level}>{text}</h{level}>\n"
            i += 1
            continue

        # List items
        li = re.match(r"^[\*\-]\s+(.+)", stripped)
        if li:
            if not in_list:
                html += "<ul>\n"
                in_list = True
            content = _inline_format(_escape(li.group(1)))
            # Colorize ✅/❌
            content = content.replace("✅", '<span class="pass">✅</span>')
            content = content.replace("❌", '<span class="fail">❌</span>')
            html += f"<li>{content}</li>\n"
            i += 1
            continue

        # Regular paragraph
        if in_list:
            html += "</ul>\n"
            in_list = False
        content = _inline_format(_escape(stripped))
        content = content.replace("✅", '<span class="pass">✅</span>')
        content = content.replace("❌", '<span class="fail">❌</span>')
        html += f"<p>{content}</p>\n"
        i += 1

    if in_list:
        html += "</ul>\n"

    html += '<div class="report-footer">本报告由 AI 股票分析平台自动生成 · 仅供参考，不构成投资建议</div>\n'
    html += "</div>\n"
    return html
