import asyncio
import logging
from app.clients import mixpanel_client
from app.helpers import retry_with_backoff

logger = logging.getLogger(__name__)


def track_event(distinct_id: str, event_name: str, properties: dict = None):
    """
    Internal helper to send an event to Mixpanel with the 'mcp:' prefix.

    :param distinct_id: Unique user identifier.
    :param event_name: Event name (without the 'mcp:' prefix).
    :param properties: Optional dictionary of event properties.
    """

    full_event_name = f"mcp:{event_name}"
    # Log if any property field is a list with more than 50 items
    # List elements should not exceed 8KB: https://docs.mixpanel.com/docs/data-structure/property-reference/data-type
    if any(isinstance(value, list) and len(value) > 50 for value in properties.values()):
        logger.warning(
            f"Event {full_event_name} for distinct_id {distinct_id} has properties with a list longer than 50 items. Properties: {properties}"
        )
    mixpanel_client.track(distinct_id, full_event_name, properties or {})


def mixpanel_event_tracking(distinct_id: str, event_name: str, properties: dict):
    """
    Track a Mixpanel event for MCP Server with retry/backoff logic.
    
    :param distinct_id: Unique user identifier.
    :param event_name: Event name (without the 'mcp:' prefix).
    :param properties: Optional dictionary of event properties.

    Source: https://developer.mixpanel.com/reference/import-events
    From Mixpanel: "When you see 429s, employ an exponential backoff with jitter strategy. 
    We recommend starting with a backoff of 2s and doubling backoff until 60s, with 1-5s of jitter.
    In the rare event that our API returns a 502 or 503 status code, 
    we recommend employing the same exponential backoff strategy as with 429s."

    :param distinct_id: Unique user identifier.
    :param event_name: Event name (without the 'mcp:' prefix).
    :param properties: Optional dictionary of event properties.
    """

    try:
        def track_to_mixpanel():
            track_event(distinct_id, event_name, properties)
        
        retry_with_backoff(
            func=track_to_mixpanel,
            max_retries=10,
            backoff_factor=2,
            max_backoff=60,
            jitter_range=(1, 5),
            retry_status_codes=[429, 502, 503],
            exclude_status_codes=[400, 401, 403, 404],  
            timeout=300, 
        )
    except Exception as e:
        logger.warning(
            f"Error triggering Mixpanel event. Event: {event_name}; Distinct ID: {distinct_id}; Error: {str(e)}"
        )


async def background_mixpanel_event_tracking(user_id: str, event: str, properties: dict):
    """
    Asynchronously sends a Mixpanel tracking event in a background thread.

    This function wraps a synchronous Mixpanel SDK call using asyncio's
    default thread pool executor, allowing non-blocking usage within async code.

    Args:
        user_id (str): The identifier of the user performing the event.
        event (str): The name of the event to track.
        properties (dict): A dictionary of properties associated with the event.

    Returns:
        None
    """
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, mixpanel_event_tracking, user_id, event, properties)
