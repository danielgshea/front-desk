"""Tests for Google Calendar tools wrapper."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError

from admin_agent.utils.tools import (
    list_calendars,
    list_events,
    create_event,
    update_event,
    delete_event,
    get_calendar_client,
    CALENDAR_TOOLS
)


class TestCalendarTools:
    """Test suite for calendar tool wrappers."""
    
    def test_calendar_tools_exported(self):
        """Test that all tools are properly exported."""
        assert len(CALENDAR_TOOLS) == 7
        assert list_calendars in CALENDAR_TOOLS
        assert list_events in CALENDAR_TOOLS
        assert create_event in CALENDAR_TOOLS
        assert update_event in CALENDAR_TOOLS
        assert delete_event in CALENDAR_TOOLS
        # New multi-calendar tools
        from admin_agent.utils.tools import list_events_from_multiple_calendars, list_events_from_all_calendars
        assert list_events_from_multiple_calendars in CALENDAR_TOOLS
        assert list_events_from_all_calendars in CALENDAR_TOOLS
    
    @patch('admin_agent.utils.tools.GoogleCalendarClient')
    def test_get_calendar_client_singleton(self, mock_client_class):
        """Test that get_calendar_client returns singleton instance."""
        # Reset the global client
        import admin_agent.utils.tools as tools_module
        tools_module._calendar_client = None
        
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        
        client1 = get_calendar_client()
        client2 = get_calendar_client()
        
        assert client1 == client2
        assert mock_client_class.call_count == 1
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_calendars_success(self, mock_get_client, sample_calendars):
        """Test list_calendars tool with successful response."""
        mock_client = MagicMock()
        mock_client.list_calendars.return_value = sample_calendars
        mock_get_client.return_value = mock_client
        
        result = list_calendars.invoke({})
        
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]['id'] == 'primary'
        assert parsed[1]['id'] == 'work@example.com'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_calendars_empty(self, mock_get_client):
        """Test list_calendars when no calendars exist."""
        mock_client = MagicMock()
        mock_client.list_calendars.return_value = []
        mock_get_client.return_value = mock_client
        
        result = list_calendars.invoke({})
        
        parsed = json.loads(result)
        assert 'message' in parsed
        assert parsed['message'] == 'No calendars found.'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_calendars_http_error(self, mock_get_client):
        """Test list_calendars handles HttpError."""
        mock_client = MagicMock()
        mock_client.list_calendars.side_effect = HttpError(
            resp=Mock(status=403),
            content=b'Forbidden'
        )
        mock_get_client.return_value = mock_client
        
        result = list_calendars.invoke({})
        
        parsed = json.loads(result)
        assert 'error' in parsed
        assert 'An error occurred' in parsed['error']
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_calendars_generic_error(self, mock_get_client):
        """Test list_calendars handles generic exceptions."""
        mock_client = MagicMock()
        mock_client.list_calendars.side_effect = Exception('Network error')
        mock_get_client.return_value = mock_client
        
        result = list_calendars.invoke({})
        
        parsed = json.loads(result)
        assert 'error' in parsed
        assert 'Network error' in parsed['error']
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_events_success(self, mock_get_client, sample_events):
        """Test list_events tool with successful response."""
        mock_client = MagicMock()
        mock_client.list_events.return_value = sample_events
        mock_get_client.return_value = mock_client
        
        result = list_events.invoke({
            'calendar_id': 'primary',
            'time_min': '2024-01-15T00:00:00Z',
            'time_max': '2024-01-15T23:59:59Z',
            'max_results': 10
        })
        
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]['summary'] == 'Morning Meeting'
        assert parsed[1]['summary'] == 'Lunch Break'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_events_default_params(self, mock_get_client, sample_events):
        """Test list_events with default parameters."""
        mock_client = MagicMock()
        mock_client.list_events.return_value = sample_events
        mock_get_client.return_value = mock_client
        
        result = list_events.invoke({})
        
        parsed = json.loads(result)
        assert len(parsed) == 2
        
        # Verify default parameters were used
        mock_client.list_events.assert_called_once_with(
            calendar_id='primary',
            time_min=None,
            time_max=None,
            max_results=10
        )
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_list_events_empty(self, mock_get_client):
        """Test list_events when no events exist."""
        mock_client = MagicMock()
        mock_client.list_events.return_value = []
        mock_get_client.return_value = mock_client
        
        result = list_events.invoke({})
        
        parsed = json.loads(result)
        assert 'message' in parsed
        assert parsed['message'] == 'No upcoming events found.'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_create_event_success(self, mock_get_client, sample_event):
        """Test create_event tool with successful response."""
        mock_client = MagicMock()
        created_event = {
            'id': 'new_event_123',
            'summary': sample_event['summary'],
            'start': sample_event['start_time'],
            'end': sample_event['end_time'],
            'htmlLink': 'https://calendar.google.com/event?eid=new_event_123'
        }
        mock_client.create_event.return_value = created_event
        mock_get_client.return_value = mock_client
        
        result = create_event.invoke(sample_event)
        
        parsed = json.loads(result)
        assert parsed['id'] == 'new_event_123'
        assert parsed['summary'] == sample_event['summary']
        assert parsed['message'] == 'Event created successfully'
        assert 'htmlLink' in parsed
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_create_event_minimal(self, mock_get_client):
        """Test create_event with minimal required fields."""
        mock_client = MagicMock()
        created_event = {
            'id': 'simple_event',
            'summary': 'Simple Meeting',
            'start': '2024-01-20T10:00:00Z',
            'end': '2024-01-20T11:00:00Z',
            'htmlLink': 'https://calendar.google.com/event?eid=simple_event'
        }
        mock_client.create_event.return_value = created_event
        mock_get_client.return_value = mock_client
        
        result = create_event.invoke({
            'summary': 'Simple Meeting',
            'start_time': '2024-01-20T10:00:00Z',
            'end_time': '2024-01-20T11:00:00Z'
        })
        
        parsed = json.loads(result)
        assert parsed['id'] == 'simple_event'
        assert parsed['message'] == 'Event created successfully'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_create_event_with_attendees(self, mock_get_client):
        """Test create_event with attendees list."""
        mock_client = MagicMock()
        created_event = {
            'id': 'event_with_attendees',
            'summary': 'Team Meeting',
            'start': '2024-01-20T10:00:00Z',
            'end': '2024-01-20T11:00:00Z',
            'htmlLink': 'https://calendar.google.com/event?eid=event_with_attendees'
        }
        mock_client.create_event.return_value = created_event
        mock_get_client.return_value = mock_client
        
        result = create_event.invoke({
            'summary': 'Team Meeting',
            'start_time': '2024-01-20T10:00:00Z',
            'end_time': '2024-01-20T11:00:00Z',
            'attendees': ['user1@example.com', 'user2@example.com']
        })
        
        parsed = json.loads(result)
        assert parsed['id'] == 'event_with_attendees'
        
        # Verify attendees were passed to client
        call_kwargs = mock_client.create_event.call_args[1]
        assert call_kwargs['attendees'] == ['user1@example.com', 'user2@example.com']
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_update_event_success(self, mock_get_client):
        """Test update_event tool with successful response."""
        mock_client = MagicMock()
        updated_event = {
            'id': 'event1',
            'summary': 'Updated Meeting',
            'start': '2024-01-20T11:00:00Z',
            'end': '2024-01-20T12:00:00Z',
            'htmlLink': 'https://calendar.google.com/event?eid=event1'
        }
        mock_client.update_event.return_value = updated_event
        mock_get_client.return_value = mock_client
        
        result = update_event.invoke({
            'event_id': 'event1',
            'summary': 'Updated Meeting',
            'start_time': '2024-01-20T11:00:00Z'
        })
        
        parsed = json.loads(result)
        assert parsed['id'] == 'event1'
        assert parsed['summary'] == 'Updated Meeting'
        assert parsed['message'] == 'Event updated successfully'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_update_event_partial_update(self, mock_get_client):
        """Test update_event with partial field update."""
        mock_client = MagicMock()
        updated_event = {
            'id': 'event1',
            'summary': 'New Title',
            'start': '2024-01-20T10:00:00Z',
            'end': '2024-01-20T11:00:00Z',
            'htmlLink': 'https://calendar.google.com/event?eid=event1'
        }
        mock_client.update_event.return_value = updated_event
        mock_get_client.return_value = mock_client
        
        result = update_event.invoke({
            'event_id': 'event1',
            'summary': 'New Title'
        })
        
        parsed = json.loads(result)
        assert parsed['summary'] == 'New Title'
        
        # Verify only summary was passed
        call_kwargs = mock_client.update_event.call_args[1]
        assert call_kwargs['summary'] == 'New Title'
        assert call_kwargs.get('start_time') is None
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_delete_event_success(self, mock_get_client):
        """Test delete_event tool with successful response."""
        mock_client = MagicMock()
        mock_client.delete_event.return_value = True
        mock_get_client.return_value = mock_client
        
        result = delete_event.invoke({
            'event_id': 'event1',
            'calendar_id': 'primary'
        })
        
        parsed = json.loads(result)
        assert 'message' in parsed
        assert 'deleted successfully' in parsed['message']
        assert 'event1' in parsed['message']
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_delete_event_default_calendar(self, mock_get_client):
        """Test delete_event with default calendar_id."""
        mock_client = MagicMock()
        mock_client.delete_event.return_value = True
        mock_get_client.return_value = mock_client
        
        result = delete_event.invoke({'event_id': 'event1'})
        
        parsed = json.loads(result)
        assert 'message' in parsed
        
        # Verify default calendar_id was used
        call_kwargs = mock_client.delete_event.call_args[1]
        assert call_kwargs['calendar_id'] == 'primary'
    
    @patch('admin_agent.utils.tools.get_calendar_client')
    def test_tools_error_handling(self, mock_get_client):
        """Test that all tools properly handle exceptions."""
        mock_client = MagicMock()
        mock_client.list_events.side_effect = Exception('Test error')
        mock_client.create_event.side_effect = Exception('Test error')
        mock_client.update_event.side_effect = Exception('Test error')
        mock_client.delete_event.side_effect = Exception('Test error')
        mock_get_client.return_value = mock_client
        
        # Test each tool
        for tool_func in [list_events, create_event, update_event, delete_event]:
            result = tool_func.invoke({} if tool_func == list_events else {
                'event_id': 'test',
                'summary': 'Test',
                'start_time': '2024-01-01T10:00:00Z',
                'end_time': '2024-01-01T11:00:00Z'
            })
            
            parsed = json.loads(result)
            assert 'error' in parsed
            assert 'Test error' in parsed['error']
