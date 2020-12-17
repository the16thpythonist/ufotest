import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import click

from ufotest.config import Config
from ufotest.util import get_template
from ufotest.testing import TestReport
from ufotest.ci.build import BuildReport

CONFIG = Config()


def send_report_mail(receiver_email: str, receiver_name: str, build_report: BuildReport):
    message = MIMEMultipart('alternative')
    message['Subject'] = 'UfoTest Report'
    message['To'] = receiver_email

    context = {
        'name': receiver_name,
        'report': build_report,
        'config': CONFIG
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
    click.secho('(+) Sent report email to: {}'.format(receiver_email), fg='green')


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
