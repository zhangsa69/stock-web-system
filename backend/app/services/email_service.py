"""
邮件发送服务
使用 smtplib 发送 .md 分析报告附件
"""
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from ..config import settings

logger = logging.getLogger("stock-analysis.email")


class EmailService:
    """SMTP 邮件服务"""

    @staticmethod
    async def send_verification_code(to_email: str, code: str) -> bool:
        """发送邮箱验证码"""
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

            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to_email, msg.as_string())
            server.quit()

            logger.info("[EMAIL_VERIFY] 验证码已发送: %s", to_email)
            return True

        except Exception as e:
            logger.error("[EMAIL_VERIFY] 发送失败: %s reason=%s", to_email, str(e))
            return False

    def send_report_email(
        self,
        to_email: str,
        stock_code: str,
        stock_name: str,
        report: str,
        html_report: str = "",
    ) -> bool:
        """
        发送分析报告邮件 — 原始 .md 文件作为附件

        Args:
            to_email: 收件人邮箱
            stock_code: 股票代码
            stock_name: 股票名称
            report: Markdown 报告
            html_report: 已废弃，保留兼容性
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

            # 正文
            body = f"{stock_name}({stock_code}) 分析报告见附件。\n\n可在线下载：http://66.63.162.26/history"
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # 附件：原始 .md 文件
            filename = f"{stock_code}_{stock_name}_分析报告.md"
            part = MIMEBase("application", "octet-stream")
            part.set_payload(report.encode("utf-8"))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"',
            )
            msg.attach(part)

            logger.info("[EMAIL_SEND][MSG_BUILT] 附件构建完成 | to=%s file=%s", to_email, filename)

        except Exception as e:
            logger.error(
                "[EMAIL_SEND][BUILD_FAIL] 邮件构建失败 | to=%s reason=%s",
                to_email, str(e),
            )
            raise

        server = None
        try:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.set_debuglevel(0)
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to_email, msg.as_string())
            logger.info("[EMAIL_SEND][SUCCESS] 邮件发送成功 | to=%s stock=%s", to_email, stock_code)
            return True

        except Exception as e:
            logger.error("[EMAIL_SEND][FAILED] 发送失败 | to=%s reason=%s", to_email, str(e))
            raise
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass


email_service = EmailService()
