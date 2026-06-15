"""
Markdown 报告 → PDF 生成器
使用 WeasyPrint 将 md_to_html() 生成的 HTML 渲染为精美 PDF
"""
import logging
import os
from pathlib import Path

from weasyprint import HTML

from .report_html import md_to_html

logger = logging.getLogger("stock-analysis.pdf")

# PDF 缓存目录
PDF_CACHE = os.environ.get("PDF_CACHE_DIR", "/app/pdf_cache")


def generate_pdf(
    markdown: str,
    stock_code: str = "",
    output_path: str = "",
) -> str:
    """
    将 Markdown 报告渲染为 PDF 并保存到磁盘。

    Args:
        markdown: 分析报告 Markdown 原文
        stock_code: 股票代码（用于标题）
        output_path: 输出路径，为空则自动生成到 PDF_CACHE

    Returns:
        PDF 文件的绝对路径
    """
    # 生成输出路径
    if not output_path:
        Path(PDF_CACHE).mkdir(parents=True, exist_ok=True)
        safe_code = stock_code.replace("/", "_") if stock_code else "report"
        output_path = os.path.join(PDF_CACHE, f"{safe_code}_report.pdf")

    logger.info(
        "[PDF][GENERATING] 开始生成PDF | stock=%s output=%s",
        stock_code, output_path,
    )

    # 1. 生成 HTML（复用现有渲染器）
    html_str = md_to_html(markdown, stock_code=stock_code)

    # 2. HTML → PDF
    try:
        HTML(string=html_str).write_pdf(
            output_path,
            presentational_hints=True,  # 支持 <table width="..."> 等表现属性
        )
    except Exception:
        logger.exception("[PDF][FAILED] WeasyPrint 渲染失败")
        raise

    size_kb = os.path.getsize(output_path) / 1024
    logger.info(
        "[PDF][SUCCESS] PDF生成成功 | stock=%s path=%s size=%.1fKB",
        stock_code, output_path, size_kb,
    )
    return output_path
