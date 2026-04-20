"""Tests for Google Calendar client."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError

from utils.calendar.google_cal import GoogleCalendarClient


class TestGoogleCalendarClient:
    """Test suite for GoogleCalendarClient."""
    
    def test_init_default_paths(self):
        """Test initialization with default paths."""
        client = GoogleCalendarClient()
        assert client.credentials_path.name == 'credentials.json'
        assert client.token_path.name == 'token.json'
        assert client._service is None
    
    def test_init_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        creds_path = tmp_path / "custom_creds.json"
        token_path = tmp_path / "custom_token.json"
        
        client = GoogleCalendarClient(
            credentials_path=creds_path,
            token_path=token_path
        )
        
        assert client.credentials_path == creds_path
        assert client.token_path == token_path
    
    @patch('utils.calendar.google_cal.Credentials')
    @patch('utils.calendar.google_cal.build')
    def test_get_credentials_from_token(
        self, mock_build, mock_creds_class, tmp_path, mock_token_path, mock_credentials
    ):
        """Test getting credentials from existing token file."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        creds = client._get_credentials()
        
        assert creds == mock_credentials
        mock_creds_class.from_authorized_user_file.assert_called_once()
    
    @patch('utils.calendar.google_cal.Credentials')
    def test_get_credentials_no_file_raises_error(self, mock_creds_class, tmp_path):
        """Test that missing credentials file raises FileNotFoundError."""
        mock_creds_class.from_authorized_user_file.return_value = None
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "nonexistent.json",
            token_path=tmp_path / "nonexistent_token.json"
        )
        
        with pytest.raises(FileNotFoundError) as exc_info:
            client._get_credentials()
        
        assert "credentials.json not found" in str(exc_info.value)
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_service_property(
        self, mock_creds_class, mock_build, tmp_path, mock_token_path, mock_credentials
    ):
        """Test service property creates and caches service instance."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        # First access
        service1 = client.service
        assert service1 == mock_service
        
        # Second access should return cached instance
        service2 = client.service
        assert service2 == mock_service
        
        # Build should only be called once
        assert mock_build.call_count == 1
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_list_calendars_success(
        self, mock_creds_class, mock_build, 
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test successfully listing calendars."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        calendars = client.list_calendars()
        
        assert len(calendars) == 2
        assert calendars[0]['id'] == 'primary'
        assert calendars[0]['summary'] == 'Test Calendar'
        assert calendars[0]['primary'] is True
        assert calendars[1]['id'] == 'secondary@group.calendar.google.com'
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_list_calendars_empty(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials
    ):
        """Test listing calendars when none exist."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_service = MagicMock()
        mock_service.calendarList().list().execute.return_value = {'items': []}
        mock_build.return_value = mock_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        calendars = client.list_calendars()
        
        assert len(calendars) == 0
        assert calendars == []
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_list_events_success(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test successfully listing events."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        events = client.list_events(
            calendar_id='primary',
            time_min='2024-01-01T00:00:00Z',
            time_max='2024-12-31T23:59:59Z',
            max_results=10
        )
        
        assert len(events) == 2
        assert events[0]['id'] == 'event1'
        assert events[0]['summary'] == 'Test Event 1'
        assert events[0]['location'] == 'Test location'
        assert 'test@example.com' in events[0]['attendees']
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    @patch('utils.calendar.google_cal.datetime')
    def test_list_events_default_time_min(
        self, mock_datetime, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test list_events uses current time when time_min not provided."""
        mock_now = MagicMock()
        mock_now.isoformat.return_value = '2024-01-15T12:00:00'
        mock_datetime.utcnow.return_value = mock_now
        
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        events = client.list_events()
        
        # Verify that datetime.utcnow was called
        mock_datetime.utcnow.assert_called_once()
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_create_event_success(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test successfully creating an event."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        event = client.create_event(
            summary='New Meeting',
            start_time='2024-01-20T10:00:00Z',
            end_time='2024-01-20T11:00:00Z',
            description='Important meeting',
            location='Room 101',
            attendees=['user@example.com']
        )
        
        assert event['id'] == 'new_event_id'
        assert event['summary'] == 'New Meeting'
        assert 'htmlLink' in event
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_create_event_minimal_args(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test creating event with only required arguments."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        event = client.create_event(
            summary='Simple Meeting',
            start_time='2024-01-20T10:00:00Z',
            end_time='2024-01-20T11:00:00Z'
        )
        
        assert event['id'] == 'new_event_id'
        assert event['summary'] == 'Simple Meeting'
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_update_event_success(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test successfully updating an event."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        event = client.update_event(
            event_id='event1',
            summary='Updated Meeting',
            location='New Location'
        )
        
        assert event['id'] == 'event1'
        assert event['summary'] == 'Updated Meeting'
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_update_event_partial(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test updating only some event fields."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        # Update only summary
        event = client.update_event(
            event_id='event1',
            summary='New Title Only'
        )
        
        assert event['id'] == 'event1'
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_delete_event_success(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials, mock_calendar_service
    ):
        """Test successfully deleting an event."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_build.return_value = mock_calendar_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        result = client.delete_event(event_id='event1')
        
        assert result is True
    
    @patch('utils.calendar.google_cal.build')
    @patch('utils.calendar.google_cal.Credentials')
    def test_http_error_handling(
        self, mock_creds_class, mock_build,
        tmp_path, mock_token_path, mock_credentials
    ):
        """Test that HttpError is properly raised."""
        mock_creds_class.from_authorized_user_file.return_value = mock_credentials
        mock_service = MagicMock()
        
        # Mock an HTTP error
        mock_service.events().list().execute.side_effect = HttpError(
            resp=Mock(status=404),
            content=b'Not Found'
        )
        mock_build.return_value = mock_service
        
        client = GoogleCalendarClient(
            credentials_path=tmp_path / "credentials.json",
            token_path=mock_token_path
        )
        
        with pytest.raises(HttpError):
            client.list_events()
