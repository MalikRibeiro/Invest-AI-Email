import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config.settings import Settings
import logging
import os
import markdown

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        pass

    def send_email(self, subject, body_markdown, attachment_path=None):
        if not Settings.EMAIL_SENDER or not Settings.EMAIL_PASSWORD:
            logger.warning("Email credentials not set. Skipping email.")
            return

        msg = MIMEMultipart()
        msg['From'] = Settings.EMAIL_SENDER
        msg['To'] = Settings.EMAIL_RECEIVER
        msg['Subject'] = subject

        # Convert Markdown to HTML
        html_content = markdown.markdown(body_markdown, extensions=['tables'])
        
        # Add some basic CSS for tables
        css = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            h1, h2 { color: #2c3e50; }
        </style>
        """
        
        full_html = f"<html><head>{css}</head><body>{html_content}</body></html>"

        msg.attach(MIMEText(full_html, 'html')) 

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

        try:
            # Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(Settings.EMAIL_SENDER, Settings.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def send_whatsapp(self, message):
        # Twilio Implementation
        if Settings.TWILIO_ACCOUNT_SID and Settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                client = Client(Settings.TWILIO_ACCOUNT_SID, Settings.TWILIO_AUTH_TOKEN)
                
                # Twilio WhatsApp usually requires "whatsapp:" prefix
                from_number = f"whatsapp:{Settings.TWILIO_FROM_NUMBER}" if not Settings.TWILIO_FROM_NUMBER.startswith("whatsapp:") else Settings.TWILIO_FROM_NUMBER
                to_number = f"whatsapp:{Settings.WHATSAPP_TO_NUMBER}" if not Settings.WHATSAPP_TO_NUMBER.startswith("whatsapp:") else Settings.WHATSAPP_TO_NUMBER
                
                # Split message if too long (Twilio limit is 1600 chars usually)
                if len(message) > 1600:
                    message = message[:1500] + "\n... (truncated)"
                
                msg = client.messages.create(
                    body=message,
                    from_=from_number,
                    to=to_number
                )
                logger.info(f"WhatsApp sent: {msg.sid}")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp via Twilio: {e}")
        else:
            logger.info("Twilio credentials not set. Skipping WhatsApp.")
