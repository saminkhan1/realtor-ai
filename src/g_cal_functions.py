import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


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

        return build("calendar", "v3", credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Unexpected error creating Calendar service: {str(e)}")


def get_calendar_list(service: Any) -> List[Dict[str, Any]]:
    """
    Retrieve the list of calendars accessible by the user.

    Args:
        service (Any): Authorized Calendar API service instance.

    Returns:
        List[Dict[str, Any]]: List of calendars.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get("items", [])
    except HttpError as error:
        logger.error(f"An error occurred while retrieving calendar list: {error}")
        raise


def list_events(
    service: Any,
    calendar_id: str,
    time_min: str,
    time_max: str,
    time_zone: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve events from a specific calendar within a given time range.

    Args:
        service (Any): Authorized Calendar API service instance.
        calendar_id (str): The ID of the calendar to retrieve events from.
        time_min (str): The start of the time range in RFC3339 format.
        time_max (str): The end of the time range in RFC3339 format.
        time_zone (Optional[str]): The time zone to use in the response. Defaults to 'UTC'.

    Returns:
        List[Dict[str, Any]]: A list of events within the specified time range.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        events_result = (
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
        return events_result.get("items", [])
    except HttpError as error:
        logger.error(f"An error occurred while retrieving events: {error}")
        raise


def get_event(
    service: Any,
    calendar_id: str,
    event_id: str,
    max_attendees: Optional[int] = None,
    time_zone: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves an event from a Google Calendar based on its calendar ID and event ID.

    Args:
        service (Any): Authorized Calendar API service instance.
        calendar_id (str): Calendar identifier. Use "primary" for the primary calendar of the logged-in user.
        event_id (str): Event identifier.
        max_attendees (Optional[int]): The maximum number of attendees to include in the response.
        time_zone (Optional[str]): Time zone used in the response.

    Returns:
        Optional[Dict[str, Any]]: Event details or None if an error occurs.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        request_params = {
            "calendarId": calendar_id,
            "eventId": event_id,
        }
        if max_attendees is not None:
            request_params["maxAttendees"] = max_attendees
        if time_zone is not None:
            request_params["timeZone"] = time_zone

        return service.events().get(**request_params).execute()
    except HttpError as error:
        logger.error(f"An error occurred while retrieving event: {error}")
        raise


def create_event(
    service: Any,
    calendar_id: str,
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
        service (Any): The Google Calendar API service instance.
        calendar_id (str): Calendar identifier.
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

        event = service.events().insert(**request_params).execute()
        logger.info(f"Event created: {event['htmlLink']}")
        return event
    except HttpError as error:
        logger.error(f"An error occurred while creating event: {error}")
        raise


def update_event(
    service: Any,
    calendar_id: str,
    event_id: str,
    updated_event_data: Dict[str, Any],
    max_attendees: Optional[int] = None,
    time_zone: Optional[str] = None,
    conference_data_version: Optional[int] = None,
    send_updates: Optional[str] = None,
    supports_attachments: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Updates an event in a Google Calendar based on its calendar ID and event ID.

    Args:
        service (Any): Authorized Calendar API service instance.
        calendar_id (str): Calendar identifier.
        event_id (str): Event identifier.
        updated_event_data (Dict[str, Any]): Dictionary containing the updated event data.
        max_attendees (Optional[int]): The maximum number of attendees to include in the response.
        time_zone (Optional[str]): Time zone used in the response.
        conference_data_version (Optional[int]): Version number of conference data supported by the API client.
        send_updates (Optional[str]): Guests who should receive notifications about the update.
        supports_attachments (Optional[bool]): Whether API client performing operation supports event attachments.

    Returns:
        Dict[str, Any]: Updated event details.

    Raises:
        HttpError: If there's an error in the API request.
        ValueError: If required parameters are missing or invalid.
    """
    if not updated_event_data:
        raise ValueError("updated_event_data is required")

    try:
        event = get_event(
            service,
            calendar_id,
            event_id,
            max_attendees=max_attendees,
            time_zone=time_zone,
        )

        event.update(updated_event_data)

        return (
            service.events()
            .update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event,
                conferenceDataVersion=conference_data_version,
                sendUpdates=send_updates,
                supportsAttachments=supports_attachments,
            )
            .execute()
        )
    except HttpError as error:
        logger.error(f"An error occurred while updating event: {error}")
        raise


