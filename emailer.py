import smtplib, ssl
from email.message import EmailMessage
from email.utils import make_msgid
import mimetypes
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

    def send_mail(self, receiver, subject, text, image=None):
        context = ssl.create_default_context()
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = receiver
        message.set_content(text)

        text = text.replace('\n', '<br />')

        if (not image is None):
            image_cid = make_msgid(domain='xyz.com')
            message.add_alternative("""\
            <html>
                <body>
                    <p>
                    {text}
                    </p>
                    <img src="cid:{image_cid}">
                </body>
            </html>
            """.format(text=text, image_cid=image_cid[1:-1]), subtype='html')
            with open('./data/output.png', 'rb') as img:
                maintype, subtype = mimetypes.guess_type(img.name)[0].split('/')
                message.get_payload()[1].add_related(img.read(), maintype=maintype, subtype=subtype, cid=image_cid)

        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.starttls(context=context)
            server.login(self.sender_email, self.password)
            #server.sendmail(self.sender_email, receiver, message.as_string())
            server.send_message(message)
            server.quit()