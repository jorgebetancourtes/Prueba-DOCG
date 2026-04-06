# python/services/send_email.py

import smtplib
from flask import render_template
import os

def send_html_email(subject, recipient_email, template, sender_name="RGV", **kwargs):
    EMAIL_USUARIO = os.getenv("EMAIL_USUARIO")
    EMAIL_CONTRASENA = os.getenv("EMAIL_CONTRASENA")
    try:
        # Conexión con el servidor SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()

            # Verificar si las variables de entorno están correctamente cargadas
            if not EMAIL_USUARIO or not EMAIL_CONTRASENA:
                raise Exception(
                    "Las credenciales de correo no están configuradas correctamente."
                )

            # Iniciar sesión en la cuenta de correo
            server.login(EMAIL_USUARIO, EMAIL_CONTRASENA)

            # Renderizar la plantilla HTML con los datos
            html_content = render_template(template, **kwargs)

            # Construir el mensaje de correo
            from_email = f"{sender_name} <{EMAIL_USUARIO}>"
            message = f"Subject: {subject}\nFrom: {from_email}\nTo: {recipient_email}\nContent-Type: text/html\n\n{html_content}".encode(
                "utf-8"
            )

            # Enviar el correo
            server.sendmail(EMAIL_USUARIO, recipient_email, message)

    except smtplib.SMTPException as smtp_error:
        # Capturar errores específicos de SMTP
        raise Exception(f"Error SMTP al enviar el correo: {smtp_error}")

    except Exception as e:
        # Capturar cualquier otro error
        raise Exception(f"Error general al enviar el correo: {e}")


def forgot_password_email(recipient_email,unique_code):
    try:
        # Enviar correo al cliente
        send_html_email(
            subject="Cambio de contraseña - Prueba DOCG",
            recipient_email=recipient_email,
            template="partials/system/email_template.html",
            body_content="Favor de ingresar al siguiente link para cambiar la contraseña.",
            details_list=[
                f"https://url_app/authentication/update_password/{unique_code}"
            ]
        )
    except Exception as e:
        raise Exception(f"Error al enviar correos: {e}")

def new_user_email(recipient_email,contrasena):
    try:
        # Enviar correo al cliente
        send_html_email(
            subject="Prueba DOCG",
            recipient_email=recipient_email,
            template="partials/system/email_template.html",
            body_content="Se acaba de crear tu usuario para la aplicación Prueba DOCG.",
            details_list=[
                "URL Plataforma: url_app",
                f"Correo electrónico: {recipient_email}",
                f"Contraseña: {contrasena}"
            ]
        )
    except Exception as e:
        raise Exception(f"Error al enviar correos: {e}")
    
def one_time_code_email(recipient_email,unique_code):
    try:
        # Enviar correo al cliente
        send_html_email(
            subject="Código de un solo uso para inicio de sesión - Prueba DOCG",
            recipient_email=recipient_email,
            template="partials/system/email_template.html",
            body_content="El siguiente código tiene una vigencia de 15 minutos para inciar sesión.",
            details_list=[
                f"{unique_code}"
            ]
        )
    except Exception as e:
        raise Exception(f"Error al enviar correos: {e}")
