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
