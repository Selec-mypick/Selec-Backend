import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import settings
from app.core.exception import ServerException


class EmailClient:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.use_tls = settings.smtp_use_tls

    async def send_email(
            self,
            to_email: str,
            subject: str,
            html_content: str,
            text_content: Optional[str] = None
    ) -> None:
        """
        이메일 전송
        
        Args:
            to_email: 수신자 이메일 주소
            subject: 이메일 제목
            html_content: HTML 형식의 이메일 본문
            text_content: 텍스트 형식의 이메일 본문 (선택사항)
        """
        try:
            # 메시지 생성
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject

            # 텍스트 본문 추가
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)

            # HTML 본문 추가
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # SMTP 서버에 연결하여 이메일 전송
            # 포트 587은 STARTTLS, 포트 465는 SSL 사용
            if self.smtp_port == 465:
                # 포트 465는 SSL 연결
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=True,
                    start_tls=False
                )
            else:
                # 포트 587은 STARTTLS 사용
                smtp = aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=False,
                    start_tls=self.use_tls
                )

            await smtp.connect()
            await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(message)
            await smtp.quit()

        except Exception as e:
            raise ServerException(f"이메일 전송 중 오류가 발생했습니다: {str(e)}")

