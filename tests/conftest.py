"""Pytest configuration and fixtures."""
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest


@pytest.fixture
def mock_credentials(tmp_path):
    """Create mock credentials for testing."""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    creds.refresh_token = "mock_refresh_token"
    creds.to_json.return_value = json.dumps({
        "token": "mock_token",
        "refresh_token": "mock_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "mock_client_id",
        "client_secret": "mock_client_secret",
        "scopes": ["https://www.googleapis.com/auth/calendar"]
    })
    return creds


@pytest.fixture
def mock_credentials_path(tmp_path):
    """Create a mock credentials.json file."""
    creds_file = tmp_path / "credentials.json"
    creds_data = {
        "installed": {
            "client_id": "mock_client_id",
            "project_id": "mock_project",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "mock_secret",
            "redirect_uris": ["http://localhost"]
        }
    }
    creds_file.write_text(json.dumps(creds_data))
    return creds_file


@pytest.fixture
def mock_token_path(tmp_path, mock_credentials):
    """Create a mock token.json file."""
    token_file = tmp_path / "token.json"
    token_file.write_text(mock_credentials.to_json())
    return token_file


@pytest.fixture
def mock_calendar_service():
    """Create a mock Google Calendar API service."""
    service = MagicMock()
    
    # Mock calendar list
    service.calendarList().list().execute.return_value = {
        'items': [
            {
                'id': 'primary',
                'summary': 'Test Calendar',
                'description': 'Test Description',
                'primary': True,
                'timeZone': 'America/New_York'
            },
            {
                'id': 'secondary@group.calendar.google.com',
                'summary': 'Secondary Calendar',
                'description': 'Another Calendar',
                'primary': False,
                'timeZone': 'America/Los_Angeles'
            }
        ]
    }
    
    # Mock events list
    service.events().list().execute.return_value = {
        'items': [
            {
                'id': 'event1',
                'summary': 'Test Event 1',
                'start': {'dateTime': '2024-01-01T10:00:00Z'},
                'end': {'dateTime': '2024-01-01T11:00:00Z'},
                'description': 'Test description',
                'location': 'Test location',
                'attendees': [{'email': 'test@example.com'}]
            },
            {
                'id': 'event2',
                'summary': 'Test Event 2',
                'start': {'dateTime': '2024-01-02T14:00:00Z'},
                'end': {'dateTime': '2024-01-02T15:00:00Z'},
                'description': '',
                'location': '',
                'attendees': []
            }
        ]
    }
    
    # Mock event creation
    def mock_insert(calendarId, body):
        result = MagicMock()
        result.execute.return_value = {
            'id': 'new_event_id',
            'summary': body.get('summary'),
            'start': body.get('start'),
            'end': body.get('end'),
            'description': body.get('description', ''),
            'location': body.get('location', ''),
            'htmlLink': 'https://calendar.google.com/event?eid=new_event_id'
        }
        return result
    
    service.events().insert = mock_insert
    
    # Mock event get
    service.events().get().execute.return_value = {
        'id': 'event1',
        'summary': 'Test Event 1',
        'start': {'dateTime': '2024-01-01T10:00:00Z'},
        'end': {'dateTime': '2024-01-01T11:00:00Z'},
        'description': 'Test description',
        'location': 'Test location'
    }
    
    # Mock event update
    def mock_update(calendarId, eventId, body):
        result = MagicMock()
        result.execute.return_value = {
            'id': eventId,
            'summary': body.get('summary'),
            'start': body.get('start'),
            'end': body.get('end'),
            'description': body.get('description', ''),
            'location': body.get('location', ''),
            'htmlLink': f'https://calendar.google.com/event?eid={eventId}'
        }
        return result
    
    service.events().update = mock_update
    
    # Mock event delete
    def mock_delete(calendarId, eventId):
        result = MagicMock()
        result.execute.return_value = None
        return result
    
    service.events().delete = mock_delete
    
    return service


@pytest.fixture
def sample_event():
    """Sample event data for testing."""
    return {
        'summary': 'Test Meeting',
        'start_time': '2024-01-15T10:00:00Z',
        'end_time': '2024-01-15T11:00:00Z',
        'description': 'Test meeting description',
        'location': 'Conference Room A',
        'attendees': ['attendee1@example.com', 'attendee2@example.com']
    }


@pytest.fixture
def sample_calendars():
    """Sample calendar data for testing."""
    return [
        {
            'id': 'primary',
            'summary': 'Primary Calendar',
            'description': 'Main calendar',
            'primary': True,
            'timeZone': 'America/New_York'
        },
        {
            'id': 'work@example.com',
            'summary': 'Work Calendar',
            'description': 'Work events',
            'primary': False,
            'timeZone': 'America/New_York'
        }
    ]


@pytest.fixture
def sample_events():
    """Sample events data for testing."""
    return [
        {
            'id': 'event1',
            'summary': 'Morning Meeting',
            'start': '2024-01-15T09:00:00Z',
            'end': '2024-01-15T10:00:00Z',
            'description': 'Daily standup',
            'location': 'Zoom',
            'attendees': ['team@example.com']
        },
        {
            'id': 'event2',
            'summary': 'Lunch Break',
            'start': '2024-01-15T12:00:00Z',
            'end': '2024-01-15T13:00:00Z',
            'description': '',
            'location': 'Cafeteria',
            'attendees': []
        }
    ]
