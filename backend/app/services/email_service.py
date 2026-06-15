"""
邮件发送服务
使用 smtplib 发送 HTML 分析报告邮件
"""
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings

logger = logging.getLogger("stock-analysis.email")


class EmailService:
    """SMTP 邮件服务"""

    def send_report_email(
        self,
        to_email: str,
        stock_code: str,
        stock_name: str,
        report: str,
        html_report: str = "",
    ) -> bool:
        """
        发送 HTML 分析报告邮件

        Args:
            to_email: 收件人邮箱
            stock_code: 股票代码
            stock_name: 股票名称
            report: Markdown 报告（作为 plain text 兜底）
            html_report: md2html 生成的 HTML 报告

        Returns:
            是否发送成功
        """
        logger.info(
            "[EMAIL_SEND][START] 开始发送邮件 | to=%s stock=%s",
            to_email, stock_code,
        )

        if not settings.smtp_host or not settings.smtp_user:
            logger.error(
                "[EMAIL_SEND][CONFIG_MISSING] SMTP未配置 | host=%s user=%s",
                settings.smtp_host or "(空)", settings.smtp_user or "(空)",
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.smtp_from
            msg["To"] = to_email
            msg["Subject"] = f"【股票分析】{stock_code} {stock_name} 分析报告"

            # Plain text（老邮件客户端兜底）
            text_body = report if report else f"{stock_name}({stock_code}) 分析报告见 HTML 部分。"
            msg.attach(MIMEText(text_body, "plain", "utf-8"))

            # HTML（主力，md2html 生成的精美 HTML）
            if html_report:
                msg.attach(MIMEText(html_report, "html", "utf-8"))
                logger.info(
                    "[EMAIL_SEND][MSG_BUILT] HTML邮件构建完成 | to=%s html_len=%d",
                    to_email, len(html_report),
                )
            else:
                logger.warning("[EMAIL_SEND][NO_HTML] html_report 为空，仅发 plain text")

        except Exception as e:
            logger.error(
                "[EMAIL_SEND][BUILD_FAIL] 邮件构建失败 | to=%s reason=%s traceback=%s",
                to_email, str(e), traceback.format_exc(),
            )
            raise

        # SMTP 发送
        server = None
        try:
            logger.info(
                "[EMAIL_SEND][CONNECTING] 连接SMTP | host=%s port=%s tls=%s",
                settings.smtp_host, settings.smtp_port, settings.smtp_use_tls,
            )
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.set_debuglevel(0)

            if settings.smtp_use_tls:
                server.starttls()

            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to_email, msg.as_string())
            logger.info(
                "[EMAIL_SEND][SUCCESS] 邮件发送成功 | to=%s stock=%s",
                to_email, stock_code,
            )
            return True

        except Exception as e:
            logger.error(
                "[EMAIL_SEND][FAILED] 发送失败 | to=%s reason=%s",
                to_email, str(e),
            )
            raise
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass


email_service = EmailService()
