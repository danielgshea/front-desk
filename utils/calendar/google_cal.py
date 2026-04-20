"""Google Calendar API client for managing calendar events.

This module provides a clean interface to interact with the Google Calendar API,
handling authentication and common calendar operations.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarClient:
    """Client for interacting with Google Calendar API."""
    
    def __init__(self, credentials_path: Optional[Path] = None, token_path: Optional[Path] = None):
        """Initialize the Google Calendar client.
        
        Args:
            credentials_path: Path to credentials.json file. Defaults to project root.
            token_path: Path to token.json file. Defaults to project root.
        """
        project_root = Path(__file__).parent.parent.parent
        self.credentials_path = credentials_path or project_root / 'credentials.json'
        self.token_path = token_path or project_root / 'token.json'
        self._service = None
    
    def _get_credentials(self) -> Credentials:
        """Get valid credentials for Google Calendar API.
        
        Returns:
            Valid credentials object.
            
        Raises:
            FileNotFoundError: If credentials.json is not found.
        """
        creds = None
        
        # The token.json stores the user's access and refresh tokens
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {self.credentials_path}. "
                        "Please download it from Google Cloud Console and place it in the project root."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            self.token_path.write_text(creds.to_json())
        
        return creds
    
    @property
    def service(self):
        """Get or create the Calendar API service instance.
        
        Returns:
            Google Calendar API service instance.
        """
        if self._service is None:
            creds = self._get_credentials()
            self._service = build('calendar', 'v3', credentials=creds)
        return self._service
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all available Google calendars.
        
        Returns:
            List of calendar dictionaries containing id, summary, description, etc.
            
        Raises:
            HttpError: If the API request fails.
        """
        calendars_result = self.service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        calendar_list = []
        for calendar in calendars:
            calendar_list.append({
                'id': calendar['id'],
                'summary': calendar.get('summary', 'Unnamed Calendar'),
                'description': calendar.get('description', ''),
                'primary': calendar.get('primary', False),
                'timeZone': calendar.get('timeZone', '')
            })
        
        return calendar_list
    
    def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """List events from a Google Calendar.
        
        Args:
            calendar_id: The calendar ID (default: "primary" for main calendar)
            time_min: Start time in RFC3339 format (e.g., "2024-01-01T00:00:00Z")
                     If not specified, defaults to midnight today (UTC)
            time_max: End time in RFC3339 format (e.g., "2024-12-31T23:59:59Z")
            max_results: Maximum number of events to return (default: 10)
            
        Returns:
            List of event dictionaries containing id, summary, start, end, etc.
            
        Raises:
            HttpError: If the API request fails.
        """
        # If no time_min specified, use start of today (midnight UTC)
        # This ensures we get all of today's events, not just future ones
        if not time_min:
            now_utc = datetime.utcnow()
            start_of_today = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            time_min = start_of_today.isoformat() + 'Z'
        
        # Call the Calendar API
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            event_list.append({
                'id': event['id'],
                'summary': event.get('summary', 'Untitled Event'),
                'start': start,
                'end': end,
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'attendees': [att.get('email') for att in event.get('attendees', [])]
            })
        
        return event_list
    
    def list_events_from_all_calendars(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results_per_calendar: int = 10
    ) -> List[Dict[str, Any]]:
        """List events from all accessible calendars.
        
        Args:
            time_min: Start time in RFC3339 format (defaults to midnight today UTC)
            time_max: End time in RFC3339 format
            max_results_per_calendar: Max events per calendar (default: 10)
            
        Returns:
            Combined list of events from all calendars, sorted by start time.
            Each event includes a 'calendar' field with calendar details.
            
        Raises:
            HttpError: If any API request fails.
        """
        calendars = self.list_calendars()
        all_events = []
        
        for calendar in calendars:
            try:
                events = self.list_events(
                    calendar_id=calendar['id'],
                    time_min=time_min,
                    time_max=time_max,
                    max_results=max_results_per_calendar
                )
                
                # Add calendar info to each event
                for event in events:
                    event['calendar'] = {
                        'id': calendar['id'],
                        'summary': calendar['summary']
                    }
                    all_events.append(event)
                    
            except HttpError as e:
                # Skip calendars that error (e.g., permission issues)
                continue
        
        # Sort all events by start time
        all_events.sort(key=lambda x: x['start'])
        
        return all_events
    
    def list_events_from_calendars(
        self,
        calendar_ids: List[str],
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results_per_calendar: int = 10
    ) -> List[Dict[str, Any]]:
        """List events from specific calendars.
        
        Args:
            calendar_ids: List of calendar IDs to query
            time_min: Start time in RFC3339 format (defaults to midnight today UTC)
            time_max: End time in RFC3339 format
            max_results_per_calendar: Max events per calendar (default: 10)
            
        Returns:
            Combined list of events from specified calendars, sorted by start time.
            Each event includes a 'calendar' field with calendar ID.
            
        Raises:
            HttpError: If any API request fails.
        """
        all_events = []
        
        for calendar_id in calendar_ids:
            try:
                events = self.list_events(
                    calendar_id=calendar_id,
                    time_min=time_min,
                    time_max=time_max,
                    max_results=max_results_per_calendar
                )
                
                # Add calendar info to each event
                for event in events:
                    event['calendar'] = {'id': calendar_id}
                    all_events.append(event)
                    
            except HttpError as e:
                # Skip calendars that error
                continue
        
        # Sort all events by start time
        all_events.sort(key=lambda x: x['start'])
        
        return all_events
    
    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new event in Google Calendar.
        
        Args:
            summary: The title/summary of the event
            start_time: Start time in RFC3339 format (e.g., "2024-01-01T10:00:00Z")
            end_time: End time in RFC3339 format (e.g., "2024-01-01T11:00:00Z")
            calendar_id: The calendar ID (default: "primary")
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee email addresses
            
        Returns:
            Dictionary with created event details including event ID.
            
        Raises:
            HttpError: If the API request fails.
        """
        # Build event body
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Create the event
        created_event = self.service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()
        
        return {
            'id': created_event['id'],
            'summary': created_event.get('summary'),
            'start': created_event['start'].get('dateTime', created_event['start'].get('date')),
            'end': created_event['end'].get('dateTime', created_event['end'].get('date')),
            'htmlLink': created_event.get('htmlLink')
        }
    
    def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing event in Google Calendar.
        
        Args:
            event_id: The ID of the event to update
            calendar_id: The calendar ID (default: "primary")
            summary: New event title/summary
            start_time: New start time in RFC3339 format
            end_time: New end time in RFC3339 format
            description: New event description
            location: New event location
            
        Returns:
            Dictionary with updated event details.
            
        Raises:
            HttpError: If the API request fails.
        """
        # First, retrieve the existing event
        event = self.service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Update fields if provided
        if summary:
            event['summary'] = summary
        if start_time:
            event['start'] = {'dateTime': start_time}
        if end_time:
            event['end'] = {'dateTime': end_time}
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        # Update the event
        updated_event = self.service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        return {
            'id': updated_event['id'],
            'summary': updated_event.get('summary'),
            'start': updated_event['start'].get('dateTime', updated_event['start'].get('date')),
            'end': updated_event['end'].get('dateTime', updated_event['end'].get('date')),
            'htmlLink': updated_event.get('htmlLink')
        }
    
    def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        """Delete an event from Google Calendar.
        
        Args:
            event_id: The ID of the event to delete
            calendar_id: The calendar ID (default: "primary")
            
        Returns:
            True if deletion was successful.
            
        Raises:
            HttpError: If the API request fails.
        """
        self.service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        return True
