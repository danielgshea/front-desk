"""
Integration tests for Google Calendar API using real credentials.

These tests require:
1. credentials.json in the project root
2. Successful OAuth authentication (will prompt on first run)
3. Active internet connection

Run with: pytest tests/test_integration_live.py -v -s

Note: Add @pytest.mark.skip() decorator to skip these tests in CI/CD
"""
import pytest
from datetime import datetime, timedelta
from utils.calendar import GoogleCalendarClient


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def live_client():
    """Create a real GoogleCalendarClient instance.
    
    This will trigger OAuth flow on first run if token.json doesn't exist.
    """
    try:
        client = GoogleCalendarClient()
        return client
    except FileNotFoundError as e:
        pytest.skip(f"Credentials not found: {e}")
    except Exception as e:
        pytest.skip(f"Could not create client: {e}")


class TestLiveCalendarIntegration:
    """Integration tests using real Google Calendar API."""
    
    def test_list_calendars(self, live_client):
        """Test listing real calendars from the authenticated account."""
        calendars = live_client.list_calendars()
        
        # Should have at least the primary calendar
        assert len(calendars) > 0
        
        # Should have a primary calendar
        primary_cals = [cal for cal in calendars if cal.get('primary')]
        assert len(primary_cals) == 1
        
        # Print calendars for visibility
        print("\n=== Available Calendars ===")
        for cal in calendars:
            primary_marker = " (PRIMARY)" if cal.get('primary') else ""
            print(f"  - {cal['summary']}{primary_marker}")
            print(f"    ID: {cal['id']}")
    
    def test_list_upcoming_events(self, live_client):
        """Test listing upcoming events from primary calendar."""
        # Get events from now onwards
        now = datetime.utcnow().isoformat() + 'Z'
        
        events = live_client.list_events(
            calendar_id='primary',
            time_min=now,
            max_results=5
        )
        
        # Print events (may be empty if no upcoming events)
        print(f"\n=== Upcoming Events (max 5) ===")
        if events:
            for event in events:
                print(f"  - {event['summary']}")
                print(f"    Start: {event['start']}")
                print(f"    End: {event['end']}")
        else:
            print("  No upcoming events found")
        
        # Just verify the structure, don't assert on count since it may be empty
        assert isinstance(events, list)
    
    def test_create_and_delete_event(self, live_client):
        """Test creating and then deleting an event."""
        # Create event for tomorrow at 10 AM
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        # Create the event
        event = live_client.create_event(
            summary='[TEST] Integration Test Event',
            start_time=start_time.isoformat() + 'Z',
            end_time=end_time.isoformat() + 'Z',
            description='This is a test event created by integration tests. It will be deleted automatically.',
            location='Test Location'
        )
        
        print(f"\n=== Created Test Event ===")
        print(f"  ID: {event['id']}")
        print(f"  Summary: {event['summary']}")
        print(f"  Link: {event.get('htmlLink', 'N/A')}")
        
        # Verify event was created
        assert event['id'] is not None
        assert event['summary'] == '[TEST] Integration Test Event'
        
        # Clean up - delete the event
        result = live_client.delete_event(event_id=event['id'])
        assert result is True
        
        print(f"  ✓ Event deleted successfully")
    
    def test_create_update_and_delete_event(self, live_client):
        """Test full CRUD cycle: create, update, and delete an event."""
        # Create event
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        event = live_client.create_event(
            summary='[TEST] Event to Update',
            start_time=start_time.isoformat() + 'Z',
            end_time=end_time.isoformat() + 'Z',
            description='Original description'
        )
        
        event_id = event['id']
        print(f"\n=== CRUD Test ===")
        print(f"  Created event: {event['summary']}")
        
        # Update the event
        updated_event = live_client.update_event(
            event_id=event_id,
            summary='[TEST] Updated Event Title',
            description='Updated description',
            location='Updated Location'
        )
        
        print(f"  Updated event: {updated_event['summary']}")
        assert updated_event['summary'] == '[TEST] Updated Event Title'
        
        # Delete the event
        result = live_client.delete_event(event_id=event_id)
        assert result is True
        print(f"  ✓ Event deleted successfully")
    
    def test_create_event_with_attendees(self, live_client):
        """Test creating an event with attendees."""
        tomorrow = datetime.utcnow() + timedelta(days=2)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=30)
        
        # Note: Using test email addresses - they won't actually receive invites
        # unless you use real email addresses
        event = live_client.create_event(
            summary='[TEST] Meeting with Attendees',
            start_time=start_time.isoformat() + 'Z',
            end_time=end_time.isoformat() + 'Z',
            description='Test meeting',
            attendees=['test@example.com']  # Use your own email to test notifications
        )
        
        print(f"\n=== Event with Attendees ===")
        print(f"  Created: {event['summary']}")
        print(f"  Event ID: {event['id']}")
        
        assert event['id'] is not None
        
        # Clean up
        live_client.delete_event(event_id=event['id'])
        print(f"  ✓ Event deleted")
    
    def test_list_events_date_range(self, live_client):
        """Test listing events within a specific date range."""
        # Get events from last week to next week
        last_week = datetime.utcnow() - timedelta(days=7)
        next_week = datetime.utcnow() + timedelta(days=7)
        
        events = live_client.list_events(
            calendar_id='primary',
            time_min=last_week.isoformat() + 'Z',
            time_max=next_week.isoformat() + 'Z',
            max_results=20
        )
        
        print(f"\n=== Events in Date Range ===")
        print(f"  From: {last_week.date()}")
        print(f"  To: {next_week.date()}")
        print(f"  Found: {len(events)} event(s)")
        
        assert isinstance(events, list)
        
        if events:
            for event in events[:3]:  # Show first 3
                print(f"    - {event['summary']} ({event['start']})")


