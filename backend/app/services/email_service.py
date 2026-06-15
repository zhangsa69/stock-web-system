"""
邮件发送服务
使用 smtplib 发送分析报告邮件，支持 Gmail / 腾讯企业邮箱等 SMTP 服务
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """SMTP 邮件服务"""

    def send_report_email(
        self, to_email: str, stock_code: str, stock_name: str, report: str
    ) -> bool:
        """
        发送分析报告邮件

        Args:
            to_email: 收件人邮箱
            stock_code: 股票代码
            stock_name: 股票名称
            report: 分析报告 Markdown 文本

        Returns:
            是否发送成功
        """
        if not settings.smtp_host or not settings.smtp_user:
            logger.warning("SMTP 未配置，跳过邮件发送")
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = settings.smtp_from
        msg["To"] = to_email
        msg["Subject"] = f"【股票分析】{stock_code} {stock_name} 分析报告"

        # 纯文本版本
        text = (
            f"股票 {stock_name}({stock_code}) 的 AI 分析报告：\n\n"
            f"{report}\n\n"
            f"---\n"
            f"本邮件由 AI 股票分析平台自动发送"
        )
        msg.attach(MIMEText(text, "plain", "utf-8"))

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from, to_email, msg.as_string())
            logger.info(f"邮件已发送: {to_email} ({stock_code})")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            raise


email_service = EmailService()
