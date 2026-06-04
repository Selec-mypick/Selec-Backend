def get_verification_email_html(verification_code: str) -> str:
    """
    이메일 인증번호 HTML 템플릿
    
    Args:
        verification_code: 6자리 인증번호
        
    Returns:
        str: HTML 형식의 이메일 본문
    """
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdEdge 이메일 인증</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 4px; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #ffffff; border-bottom: 1px solid #e0e0e0;">
                            <h1 style="margin: 0; font-size: 24px; color: #333333; font-weight: normal;">AdEdge</h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333; line-height: 1.6;">
                                안녕하세요,
                            </p>
                            <p style="margin: 0 0 30px 0; font-size: 16px; color: #333333; line-height: 1.6;">
                                이메일 인증을 위한 인증번호를 발송해드립니다.
                            </p>
                            
                            <!-- Verification Code -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center" style="padding: 20px; background-color: #f8f8f8; border: 2px solid #e0e0e0; border-radius: 4px;">
                                        <span style="font-size: 32px; font-weight: bold; color: #333333; letter-spacing: 8px; font-family: 'Courier New', monospace;">{verification_code}</span>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0 0; font-size: 14px; color: #666666; line-height: 1.6;">
                                • 인증번호는 <strong>3분간</strong> 유효합니다.<br>
                                • 인증번호는 <strong>1회만</strong> 사용 가능합니다.<br>
                                • 본인이 요청하지 않은 경우 이 이메일을 무시하세요.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f8f8f8; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0; font-size: 12px; color: #999999; text-align: center;">
                                이 이메일은 자동으로 발송된 메일입니다.<br>
                                © 2024 AdEdge. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

