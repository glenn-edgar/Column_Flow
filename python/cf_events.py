"""
Event-driven processing system with dual queue architecture
"""

from collections import deque
from typing import Any, Optional, List
import threading

class Event_id_dict():
    def __init__(self):
        self.event_id_dict = {}
    
    def add_event_id(self,event_id,description):
        if event_id in self.event_id_dict:
            raise ValueError(f"Event ID '{event_id}' already exists")
        self.event_id_dict[event_id] = description
        
        
    
    def get_description(self,event_id):
        if event_id not in self.event_id_dict:
            raise ValueError(f"Event ID '{event_id}' does not exist")
        return self.event_id_dict[event_id]
    
    def dump_events(self):
        for event_id, description in self.event_id_dict.items():
            print(f"{event_id}: {description}")
            
  
    
    
class Event:
    """Event class to encapsulate event data and metadata"""
    
    def __init__(self, event_id: str, data: Any):
        """
        Initialize an Event
        
        Args:
            event_id (str): Unique string identifier for the event
            data (object): Python object containing event data
        """
        if not isinstance(event_id, str):
            raise TypeError("event_id must be a string")
        
        if not event_id.strip():
            raise ValueError("event_id cannot be empty or only whitespace")
        
        self.event_id = event_id.strip()
        self.data = data
    
    def __repr__(self):
        return f"Event(event_id='{self.event_id}', data={self.data})"
    
    def __eq__(self, other):
        """Check equality based on event_id and data"""
        if not isinstance(other, Event):
            return False
        return self.event_id == other.event_id and self.data == other.data
    
    def __hash__(self):
        """Make Event hashable for use in sets/dicts"""
        return hash((self.event_id, str(self.data)))