def delete_event(
    service: Any, calendar_id: str, event_id: str, send_updates: str = "all"
) -> None:
    """
    Deletes an event from the specified calendar.

    Args:
        service (Any): The Google Calendar API service instance.
        calendar_id (str): Calendar identifier.
        event_id (str): Event identifier.
        send_updates (str): Guests who should receive notifications about the deletion of the event.

    Raises:
        HttpError: If there's an error in the API request.
    """
    try:
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id,
            sendUpdates=send_updates,
        ).execute()
        logger.info(
            f"Event with ID '{event_id}' deleted successfully from calendar '{calendar_id}'."
        )
    except HttpError as error:
        logger.error(f"An error occurred while deleting event: {error}")
        raise


def get_freebusy_info(
    service: Any,
    calendar_ids: List[str],
    start_time: str,
    end_time: str,
    time_zone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns free/busy information for a set of calendars.

    Args:
        service (Any): Authorized Calendar API service instance.
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
        body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "timeZone": time_zone,
            "items": [{"id": calendar_id} for calendar_id in calendar_ids],
        }

        freebusy_result = service.freebusy().query(body=body).execute()
        return freebusy_result["calendars"]
    except HttpError as error:
        logger.error(f"An error occurred while checking availability: {error}")
        raise


def main() -> None:
    """Example usage of the Google Calendar functions."""
    try:
        service = get_calendar_service()

        # Get the list of calendars
        calendar_list = get_calendar_list(service)
        logger.info("Calendars:")
        for calendar in calendar_list:
            logger.info(f"- {calendar['summary']} (ID: {calendar['id']})")

        # Get events from the primary calendar
        calendar_id = "saminkhann1@gmail.com"
        time_min = datetime(2024, 7, 31).isoformat() + "Z"
        time_max = datetime(2024, 8, 2).isoformat() + "Z"
        events = list_events(service, calendar_id, time_min, time_max)
        logger.info("\nEvents on 7/31/2024-8/2/2024:")
        for event in events:
            start = event.get("start", {}).get("dateTime", "")
            end = event.get("end", {}).get("dateTime", "")
            summary = event.get("summary", "No title")
            logger.info(f"- {summary}: {start} to {end}")

        # Get a specific event
        if events:
            event_id = events[-1]["id"]
            event = get_event(service, calendar_id, event_id)
            logger.info(f"Specific event details: {event}")

        # Get free/busy information
        calendar_ids = [calendar_id]
        time_min = datetime(2024, 8, 1).isoformat() + "Z"
        time_max = (
            datetime(2024, 8, 1) + timedelta(days=1) - timedelta(seconds=1)
        ).isoformat() + "Z"
        freebusy_info = get_freebusy_info(
            service, calendar_ids, time_min, time_max, "America/New_York"
        )

        logger.info("\nFree/Busy information:")
        for calendar_id, calendar_info in freebusy_info.items():
            logger.info(f"Calendar ID: {calendar_id}")
            busy_times = calendar_info.get("busy", [])
            if not busy_times:
                logger.info(" - Free")
            else:
                for busy_time in busy_times:
                    start = busy_time["start"]
                    end = busy_time["end"]
                    logger.info(f" - Busy: {start} to {end}")

        # Create an event
        event_body = {
            "summary": "Test Event",
            "description": "This is the description test event",
            "start": {
                "dateTime": "2024-08-01T10:00:00",
                "timeZone": "America/New_York",
            },
            "end": {"dateTime": "2024-08-01T11:00:00", "timeZone": "America/New_York"},
            "reminders": {"useDefault": False},
        }
        new_event = create_event(service, "primary", event_body, send_updates="all")

        logger.info(f"New event created: {new_event}")

        # Update the created event
        updated_event_data = {
            "summary": "Updated Event Title",
            "description": "Updated description.",
        }

        updated_event = update_event(
            service,
            calendar_id,
            new_event["id"],
            updated_event_data,
            send_updates="all",
        )

        logger.info(f"Updated Event: {updated_event}")

        # Delete the created event
        delete_event(service, "primary", new_event["id"])
        logger.info("Event deleted successfully")

    except IOError as e:
        logger.error(f"IO Error: {str(e)}")
    except HttpError as e:
        logger.error(f"HTTP Error: {str(e)}")


if __name__ == "__main__":
    main()
