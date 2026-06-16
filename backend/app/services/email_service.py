"""
邮件发送服务
使用 smtplib + asyncio.to_thread 避免阻塞事件循环
"""
import asyncio
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings

logger = logging.getLogger("stock-analysis.email")


def _send_sync(msg: MIMEMultipart) -> None:
    """同步 SMTP 发送（在 thread 中执行）"""
    server = None
    try:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, msg["To"], msg.as_string())
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


class EmailService:
    """SMTP 邮件服务"""

    @staticmethod
    async def send_verification_code(to_email: str, code: str) -> bool:
        """发送邮箱验证码（异步，不阻塞事件循环）"""
        if not settings.smtp_host or not settings.smtp_user:
            logger.error("[EMAIL_VERIFY] SMTP未配置")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.smtp_from
            msg["To"] = to_email
            msg["Subject"] = "【AI股票分析】邮箱验证码"

            html_body = f"""\
<html><body style="font-family: Arial, sans-serif; padding: 20px;">
  <h2 style="color: #D4A843;">AI 股票财报分析平台</h2>
  <p>您的验证码是：</p>
  <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px;
              color: #0A1929; background: #F0C060; display: inline-block;
              padding: 12px 24px; border-radius: 8px; margin: 16px 0;">
    {code}
  </div>
  <p style="color: #666; margin-top: 20px;">验证码 10 分钟内有效，请勿泄露。</p>
</body></html>"""
            msg.attach(MIMEText(f"您的验证码是：{code}，10分钟内有效。", "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # 在独立线程中发送，不阻塞事件循环
            await asyncio.to_thread(_send_sync, msg)

            logger.info("[EMAIL_VERIFY] 验证码已发送: %s", to_email)
            return True

        except Exception as e:
            logger.error("[EMAIL_VERIFY] 发送失败: %s reason=%s", to_email, str(e))
            return False

    @staticmethod
    def send_report_email(
        to_email: str,
        stock_code: str,
        stock_name: str,
        report: str,
        html_report: str = "",
    ) -> bool:
        """
        发送分析报告邮件 — 原始 .md 文件作为附件
        （在 Celery worker 中同步调用，不需要 async）
        """
        logger.info(
            "[EMAIL_SEND][START] 开始发送邮件 | to=%s stock=%s",
            to_email, stock_code,
        )

        if not settings.smtp_host or not settings.smtp_user:
            logger.error("[EMAIL_SEND][CONFIG_MISSING] SMTP未配置")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = settings.smtp_from
            msg["To"] = to_email
            msg["Subject"] = f"【股票分析】{stock_code} {stock_name} 分析报告"

            body = f"{stock_name}({stock_code}) 分析报告见附件。\n\n可在线下载：http://66.63.162.26/history"
            msg.attach(MIMEText(body, "plain", "utf-8"))

            filename = f"{stock_code}_{stock_name}_分析报告.md"
            part = MIMEText(report, "plain", "utf-8")
            part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
            msg.attach(part)

            logger.info("[EMAIL_SEND][MSG_BUILT] 附件构建完成 | to=%s file=%s", to_email, filename)

        except Exception as e:
            logger.error("[EMAIL_SEND][BUILD_FAIL] 邮件构建失败 | to=%s reason=%s", to_email, str(e))
            raise

        _send_sync(msg)
        logger.info("[EMAIL_SEND][SUCCESS] 邮件发送成功 | to=%s stock=%s", to_email, stock_code)
        return True


email_service = EmailService()
