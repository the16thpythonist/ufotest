import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ufotest.config import Config
from ufotest.util import get_template
from ufotest.testing import TestReport

CONFIG = Config()


def send_report_mail(receiver_email: str, receiver_name: str, test_report: TestReport):
    message = MIMEMultipart('alternative')
    message['Subject'] = 'UfoTest Report'
    message['To'] = receiver_email

    context = {
        'name': receiver_name,
        'report': test_report,
        'repository': CONFIG.get_ci_repository_url()
    }

    text_template = get_template('report_mail.text')
    text = text_template.render(context)
    text_mime = MIMEText(text, 'plain')
    message.attach(text_mime)

    html_template = get_template('report_mail.html')
    html = html_template.render(context)
    html_mime = MIMEText(html, 'html')
    message.attach(html_mime)

    send_mime_multipart(receiver_email, message)


def send_mime_multipart(receiver_email: str, message: MIMEMultipart):
    sender_email = CONFIG.get_email_address()
    sender_password = CONFIG.get_email_password()

    message['From'] = sender_email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(
            sender_email,
            receiver_email,
            message.as_string()
        )
