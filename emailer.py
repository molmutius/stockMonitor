import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

class Emailer:
    """
    This class is able to send emails via a predefined smtp server
    """

    def __init__(self):
        self.port = 587
        self.smtp_server = config.email_smtp_server
        self.sender_email = config.email_sender
        self.password = config.email_password

    def send_mail(self, receiver, subject, text):
        context = ssl.create_default_context()
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = receiver
        text_multipart = MIMEText(text, "plain")
        message.attach(text_multipart)
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.starttls(context=context)
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, receiver, message.as_string())