class EventQueue:
    """Thread-safe event queue for managing events"""
    
    def __init__(self, name: str, max_size: Optional[int] = None):
        """
        Initialize an EventQueue
        
        Args:
            name (str): Name identifier for the queue
            max_size (int, optional): Maximum queue size, None for unlimited
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        
        self.name = name
        self.max_size = max_size
        self._queue = deque()
        self._lock = threading.Lock()
        self._event_count = 0
    
    def enqueue(self, event: Event) -> bool:
        """
        Add an event to the queue
        
        Args:
            event (Event): Event to add to the queue
            
        Returns:
            bool: True if event was added, False if queue is full
            
        Raises:
            TypeError: If event is not an Event instance
        """
        if not isinstance(event, Event):
            raise TypeError("event must be an Event instance")
        
        with self._lock:
            if self.max_size is not None and len(self._queue) >= self.max_size:
                return False  # Queue is full
            
            self._queue.append(event)
            self._event_count += 1
            return True
    
    def dequeue(self) -> Optional[Event]:
        """
        Remove and return the next event from the queue
        
        Returns:
            Event or None: Next event or None if queue is empty
        """
        with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()
    
    def peek(self) -> Optional[Event]:
        """
        Look at the next event without removing it
        
        Returns:
            Event or None: Next event or None if queue is empty
        """
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]
    
    def size(self) -> int:
        """Get current queue size"""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        with self._lock:
            return len(self._queue) == 0
    
    def is_full(self) -> bool:
        """Check if queue is full"""
        with self._lock:
            if self.max_size is None:
                return False
            return len(self._queue) >= self.max_size
    
    def clear(self) -> int:
        """
        Clear all events from the queue
        
        Returns:
            int: Number of events that were cleared
        """
        with self._lock:
            cleared_count = len(self._queue)
            self._queue.clear()
            return cleared_count
    
    def get_all_events(self) -> List[Event]:
        """
        Get a copy of all events in the queue without removing them
        
        Returns:
            List[Event]: List of all events in queue order
        """
        with self._lock:
            return list(self._queue)
    
    def get_stats(self) -> dict:
        """
        Get queue statistics
        
        Returns:
            dict: Queue statistics including size, total processed, etc.
        """
        with self._lock:
            return {
                'name': self.name,
                'current_size': len(self._queue),
                'max_size': self.max_size,
                'total_events_processed': self._event_count,
                'is_empty': len(self._queue) == 0,
                'is_full': self.max_size is not None and len(self._queue) >= self.max_size
            }
    
    def __repr__(self):
        return f"EventQueue(name='{self.name}', size={self.size()}, max_size={self.max_size})"


class DualEventQueueSystem:
    """System managing both normal and callback event queues"""
    
    def __init__(self,chain_list: List[str], normal_queue_max_size: Optional[int] = None, 
                 callback_queue_max_size: Optional[int] = None):
        """
        Initialize the dual queue system
        
        Args:
            chain_list (List[str]): List of chain names
            normal_queue_max_size (int, optional): Max size for normal events queue
            callback_queue_max_size (int, optional): Max size for callback events queue
        """
        if not isinstance(chain_list, list):
            raise TypeError("chain_list must be a list")
        if not all(isinstance(chain_name, str) for chain_name in chain_list):
            raise TypeError("chain_list must contain only strings")
        if not chain_list:
            raise ValueError("chain_list cannot be empty")
        self.chain_list = chain_list
        self.normal_events = EventQueue("normal_events", normal_queue_max_size)
        self.callback_events = {}
        for chain_name in chain_list:
            self.callback_events[chain_name]  = EventQueue(chain_name, callback_queue_max_size)
       
    
    def add_normal_event(self, event: Event) -> bool:
        """Add event to normal events queue"""
        return self.normal_events.enqueue(event)
    
    def add_callback_event(self,chain_name  : str, event: Event) -> bool:
        """Add event to callback events queue"""
        if chain_name not in self.chain_list:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        return self.callback_events[chain_name].enqueue(event)
    
    def get_next_normal_event(self) -> Optional[Event]:
        """Get next event from normal events queue"""
        return self.normal_events.dequeue()
    
    def get_next_callback_event(self,chain_name: str) -> Optional[Event]:
        """Get next event from callback events queue"""
        if chain_name not in self.chain_list:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        return self.callback_events[chain_name].dequeue()   
    
    def has_normal_events(self) -> bool:
        """Check if normal events queue has events"""
        return not self.normal_events.is_empty()
    
    def has_callback_events(self,chain_name: str) -> bool:
        """Check if callback events queue has events"""
        if chain_name not in self.chain_list:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        return not self.callback_events[chain_name].is_empty()
    
    def clear_normal_events(self) -> int:
        """Clear normal events queue"""
        return self.normal_events.clear()
    
    def clear_callback_events(self,chain_name: str) -> int:
        """Clear callback events queue"""
        return self.callback_events[chain_name].clear()
    
    def clear_all_queues(self) -> dict:
        """Clear both queues and return counts"""
        normal_cleared = self.normal_events.clear()
        callback_cleared = {}
        for chain_name in self.chain_list:
            callback_cleared[chain_name] = self.callback_events[chain_name].clear()
        return {
            'normal_events_cleared': normal_cleared,
            'callback_events_cleared': callback_cleared,
            'total_cleared': normal_cleared + callback_cleared
        }
    
  


# Example usage and demonstration
if __name__ == "__main__":
    print("=== Event Class with String IDs ===")
    
    # Create events with string IDs
    event1 = Event("user_login", {"user_id": "12345", "timestamp": "2025-05-25T10:00:00"})
    event2 = Event("data_processed", {"records": 150, "status": "success"})
    event3 = Event("callback_response", {"callback_id": "cb_001", "result": "completed"})
    
    print(f"Event 1: {event1}")
    print(f"Event 2: {event2}")
    print(f"Event 3: {event3}")
    
    print("\n=== Dual Queue System Demo ===")
    
    # Create the dual queue system
    chain_list = ["chain1", "chain2", "chain3"]
    queue_system = DualEventQueueSystem(chain_list, normal_queue_max_size=100, callback_queue_max_size=50)
    
    # Add events to different queues
    print("\nAdding events to queues...")
    queue_system.add_normal_event(event1)
    queue_system.add_normal_event(event2)
    queue_system.add_callback_event("chain1", event3)
    queue_system.add_callback_event("chain2", event3)
    queue_system.add_callback_event("chain3", event3)
    
    # Add more events
    for i in range(3):
        normal_event = Event(f"batch_process_{i}", {"batch_id": i, "items": i * 10})
        callback_event = Event(f"callback_{i}", {"response_code": 200 + i})
        
        queue_system.add_normal_event(normal_event)
        queue_system.add_callback_event("chain1", callback_event)
        queue_system.add_callback_event("chain2", callback_event)
        queue_system.add_callback_event("chain3", callback_event)
    
    print(f"Queue system: {queue_system}")
    
    # Show queue statistics
    print("\n=== Queue Statistics ===")
   
    
    # Process some events
    print("\n=== Processing Events ===")
    print("Processing normal events:")
    while queue_system.has_normal_events():
        event = queue_system.get_next_normal_event()
        print(f"  Processed: {event}")
    
    print("\nProcessing callback events:")
    for chain_name in chain_list:
        while queue_system.has_callback_events(chain_name):
            event = queue_system.get_next_callback_event(chain_name)
            print(f"  Processed: {event}")
    
   
    
    # Demonstrate error handling
    print("\n=== Error Handling Demo ===")
    try:
        invalid_event = Event(123, "data")  # Should fail - event_id must be string
    except TypeError as e:
        print(f"Caught expected error: {e}")
    
    try:
        empty_event = Event("", "data")  # Should fail - empty event_id
    except ValueError as e:
        print(f"Caught expected error: {e}")