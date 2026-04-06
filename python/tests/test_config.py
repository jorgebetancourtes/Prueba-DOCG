# python/tests/test_config.py

from python.services.system.email import send_html_email

# variables de configuración
SYSTEM_NAME = "Prueba DOCG"
EMAIL_RECIPIENTS = ["david.contreras@rgvsoluciones.com"]
SENDER_NAME = "Test Runner"


def print_separator():
    """Imprime un separador decorativo."""
    print("\n" + "=" * 40)


def print_result(test_name, passed, message=None):
    """Imprime el resultado de una prueba."""
    status = "✔" if passed else "✘"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status} {test_name}{reset}")
    if message and not passed:
        print(f"   ↳ {message}")


def run_all_tests(tests):
    """Ejecuta todos los tests y devuelve los errores."""
    errors = []

    print_separator()
    print("Ejecutando pruebas...\n")

    for test in tests:
        try:
            test()
            print_result(test.__name__, True)
        except AssertionError as e:
            errors.append(f"{test.__name__}: {e}")
            print_result(test.__name__, False, str(e))

    print_separator()

    if errors:
        send_test_failure_email(errors)

    return errors


def send_test_failure_email(errors):
    """Envía un correo con el resumen de los tests fallidos."""
    try:
        subject = f"⚠️ {SYSTEM_NAME}: fallos en pruebas automatizadas"
        template = "partials/system/test_failure_email.html"

        body_content = (
            f"Se encontraron fallos en las pruebas automatizadas del sistema {SYSTEM_NAME}. "
            "A continuación se presenta el resumen:"
        )
        details_list = [f"↳ {error}" for error in errors]

        # Enviar un correo a cada destinatario
        for recipient in EMAIL_RECIPIENTS:
            send_html_email(
                subject=subject,
                recipient_email=recipient,
                template=template,
                sender_name=SENDER_NAME,
                system_name=SYSTEM_NAME,
                body_content=body_content,
                details_list=details_list,
            )
        print("\033[94mNotificación por correo enviada exitosamente.\033[0m")  # Azul
    except Exception as e:
        print(f"\033[91mError al enviar la notificación por correo: {e}\033[0m")
