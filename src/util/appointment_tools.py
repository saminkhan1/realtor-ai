import logging
from typing import List, Dict, Optional, Any
from googleapiclient.errors import HttpError
from langchain_core.tools import tool

from src.util.state import State
from src.util.g_cal_functions import get_calendar_service


logger = logging.getLogger(__name__)

calendar_id = "saminkhann1@gmail.com"

@tool
def create_event(
    event_body: Dict[str, Any],
    conference_data_version: Optional[int] = None,
    max_attendees: Optional[int] = None,
    send_notifications: Optional[bool] = None,
    send_updates: Optional[str] = None,
    supports_attachments: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Creates an event in the specified calendar.

    Args:
        event_body (Dict[str, Any]): The request body containing event details.
        conference_data_version (Optional[int]): Version number of conference data supported by the API client.
        max_attendees (Optional[int]): The maximum number of attendees to include in the response.
        send_notifications (Optional[bool]): Deprecated. Please use send_updates instead.
        send_updates (Optional[str]): Whether to send notifications about the creation of the new event.
        supports_attachments (Optional[bool]): Whether API client performing operation supports event attachments.

    Returns:
        Dict[str, Any]: The created event.

    Raises:
        HttpError: If there's an error in the API request.
        ValueError: If required parameters are missing or invalid.
    """

    if not event_body:
        raise ValueError("event_body is required")

    try:
        request_params = {"calendarId": calendar_id, "body": event_body}
        if conference_data_version is not None:
            request_params["conferenceDataVersion"] = conference_data_version
        if max_attendees is not None:
            request_params["maxAttendees"] = max_attendees
        if send_notifications is not None:
            request_params["sendNotifications"] = send_notifications
        if send_updates is not None:
            request_params["sendUpdates"] = send_updates
        if supports_attachments is not None:
            request_params["supportsAttachments"] = supports_attachments
        
        service = get_calendar_service()
        event = service.events().insert(**request_params).execute()
        return f"Appointment created: {event}."
    except HttpError as error:
        logger.error(f"An error occurred while creating event: {error}")
        raise

@tool
def list_events(
    time_min: str,
    time_max: str,
    time_zone: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve events from a specific calendar within a given time range.

    Args:
        time_min (str): The start of the time range in RFC3339 format.
        time_max (str): The end of the time range in RFC3339 format.
        time_zone (Optional[str]): The time zone to use in the response. Defaults to 'UTC'.

    Returns:
        List[Dict[str, Any]]: A list of events within the specified time range.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        service = get_calendar_service()
        events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                timeZone=time_zone,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events.get("items", [])
    except HttpError as error:
        logger.error(f"An error occurred while retrieving events: {error}")
        raise

@tool
def delete_event(
    event_id: str,
    send_updates: str = "all"
) -> None:
    """
    Deletes an event from the specified calendar.

    Args:
        event_id (str): Event identifier.
        send_updates (str): Guests who should receive notifications about the deletion of the event.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        service = get_calendar_service()
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates=send_updates,
        ).execute()
        return "Appointment deleted."
    except HttpError as error:
        logger.error(f"An error occurred while deleting event: {error}")
        raise

appointment_tools = [
    create_event,
    list_events,
    delete_event
]