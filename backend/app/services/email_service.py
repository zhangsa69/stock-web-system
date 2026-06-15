"""
邮件发送服务
使用 smtplib 发送分析报告邮件，支持 Gmail / 腾讯企业邮箱等 SMTP 服务
"""
import smtplib
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
from .report_html import md_to_html

logger = logging.getLogger("stock-analysis.email")


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
        logger.info(
            "[EMAIL_SEND][START] 开始发送邮件 | to=%s stock=%s",
            to_email, stock_code,
        )

        # 检查 SMTP 配置
        if not settings.smtp_host or not settings.smtp_user:
            logger.error(
                "[EMAIL_SEND][CONFIG_MISSING] SMTP未配置 | host=%s user=%s",
                settings.smtp_host or "(空)", settings.smtp_user or "(空)",
            )
            return False

        # 构建邮件
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.smtp_from
            msg["To"] = to_email
            msg["Subject"] = f"【股票分析】{stock_code} {stock_name} 分析报告"

            # Plain text（兜底，老邮件客户端）
            text = (
                f"股票 {stock_name}({stock_code}) 的 AI 分析报告：\n\n"
                f"{report}\n\n"
                f"---\n"
                f"本邮件由 AI 股票分析平台自动发送"
            )
            msg.attach(MIMEText(text, "plain", "utf-8"))

            # HTML（主力，现代邮件客户端）
            html_body = md_to_html(report, stock_code=stock_code)
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            logger.debug(
                "[EMAIL_SEND][MSG_BUILT] 邮件构建完成 | to=%s subject=%s plain=%d html=%d",
                to_email, msg["Subject"], len(text), len(html_body),
            )
        except Exception as e:
            logger.error(
                "[EMAIL_SEND][BUILD_FAIL] 邮件构建失败 | to=%s reason=%s traceback=%s",
                to_email, str(e), traceback.format_exc(),
            )
            raise

        # SMTP 连接
        server = None
        try:
            logger.info(
                "[EMAIL_SEND][CONNECTING] 连接SMTP | host=%s port=%s tls=%s",
                settings.smtp_host, settings.smtp_port, settings.smtp_use_tls,
            )
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.set_debuglevel(0)  # 不输出敏感调试信息

            if settings.smtp_use_tls:
                server.starttls()
                logger.debug("[EMAIL_SEND][TLS_OK] TLS协商成功")

            # 登录
            server.login(settings.smtp_user, settings.smtp_password)
            logger.debug("[EMAIL_SEND][LOGIN_OK] SMTP登录成功 | user=%s", settings.smtp_user)

            # 发送
            server.sendmail(settings.smtp_from, to_email, msg.as_string())
            logger.info(
                "[EMAIL_SEND][SUCCESS] 邮件发送成功 | to=%s stock=%s",
                to_email, stock_code,
            )
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                "[EMAIL_SEND][AUTH_FAIL] SMTP认证失败 | host=%s user=%s reason=%s",
                settings.smtp_host, settings.smtp_user, str(e),
            )
            raise

        except smtplib.SMTPConnectError as e:
            logger.error(
                "[EMAIL_SEND][CONNECT_FAIL] SMTP连接失败 | host=%s port=%s reason=%s",
                settings.smtp_host, settings.smtp_port, str(e),
            )
            raise

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(
                "[EMAIL_SEND][RECIPIENT_REFUSED] 收件人拒绝 | to=%s reason=%s",
                to_email, str(e),
            )
            raise

        except smtplib.SMTPSenderRefused as e:
            logger.error(
                "[EMAIL_SEND][SENDER_REFUSED] 发件人拒绝 | from=%s reason=%s",
                settings.smtp_from, str(e),
            )
            raise

        except smtplib.SMTPDataError as e:
            logger.error(
                "[EMAIL_SEND][DATA_ERROR] SMTP数据错误 | to=%s reason=%s",
                to_email, str(e),
            )
            raise

        except smtplib.SMTPException as e:
            logger.error(
                "[EMAIL_SEND][SMTP_ERROR] SMTP通用错误 | to=%s reason=%s traceback=%s",
                to_email, str(e), traceback.format_exc(),
            )
            raise

        except Exception as e:
            logger.error(
                "[EMAIL_SEND][UNKNOWN_ERROR] 邮件发送未知错误 | to=%s reason=%s traceback=%s",
                to_email, str(e), traceback.format_exc(),
            )
            raise

        finally:
            if server:
                try:
                    server.quit()
                    logger.debug("[EMAIL_SEND][CONN_CLOSED] SMTP连接已关闭")
                except Exception:
                    pass


email_service = EmailService()