class TestLiveToolsIntegration:
    """Integration tests for LangChain tool wrappers."""
    
    def test_list_calendars_tool(self, live_client):
        """Test the list_calendars tool with real data."""
        from admin_agent.utils.tools import list_calendars
        import json
        
        result = list_calendars.invoke({})
        
        # Parse JSON result
        data = json.loads(result)
        
        print(f"\n=== list_calendars Tool ===")
        if isinstance(data, list):
            print(f"  Found {len(data)} calendar(s)")
            assert len(data) > 0
        else:
            print(f"  Result: {data}")
    
    def test_list_events_tool(self, live_client):
        """Test the list_events tool with real data."""
        from admin_agent.utils.tools import list_events
        import json
        
        result = list_events.invoke({
            'calendar_id': 'primary',
            'max_results': 5
        })
        
        data = json.loads(result)
        
        print(f"\n=== list_events Tool ===")
        if isinstance(data, list):
            print(f"  Found {len(data)} event(s)")
        elif 'message' in data:
            print(f"  {data['message']}")
        elif 'error' in data:
            print(f"  Error: {data['error']}")
            pytest.fail("Tool returned error")
    
    def test_create_delete_event_tools(self, live_client):
        """Test create and delete event tools."""
        from admin_agent.utils.tools import create_event, delete_event
        import json
        
        # Create event
        tomorrow = datetime.utcnow() + timedelta(days=1)
        start_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        create_result = create_event.invoke({
            'summary': '[TEST] Tool Test Event',
            'start_time': start_time.isoformat() + 'Z',
            'end_time': end_time.isoformat() + 'Z',
            'description': 'Created by tool test'
        })
        
        create_data = json.loads(create_result)
        
        print(f"\n=== Tool Test ===")
        print(f"  Created: {create_data.get('summary', 'N/A')}")
        
        assert 'id' in create_data
        assert create_data['message'] == 'Event created successfully'
        
        event_id = create_data['id']
        
        # Delete event
        delete_result = delete_event.invoke({
            'event_id': event_id
        })
        
        delete_data = json.loads(delete_result)
        print(f"  {delete_data['message']}")
        
        assert 'deleted successfully' in delete_data['message']
