"""
财报 Markdown → 响应式 HTML 邮件渲染器（v3）
- 状态机解析：列表项续行自动缩进，不再散架
- 全内联样式，兼容 Gmail/163/QQ
- 专业研报视觉：层级标题、强调标签、表格、排雷清单
"""

import re

# ── Design tokens ──
C_PRIMARY   = "#1e40af"
C_ACCENT    = "#3b82f6"
C_BG        = "#f0f2f5"
C_CARD      = "#ffffff"
C_TEXT      = "#1f2937"
C_MUTED     = "#6b7280"
C_BORDER    = "#e5e7eb"
C_TH_BG     = "#1e3a5f"
C_STRIPE    = "#f8fafc"
C_GREEN     = "#059669"
C_RED       = "#dc2626"
C_AMBER     = "#d97706"
C_QUOTE_BG  = "#eff6ff"
C_QUOTE_BD  = "#3b82f6"
FONT        = "-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei','Hiragino Sans GB','Segoe UI',Arial,sans-serif"
MONO        = "'SF Mono',Menlo,Consolas,monospace"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _span(text: str) -> str:
    """行内 Markdown → HTML（**bold**, *italic*, `code`, ✅❌ emoji）"""
    text = re.sub(r"\*\*(.+?)\*\*",
                  r'<strong style="color:#111827;font-weight:700;">\1</strong>', text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+?)`",
                  r'<code style="background:#f1f5f9;color:#db2777;padding:1px 5px;'
                  r'border-radius:3px;font-size:13px;font-family:' + MONO + ';">\1</code>', text)
    text = text.replace("✅", '<span style="color:#059669;font-weight:700;">✅</span>')
    text = text.replace("❌", '<span style="color:#dc2626;font-weight:700;">❌</span>')
    text = text.replace("🟢", '<span style="color:#059669;">🟢</span>')
    text = text.replace("🟡", '<span style="color:#d97706;">🟡</span>')
    text = text.replace("🔴", '<span style="color:#dc2626;">🔴</span>')
    return text


def _table_html(lines: list[str], start: int) -> tuple[str, int]:
    """Markdown 表格 → 响应式 HTML <table>"""
    rows = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(lines[i])
        i += 1
    if len(rows) < 2:
        return "", start

    header = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    ncols = len(header)

    # 处理对齐分隔行
    data_start = 1
    aligns = ["left"] * ncols
    if len(rows) > 1 and re.match(r"^[\|\s\-:]+$", rows[1].strip()):
        for ci, c in enumerate(rows[1].strip().strip("|").split("|")):
            c = c.strip()
            if c.startswith(":") and c.endswith(":"): aligns[ci] = "center"
            elif c.endswith(":"):                      aligns[ci] = "right"
        data_start = 2
    while len(aligns) < ncols:
        aligns.append("left")

    html = (
        '<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;margin:16px 0;border-radius:6px;'
        'border:1px solid ' + C_BORDER + ';">'
        '<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="width:100%;border-collapse:collapse;font-size:14px;min-width:420px;">'
        '<thead><tr>'
    )
    for cell in header:
        html += (
            f'<th style="background:{C_TH_BG};color:#fff;padding:11px 14px;text-align:left;'
            f'font-weight:600;font-size:13px;text-transform:uppercase;letter-spacing:.3px;'
            f'font-family:{FONT};">{_span(_esc(cell))}</th>'
        )
    html += '</tr></thead><tbody>'

    for ri in range(data_start, len(rows)):
        cells = [c.strip() for c in rows[ri].strip().strip("|").split("|")]
        while len(cells) < ncols: cells.append("")
        bg = C_STRIPE if (ri - data_start) % 2 == 0 else "#fff"
        html += f'<tr style="background:{bg};">'
        for ci in range(ncols):
            a = aligns[ci] if ci < len(aligns) else "left"
            html += (
                f'<td style="padding:10px 14px;border-bottom:1px solid {C_BORDER};'
                f'text-align:{a};font-family:{FONT};">{_span(_esc(cells[ci]))}</td>'
            )
        html += '</tr>'
    html += '</tbody></table></div>'
    return html, i


def _clean_report(md: str) -> str:
    """去除 NotebookLM Unicode 画框表格"""
    lines = md.split("\n")
    out, in_box = [], False
    for line in lines:
        s = line.strip()
        box = [c for c in s if c > "\u2500"]
        if box and all(c in "┏┓┗┛┃━┳┻┫┣┡┩┝┥┬┴┼╋╂╉╊╀╄┿│╭╮╰╯▔ " for c in box):
            in_box = True; continue
        if in_box and not box:
            in_box = False
            if not s: continue
        if in_box: continue
        out.append(line)
    return "\n".join(out).strip()


def md_to_html(md: str, stock_code: str = "") -> str:
    md = _clean_report(md)
    lines = md.split("\n")

    # ── 提取主标题 ──
    title = stock_code
    for line in lines[:6]:
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            title = _esc(m.group(1))
            break

    # ── HTML 头部 ──
    html = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>' + title + '</title>'
        '<style>'
        '@media only screen and (max-width:480px){'
        '.r-body{padding:12px 8px!important}'
        '.r-card{padding:18px 12px!important}'
        '.r-h1{font-size:18px!important}'
        '.r-h2{font-size:15px!important}'
        '.r-h3{font-size:14px!important}'
        '.r-p,.r-li{font-size:14px!important}'
        '}</style></head>'
        '<body style="margin:0;padding:0;background:' + C_BG + ';'
        'font-family:' + FONT + ';color:' + C_TEXT + ';'
        'font-size:15px;line-height:1.8;-webkit-font-smoothing:antialiased;">'
        '<div class="r-body" style="max-width:640px;margin:0 auto;padding:24px 16px;">'
        '<div class="r-card" style="background:' + C_CARD + ';border-radius:10px;'
        'padding:36px 30px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
    )

    # ── 报告头部 ──
    html += (
        '<div style="text-align:center;padding-bottom:20px;margin-bottom:28px;'
        'border-bottom:2px solid ' + C_PRIMARY + ';">'
        '<h1 class="r-h1" style="font-size:22px;color:' + C_PRIMARY + ';'
        'margin:0 0 6px;font-weight:800;letter-spacing:.5px;">' + title + '</h1>'
    )
    if stock_code and stock_code not in title:
        html += (
            '<span style="display:inline-block;background:' + C_PRIMARY + ';color:#fff;'
            'padding:2px 10px;border-radius:10px;font-size:12px;font-weight:600;">'
            + _esc(stock_code) + '</span>'
        )
    html += '</div>'

    # ── 状态机逐行解析 ──
    i = 0
    in_list = False       # 是否在 <ul> / <ol> 内部
    list_tag = ""         # "ul" 或 "ol"
    li_open = False       # 当前 <li> 是否已打开（等待内容或续行）

    def _close_li():
        nonlocal li_open
        if li_open:
            return "</li>\n"
        return ""

    def _close_list():
        nonlocal in_list, list_tag, li_open
        s = ""
        if li_open:
            s += "</li>\n"; li_open = False
        if in_list:
            s += f"</{list_tag}>\n"; in_list = False; list_tag = ""
        return s

    while i < len(lines):
        s = lines[i].strip()

        # 空行：关闭列表（但不关闭可能未完成的事项，空行在列表中表示段落分隔）
        if not s:
            # 在列表内部且 li 已打开 → 关闭 li（空行结束这个列表项）
            if in_list and li_open:
                html += "</li>\n"
                li_open = False
            i += 1
            continue

        # ── 水平线 ──
        if re.match(r"^[-*_]{3,}$", s):
            html += _close_list()
            html += '<hr style="border:none;border-top:1px solid ' + C_BORDER + ';margin:24px 0;">\n'
            i += 1
            continue

        # ── 标题 ──
        h = re.match(r"^(#{1,3})\s+(.+)", s)
        if h:
            html += _close_list()
            lv, text = len(h.group(1)), _span(_esc(h.group(2)))
            if lv == 1:
                i += 1; continue  # 已用作顶部标题，跳过
            elif lv == 2:
                html += (
                    '<h2 class="r-h2" style="font-size:18px;color:' + C_PRIMARY + ';'
                    'margin:30px 0 12px;padding:6px 0 6px 12px;'
                    'border-left:4px solid ' + C_ACCENT + ';font-weight:700;'
                    'line-height:1.4;">' + text + '</h2>\n'
                )
            else:
                html += (
                    '<h3 class="r-h3" style="font-size:15px;color:#374151;'
                    'margin:20px 0 6px;font-weight:700;">' + text + '</h3>\n'
                )
            i += 1
            continue

        # ── 引用 ──
        if s.startswith(">"):
            html += _close_list()
            html += (
                '<blockquote style="margin:14px 0;padding:14px 18px;'
                'background:' + C_QUOTE_BG + ';border-left:4px solid ' + C_QUOTE_BD + ';'
                'border-radius:0 6px 6px 0;color:#374151;font-size:14px;">'
                + _span(_esc(s[1:].strip())) + '</blockquote>\n'
            )
            i += 1
            continue

        # ── 表格 ──
        if s.startswith("|") and "|" in s[1:]:
            html += _close_list()
            tbl, ni = _table_html(lines, i)
            if tbl:
                html += tbl
                i = ni
                continue

        # ── 无序列表项 ──
        li_u = re.match(r"^[\*\-]\s+(.+)", s)
        if li_u:
            content = _span(_esc(li_u.group(1)))
            if not in_list or list_tag != "ul":
                html += _close_list()
                html += '<ul style="padding-left:18px;margin:8px 0;list-style-type:disc;">\n'
                in_list = True; list_tag = "ul"
            else:
                html += _close_li()
            html += (
                '<li class="r-li" style="margin:6px 0;line-height:1.75;'
                'font-size:15px;">' + content
            )
            li_open = True
            i += 1
            continue

        # ── 有序列表项 ──
        li_o = re.match(r"^\d+\.\s+(.+)", s)
        if li_o:
            content = _span(_esc(li_o.group(1)))
            if not in_list or list_tag != "ol":
                html += _close_list()
                html += '<ol style="padding-left:18px;margin:8px 0;">\n'
                in_list = True; list_tag = "ol"
            else:
                html += _close_li()
            html += (
                '<li class="r-li" style="margin:6px 0;line-height:1.75;'
                'font-size:15px;">' + content
            )
            li_open = True
            i += 1
            continue

        # ── 普通段落 ──
        content = _span(_esc(s))
        if in_list and li_open:
            # 列表内的续行 → 作为 <li> 内部的段落，缩进
            html += (
                '<br><span style="display:block;padding-left:8px;'
                'font-size:14px;color:#4b5563;">' + content + '</span>'
            )
        elif in_list and not li_open:
            # 列表内但 li 未打开 → 关闭列表，作为普通段落
            html += _close_list()
            html += '<p class="r-p" style="margin:8px 0;line-height:1.8;">' + content + '</p>\n'
        else:
            html += '<p class="r-p" style="margin:8px 0;line-height:1.8;">' + content + '</p>\n'
        i += 1

    html += _close_list()

    # ── 页脚 ──
    html += (
        '<div style="margin-top:32px;padding-top:16px;border-top:1px solid ' + C_BORDER + ';'
        'text-align:center;font-size:12px;color:' + C_MUTED + ';">'
        '📊 本报告由 AI 股票分析平台自动生成 · 仅供参考，不构成投资建议'
        '</div>'
    )

    html += '</div></div></body></html>'
    return html
