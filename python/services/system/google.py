import datetime
import uuid
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service_account.json'


def crear_reunion_con_meet(
    titulo,
    fecha,
    hora_inicio,
    hora_fin,
    invitados,
    creador_email
):

    if isinstance(fecha, str):
        fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()

    if isinstance(hora_inicio, str):
        hora_inicio = datetime.datetime.strptime(hora_inicio, "%H:%M").time()

    if isinstance(hora_fin, str):
        hora_fin = datetime.datetime.strptime(hora_fin, "%H:%M").time()

    start_datetime = datetime.datetime.combine(fecha, hora_inicio)
    end_datetime = datetime.datetime.combine(fecha, hora_fin)

    start_datetime = start_datetime.replace(tzinfo=datetime.timezone.utc)
    end_datetime = end_datetime.replace(tzinfo=datetime.timezone.utc)

    start_datetime = start_datetime + datetime.timedelta(hours=6)
    end_datetime = end_datetime + datetime.timedelta(hours=6)

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    delegated_credentials = credentials.with_subject(creador_email)

    service = build('calendar', 'v3', credentials=delegated_credentials)

    event_body = {
        'summary': titulo,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/Mexico_City'
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/Mexico_City'
        },
        'attendees': [{'email': email} for email in invitados],
        'conferenceData': {
            'createRequest': {
                'requestId': str(uuid.uuid4()),
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        },
    }

    event = service.events().insert(
        calendarId=creador_email,
        body=event_body,
        conferenceDataVersion=1,
        sendUpdates='all'
    ).execute()
    return event


def actualizar_fecha_reunion(
    google_event_id,
    nueva_fecha,
    nueva_hora_inicio,
    nueva_hora_fin,
    creador_email
):
    """
    Updates date and time of existing Google Meet event.
    """

    # 🔹 Convert strings if necessary
    if isinstance(nueva_fecha, str):
        nueva_fecha = datetime.datetime.strptime(nueva_fecha, "%Y-%m-%d").date()

    if isinstance(nueva_hora_inicio, str):
        nueva_hora_inicio = datetime.datetime.strptime(nueva_hora_inicio, "%H:%M").time()

    if isinstance(nueva_hora_fin, str):
        nueva_hora_fin = datetime.datetime.strptime(nueva_hora_fin, "%H:%M").time()

    start_datetime = datetime.datetime.combine(nueva_fecha, nueva_hora_inicio)
    end_datetime = datetime.datetime.combine(nueva_fecha, nueva_hora_fin)

    start_datetime = start_datetime.replace(tzinfo=datetime.timezone.utc)
    end_datetime = end_datetime.replace(tzinfo=datetime.timezone.utc)

    start_datetime = start_datetime + datetime.timedelta(hours=6)
    end_datetime = end_datetime + datetime.timedelta(hours=6)

    # 🔹 Authenticate
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    delegated_credentials = credentials.with_subject(creador_email)
    service = build('calendar', 'v3', credentials=delegated_credentials)

    # 🔹 Get existing event
    event = service.events().get(
        calendarId=creador_email,
        eventId=google_event_id
    ).execute()

    # 🔹 Modify date/time
    event['start'] = {
        'dateTime': start_datetime.isoformat(),
        'timeZone': 'America/Mexico_City'
    }

    event['end'] = {
        'dateTime': end_datetime.isoformat(),
        'timeZone': 'America/Mexico_City'
    }

    # 🔹 Update event
    updated_event = service.events().update(
        calendarId=creador_email,
        eventId=google_event_id,
        body=event,
        sendUpdates='all'
    ).execute()

    return updated_event

def cancelar_reunion_google(google_event_id, creador_email):
    """
    Cancels a Google Meet event and sends cancellation email to attendees.
    """

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    ).with_subject(creador_email)

    service = build('calendar', 'v3', credentials=credentials)

    service.events().delete(
        calendarId=creador_email,
        eventId=google_event_id,
        sendUpdates='all'
    ).execute()

    return True