import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from dotenv import load_dotenv
import logging

load_dotenv()

SENDER_EMAIL = os.getenv("sender_email")
SENDER_PASSWORD = os.getenv("password")  # пароль приложения

if not SENDER_EMAIL or not SENDER_PASSWORD:
    raise ValueError("Не заданы переменные sender_email или password")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def send_email(recipient_emails, code, expire_minutes):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = ", ".join(recipient_emails)
    message["Subject"] = "Код проверки"

    email_body = await generate_verification_email_html( code=code, expire_minutes=expire_minutes)
    message.attach(MIMEText(email_body, "html"))

    try:
        logging.info(f"Начинаем отправку письма на: {recipient_emails}")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            result = server.sendmail(SENDER_EMAIL, recipient_emails, message.as_string())
            if result:
                logging.warning(f"Проблемы с доставкой на адреса: {result}")
            else:
                logging.info("Письмо успешно отправлено!")
        return f"Письмо успешно отправлено, проверьте почту {recipient_emails}"
    except smtplib.SMTPAuthenticationError:
        logging.error("Ошибка аутентификации: проверь пароль приложения")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP ошибка: {e}")
    except Exception as e:
        logging.error(f"Ошибка при отправке: {e}")

async def generate_verification_email_html(code: int, expire_minutes: int) -> str:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f7;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                padding: 30px;
                text-align: center;
            }}
            h1 {{
                color: #333333;
            }}
            .code-box {{
                display: inline-block;
                padding: 15px 25px;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 4px;
                background-color: #f0f0f0;
                border-radius: 8px;
                margin: 20px 0;
                user-select: all;
                cursor: pointer;
            }}
            p {{
                color: #555555;
                font-size: 16px;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #888888;
            }}
            .button {{
                display: inline-block;
                padding: 12px 20px;
                margin-top: 20px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Привет!</h1>
            <p>Используй этот код для подтверждения действия. Срок действия кода: {expire_minutes} минут.</p>
            <div class="code-box" title="Нажми и скопируй код">{code}</div>
            <p>Выдели код и скопируй его для использования.</p>
            <div class="footer">
                Если вы не запрашивали этот код, просто проигнорируйте письмо.
            </div>
        </div>
    </body>
    </html>
    """
    return html


#
# async def main():
#     await send_email(
#         recipient_emails=["savvin.nikita.work@yandex.ru"],
#         code=4444,
#         expire_minutes=10
#     )
#
# asyncio.run(main())
