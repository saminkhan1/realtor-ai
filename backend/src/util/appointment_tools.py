from datetime import datetime
import os
import logging
from typing import List, Dict, Optional, Any
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from langchain_core.tools import tool
from twilio.rest import Client

from src.util.state import State

# from src.util.g_cal_functions import get_calendar_service

# account_sid = os.environ["TWILIO_ACCOUNT_SID"]
# auth_token = os.environ["TWILIO_AUTH_TOKEN"]
# # phone_number_from = os.environ["PHONE_NUMBER_FROM"]
# # phone_number_to = os.environ["PHONE_NUMBER_TO"]

# twilio_client = Client(account_sid, auth_token)
logger = logging.getLogger(__name__)

calendar_id = "saminkhann1@gmail.com"
# calendar_id = "lia.xin.weng@gmail.com"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = None


def get_calendar_service(credentials: Optional[Credentials] = None) -> Any:
    """
    Create and return a Google Calendar service object.

    Args:
        credentials (Optional[Credentials]): The credentials to use for authentication.

    Returns:
        Any: A Google Calendar service object.

    Raises:
        IOError: If there's an error reading or writing credential files.
        HttpError: If there's an error in the API request.
        RuntimeError: For other unexpected errors.
    """
    try:
        if not credentials:
            if os.path.exists("token.json"):
                try:
                    credentials = Credentials.from_authorized_user_file(
                        "token.json", SCOPES
                    )
                except IOError as e:
                    raise IOError(f"Error reading token file: {str(e)}")

            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                    except HttpError as e:
                        raise HttpError(f"Error refreshing credentials: {str(e)}")
                else:
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            "credentials.json", SCOPES
                        )
                        credentials = flow.run_local_server(port=8080)
                        with open("token.json", "w") as token_file:
                            token_file.write(credentials.to_json())
                    except IOError as e:
                        raise IOError(f"Error writing token file: {str(e)}")
                    except HttpError as e:
                        raise HttpError(f"Error in authorization flow: {str(e)}")

        service = build("calendar", "v3", credentials=credentials)

        global TIMEZONE
        TIMEZONE = get_user_timezone(service)

        return service
    except Exception as e:
        raise RuntimeError(f"Unexpected error creating Calendar service: {str(e)}")


def get_user_timezone(service):
    try:
        timezone_setting = service.settings().get(setting="timezone").execute()
        print(f"user's timezone: {timezone_setting.get('value')}")
        return timezone_setting.get("value")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


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
    Creates/adds an event.

    Args:
        event_body (Dict[str, Any]): The request body containing event details. Include important information such as user's time zone apartment address, appointment location, attendees.
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

    global TIMEZONE

    if not event_body:
        raise ValueError("event_body is required")

    if "attendees" not in event_body or not event_body["attendees"]:
        raise ValueError("At least one attendee with an email is required")

    try:
        service = get_calendar_service()

        if TIMEZONE:
            event_body["start"]["timeZone"] = TIMEZONE
            event_body["end"]["timeZone"] = TIMEZONE

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

        
        event = service.events().insert(**request_params).execute()
        return f"Appointment created: {event}."
    except HttpError as error:
        logger.error(f"An error occurred while creating event: {error}")
        raise


@tool
def list_events(
    time_min: str,
    time_max: str,
) -> List[Dict[str, Any]]:
    """
    Retrieve events within a given time range.

    Args:
        time_min (str): The start of the time range in RFC3339 format.
        time_max (str): The end of the time range in RFC3339 format.

    Returns:
        List[Dict[str, Any]]: A list of events within the specified time range.

    Raises:
        HttpError: If there's an error in the API request.
    """
    global TIMEZONE

    try:
        service = get_calendar_service()
        events = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                timeZone=TIMEZONE,
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
def delete_event(event_id: str, send_updates: str = "all") -> None:
    """
    Deletes an event.

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


def get_event(
    event_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves an event based on its event ID.

    Args:
        event_id (str): Event identifier.

    Returns:
        Optional[Dict[str, Any]]: Event details or None if an error occurs.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        service = get_calendar_service()
        request_params = {
            "calendarId": calendar_id,
            "eventId": event_id,
        }

        return service.events().get(**request_params).execute()
    except HttpError as error:
        logger.error(f"An error occurred while retrieving event: {error}")
        raise


@tool
def update_event(
    event_id: str,
    updated_event_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Updates information of an existing event.

    Args:
        event_id (str): Event identifier.
        updated_event_data (Dict[str, Any]): Dictionary containing the updated event data.

    Returns:
        Dict[str, Any]: Updated event details.

    Raises:
        HttpError: If there's an error in the API request.
        ValueError: If required parameters are missing or invalid.
    """
    if not updated_event_data:
        raise ValueError("updated_event_data is required")

    try:
        service = get_calendar_service()
        event = get_event(event_id)

        event.update(updated_event_data)
        updated_event = (
            service.events()
            .update(calendarId=calendar_id, eventId=event_id, body=event)
            .execute()
        )

        return f"Appointment updated: {updated_event}"
    except HttpError as error:
        logger.error(f"An error occurred while updating event: {error}")
        raise


