import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

# Trong triển khai thực tế, bạn nên sử dụng biến môi trường cho các thông tin này
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "your_password"
DEFAULT_FROM_EMAIL = "noreply@codingplatform.com"

def send_email(to_email: str, subject: str, html_content: str, 
               from_email: Optional[str] = None, cc: Optional[List[str]] = None):
    """
    Gửi email sử dụng SMTP
    
    Lưu ý: Đây chỉ là mẫu cơ bản, trong ứng dụng thực tế bạn nên sử dụng
    các dịch vụ email như SendGrid, Amazon SES, Mailgun, v.v.
    """
    try:
        # Tạo message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email or DEFAULT_FROM_EMAIL
        msg['To'] = to_email
        
        if cc:
            msg['Cc'] = ", ".join(cc)
            recipients = [to_email] + cc
        else:
            recipients = [to_email]
        
        # Thêm nội dung HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Kết nối đến SMTP server và gửi email
        # Trong triển khai thực tế, bạn nên xử lý ngoại lệ và retry
        # server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        # server.starttls()
        # server.login(SMTP_USERNAME, SMTP_PASSWORD)
        # server.sendmail(msg['From'], recipients, msg.as_string())
        # server.quit()
        
        print(f"Email would be sent to {to_email} with subject: {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_welcome_email(to_email: str, username: str):
    """Gửi email chào mừng người dùng mới"""
    subject = "Welcome to Coding Platform"
    html_content = f"""
    <html>
    <head></head>
    <body>
        <h1>Welcome to Coding Platform, {username}!</h1>
        <p>Thank you for registering on our platform. We're excited to have you join our community of coders!</p>
        <p>Here are some things you can do:</p>
        <ul>
            <li>Solve programming problems</li>
            <li>Participate in contests</li>
            <li>Track your progress</li>
            <li>Join the community</li>
        </ul>
        <p>Happy coding!</p>
        <p>The Coding Platform Team</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)

def send_contest_invitation(to_email: str, username: str, contest_title: str, contest_time: str, contest_url: str):
    """Gửi lời mời tham gia cuộc thi"""
    subject = f"You're invited to join: {contest_title}"
    html_content = f"""
    <html>
    <head></head>
    <body>
        <h1>Hi {username},</h1>
        <p>You're invited to participate in the upcoming contest: <strong>{contest_title}</strong></p>
        <p>The contest will start at: {contest_time}</p>
        <p>Don't miss this opportunity to challenge yourself and compete with other participants!</p>
        <p><a href="{contest_url}">Click here to view the contest details</a></p>
        <p>Good luck!</p>
        <p>The Coding Platform Team</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)

def send_submission_result(to_email: str, username: str, problem_title: str, status: str, score: Optional[int] = None):
    """Gửi kết quả bài nộp"""
    subject = f"Submission Result: {problem_title}"
    
    status_color = "green" if status == "accepted" else "red"
    
    html_content = f"""
    <html>
    <head></head>
    <body>
        <h1>Hi {username},</h1>
        <p>Your submission for the problem <strong>{problem_title}</strong> has been evaluated.</p>
        <p>Result: <span style="color: {status_color}; font-weight: bold;">{status.upper()}</span></p>
        {"<p>Score: " + str(score) + "</p>" if score is not None else ""}
        <p>You can check the details of your submission on the platform.</p>
        <p>Keep coding!</p>
        <p>The Coding Platform Team</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)