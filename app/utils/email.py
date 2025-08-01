
# app/utils/email.py
# -*- coding: utf-8 -*-
"""
邮件工具
提供邮件发送功能
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from jinja2 import Environment, FileSystemLoader, Template
from loguru import logger

from app.config import settings


class EmailManager:
    """邮件管理器"""

    def __init__(self):
        """初始化邮件管理器"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.email_from = settings.EMAIL_FROM or settings.SMTP_USER
        self.email_from_name = settings.EMAIL_FROM_NAME or settings.APP_NAME

        # 模板环境
        self.template_env = Environment(
            loader=FileSystemLoader("templates/email"),
            autoescape=True
        )

        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def send_email(
            self,
            to_emails: List[str],
            subject: str,
            content: str,
            content_type: str = "html",
            cc_emails: Optional[List[str]] = None,
            bcc_emails: Optional[List[str]] = None,
            attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to_emails: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 (html/plain)
            cc_emails: 抄送列表
            bcc_emails: 密送列表
            attachments: 附件列表

        Returns:
            bool: 发送成功
        """

        try:
            # 在线程池中执行发送操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._send_email_sync,
                to_emails,
                subject,
                content,
                content_type,
                cc_emails,
                bcc_emails,
                attachments
            )

            return result

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def _send_email_sync(
            self,
            to_emails: List[str],
            subject: str,
            content: str,
            content_type: str = "html",
            cc_emails: Optional[List[str]] = None,
            bcc_emails: Optional[List[str]] = None,
            attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        同步发送邮件

        Args:
            to_emails: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型
            cc_emails: 抄送列表
            bcc_emails: 密送列表
            attachments: 附件列表

        Returns:
            bool: 发送成功
        """

        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = f"{self.email_from_name} <{self.email_from}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject

            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)

            # 添加邮件内容
            msg.attach(MIMEText(content, content_type, 'utf-8'))

            # 添加附件
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)

            # 连接SMTP服务器
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            if self.smtp_tls:
                server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # 发送邮件
            all_recipients = to_emails[:]
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)

            server.send_message(msg, to_addrs=all_recipients)
            server.quit()

            logger.info(f"邮件发送成功: {subject} -> {to_emails}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """
        添加附件

        Args:
            msg: 邮件对象
            attachment: 附件信息
        """

        try:
            file_path = Path(attachment.get("path", ""))
            filename = attachment.get("filename") or file_path.name

            if not file_path.exists():
                logger.warning(f"附件文件不存在: {file_path}")
                return

            # 读取文件
            with open(file_path, "rb") as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())

            # 编码
            encoders.encode_base64(part)

            # 设置头信息
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            msg.attach(part)

        except Exception as e:
            logger.error(f"添加附件失败: {e}")

    async def send_template_email(
            self,
            to_emails: List[str],
            subject: str,
            template_name: str,
            template_data: Dict[str, Any],
            cc_emails: Optional[List[str]] = None,
            bcc_emails: Optional[List[str]] = None,
            attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        发送模板邮件

        Args:
            to_emails: 收件人列表
            subject: 邮件主题
            template_name: 模板名称
            template_data: 模板数据
            cc_emails: 抄送列表
            bcc_emails: 密送列表
            attachments: 附件列表

        Returns:
            bool: 发送成功
        """

        try:
            # 渲染模板
            template = self.template_env.get_template(f"{template_name}.html")
            content = template.render(**template_data)

            # 发送邮件
            return await self.send_email(
                to_emails=to_emails,
                subject=subject,
                content=content,
                content_type="html",
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                attachments=attachments
            )

        except Exception as e:
            logger.error(f"模板邮件发送失败: {e}")
            return False

    async def send_verification_email(
            self,
            email: str,
            username: str,
            verification_code: str
    ) -> bool:
        """
        发送验证邮件

        Args:
            email: 邮箱地址
            username: 用户名
            verification_code: 验证码

        Returns:
            bool: 发送成功
        """

        subject = f"【{settings.APP_NAME}】邮箱验证码"

        template_data = {
            "username": username,
            "verification_code": verification_code,
            "app_name": settings.APP_NAME,
            "valid_minutes": 5
        }

        return await self.send_template_email(
            to_emails=[email],
            subject=subject,
            template_name="verification",
            template_data=template_data
        )

    async def send_password_reset_email(
            self,
            email: str,
            username: str,
            reset_link: str
    ) -> bool:
        """
        发送密码重置邮件

        Args:
            email: 邮箱地址
            username: 用户名
            reset_link: 重置链接

        Returns:
            bool: 发送成功
        """

        subject = f"【{settings.APP_NAME}】密码重置"

        template_data = {
            "username": username,
            "reset_link": reset_link,
            "app_name": settings.APP_NAME,
            "valid_hours": 24
        }

        return await self.send_template_email(
            to_emails=[email],
            subject=subject,
            template_name="password_reset",
            template_data=template_data
        )


# 全局邮件管理器实例
email_manager = EmailManager()