@tool
def send_confirmation(confirmation: str) -> str:
    """
    Send confirmation text to the user regarding their appointment.

    Args:
        confirmation (str): Details about the appointment.

    Returns:
        str: Message indicating that the confirmation text was sent successfully.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        # twilio_client.messages.create(
        #     body=confirmation,
        #     from_=phone_number_from,
        #     to=phone_number_to,
        # )
        print(confirmation)
    except HttpError as error:
        logger.error(f"An error occurred while sending confirmation text: {error}")
        raise


@tool
def get_calendar_list() -> List[Dict[str, Any]]:
    """
    Retrieve the list of calendars accessible by the user.

    Returns:
        List[Dict[str, Any]]: List of calendars.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        service = get_calendar_service()
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get("items", [])
    except HttpError as error:
        logger.error(f"An error occurred while retrieving calendar list: {error}")
        raise


@tool
def get_freebusy_info(
    calendar_ids: List[str],
    start_time: str,
    end_time: str,
    time_zone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns free/busy information for a set of calendars.

    Args:
        calendar_ids (List[str]): A list of calendar IDs to check.
        start_time (str): Start time of the period to check (RFC3339 timestamp).
        end_time (str): End time of the period to check (RFC3339 timestamp).
        time_zone (Optional[str]): Time zone used in the response. Optional. The default is UTC

    Returns:
        Dict[str, Any]: Free/busy information for the specified calendars.

    Raises:
        HttpError: If there's an error in the API request.
        ValueError: If required parameters are missing or invalid.
    """
    if not calendar_ids:
        raise ValueError("calendar_ids list is required and cannot be empty")

    if not start_time or not end_time:
        raise ValueError("start_time and end_time are required")

    try:
        service = get_calendar_service()
        body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "timeZone": time_zone or TIMEZONE,
            "items": [{"id": calendar_id} for calendar_id in calendar_ids],
        }

        freebusy_result = service.freebusy().query(body=body).execute()
        return freebusy_result["calendars"]
    except HttpError as error:
        logger.error(f"An error occurred while checking availability: {error}")
        raise

@tool
def is_available_for_meeting(
    service: Any,
    calendar_id: str,
    start_time: datetime,
    end_time: datetime,
    time_zone: str = "America/New_York"
) -> bool:
    """
    Checks if the user is available for a meeting within the given time range.

    Args:
        service (Any): Authorized Calendar API service instance.
        calendar_id (str): The ID of the calendar to check.
        start_time (datetime): The start time of the proposed meeting.
        end_time (datetime): The end time of the proposed meeting.
        time_zone (str): The time zone to use. Defaults to "America/New_York".

    Returns:
        bool: True if the user is available, False otherwise.
    """
    # Convert datetime objects to RFC3339 format
    time_min = start_time.isoformat()
    time_max = end_time.isoformat()

    # Get free/busy information
    freebusy_info = get_freebusy_info(
        service, [calendar_id], time_min, time_max, time_zone
    )

    # Check for conflicts
    for calendar_id, calendar_info in freebusy_info.items():
        busy_times = calendar_info.get("busy", [])
        for busy_period in busy_times:
            busy_start = datetime.fromisoformat(busy_period["start"].replace("Z", "+00:00"))
            busy_end = datetime.fromisoformat(busy_period["end"].replace("Z", "+00:00"))
            
            if (start_time < busy_end) and (end_time > busy_start):
                return False  # There is a conflict, so not available

    return True  # No conflicts found, so available

safe_tools = [
    list_events,
    send_confirmation,
    get_calendar_list,
    get_freebusy_info,
    is_available_for_meeting,
]

sensitive_tools = [
    create_event,
    delete_event,
    update_event,
]

sensitive_tool_names = {t.name for t in sensitive_tools}