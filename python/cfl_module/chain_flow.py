"""
Chain Flow Module - Event-driven processing system with configurable chains
"""
import sys
from time import sleep
from datetime import datetime, timedelta

import time
from cf_events import Event, EventQueue, DualEventQueueSystem
from cf_events import Event_id_dict

class ChainFlow:
    """
    Chain Flow class for managing sequential processing chains
    """
    
    def __init__(self,time_tick):
       
        if not callable(time_tick):
            raise TypeError("time_tick must be a callable function")
        self.time_tick = time_tick
        
        self.reset_cf()
        """Initialize ChainFlow with empty chain collections"""
       
        
    def reset_cf(self):
        self.event_id_dict = Event_id_dict()
        self.event_id_dict.add_event_id("CF_TIMER_EVENT","Timer Event")
        self.event_id_dict.add_event_id("CF_SYSTEM_RESET","System Reset Event")
        self.event_id_dict.add_event_id("CF_SYSTEM_STOP","System Stop Event")
        self.event_id_dict.add_event_id("CF_HALT","Halt Event")
        self.event_id_dict.add_event_id("CF_CONTINUE","Continue Event")
        self.event_id_dict.add_event_id("CF_DISABLE","Disable Event")
        self.event_id_dict.add_event_id("CF_RESET","Reset Event")
        self.event_id_dict.add_event_id("CF_TERMINATE","Terminate Event")
        self.event_id_dict.add_event_id("CF_SECOND_EVENT","NewSecond Event")
        self.event_id_dict.add_event_id("CF_MINUTE_EVENT","New Minute Event")
        self.event_id_dict.add_event_id("CF_HOUR_EVENT","New Hour Event")
        self.event_id_dict.add_event_id("CF_DAY_EVENT","New Day Event")
        self.event_id_dict.add_event_id("CF_TERMINATE_SYSTEM","Terminate System Event")
        self.event_id_dict.add_event_id("CF_RESET_SYSTEM","Reset System Event")
        
        
       
        self._disable = False
        
       
        self.list_of_chains = []  # Ordered list of chain names
        self.chain_dict = {}      # Dictionary mapping chain names to chain data
        self._current_chain = None  # Track chain being defined
        self._finalized = False   # Track if chain is finalized
        self._system_active = True
        self._execution_active = False       
        self.reserved_chain_names = []
        
    def add_reserved_chain_name(self,chain_list):
        if not isinstance(chain_list,list):
            chain_list = [chain_list]
            
        for chain_name in chain_list:
           
    
            if chain_name not in self.reserved_chain_names:
                self.reserved_chain_names.append(chain_name)
            
    def define_chain(self, chain_name, auto_flag=False):
        """
        Start defining a new processing chain
        
        Args:
            chain_name (str): Unique name for the chain
            auto_flag (bool): Whether chain should auto-execute
            
        Raises:
            ValueError: If chain name already exists or another chain is being defined
            TypeError: If chain_name is not a string
        """
        if not isinstance(chain_name, str):
            raise TypeError("chain_name must be a string")
        
        if self._finalized:
            raise RuntimeError("Cannot define chains after finalization")
        
        if chain_name not in self.reserved_chain_names:
            self.reserved_chain_names.append(chain_name)
            
        if self._current_chain is not None:
            raise ValueError(f"Cannot define new chain '{chain_name}' while chain '{self._current_chain}' is still being defined. Call end_chain() first.")
        
        if chain_name in self.chain_dict:
            raise ValueError(f"Chain name '{chain_name}' already exists. Chain names must be unique.")
        
        # Initialize new chain
        self.chain_dict[chain_name] = {
            'element_list': [],
            'auto_flag': auto_flag,
            'active': False,
            'chain_data': {},
            
        }
        
        self._current_chain = chain_name
        
        
    def set_chain_data(self,chain_name,data):
        if chain_name not in self.chain_dict:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        self.chain_dict[chain_name]['chain_data'] = data
        
    def get_chain_data(self,chain_name):
        if chain_name not in self.chain_dict:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        return self.chain_dict[chain_name]['chain_data']
        
        
        
    
    def add_element(self, process_function,initialization_function=None,termination_function=None,data=None, name=None):
        """
        Add a processing element to the current chain
        
        Args:
            process_Function (callable): Python function for processing
            name (str, optional): Unique name for the element within the chain
            
        Raises:
            ValueError: If no chain is being defined or name conflicts
            TypeError: If process_Function is not callable or is None
        """
        if self._finalized:
            raise RuntimeError("Cannot add elements after finalization")
        
        if self._current_chain is None:
            raise ValueError("No chain is currently being defined. Call define_chain() first.")
        
        if process_function is None:
            raise TypeError("process_function cannot be None")
        
        if not callable(process_function):
            raise TypeError("process_function must be a callable Python function")
  
        if initialization_function is not None:
            if not callable(initialization_function):
                raise TypeError("initialization_function must be a callable Python function")
        if termination_function is not None:
            if not callable(termination_function):
                raise TypeError("termination_function must be a callable Python function")
        
        # Generate name if not provided
        if name is None:
            element_count = len(self.chain_dict[self._current_chain]['element_list'])
            name = f"element_{element_count + 1}"
        
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        
        # Check for name uniqueness within current chain
        current_chain_data = self.chain_dict[self._current_chain]
        existing_names = [elem['name'] for elem in current_chain_data['element_list']]
        
        if name in existing_names:
            raise ValueError(f"Element name '{name}' already exists in chain '{self._current_chain}'. Names must be unique within a chain.")
        
  
        # Create element dictionary
        element_dict = {
            'name': name,
            'enable': True,
            'initialized': False,
            'initialization_function': initialization_function,
            'termination_function': termination_function,
            'process_function': process_function,
            'data': data
        }
        
        # Add to current chain's element list
        current_chain_data['element_list'].append(element_dict)

    
    def end_chain(self):
        """
        Complete the definition of the current chain
        
        Raises:
            ValueError: If no chain is being defined
        """
        if self._finalized:
            raise RuntimeError("Cannot end chains after finalization")
        
        if self._current_chain is None:
            raise ValueError("No chain is currently being defined")
        
        # Add chain name to ordered list
        self.list_of_chains.append(self._current_chain)
        
        chain_name = self._current_chain
        element_count = len(self.chain_dict[self._current_chain]['element_list'])
        
       
        
        # Clear current chain
        self._current_chain = None
    
    def finalize(self):
        """
        Finalize the chain flow system - all chains must be properly defined
        
        Raises:
            ValueError: If a chain is still being defined
        """
        if self._current_chain is not None:
            raise ValueError(f"Chain '{self._current_chain}' is still being defined. Call end_chain() first.")
        self.event_system = DualEventQueueSystem(self.list_of_chains)
        self._finalized = True
       

    
    def get_chain_info(self, chain_name=None):
        """
        Get information about chains
        
        Args:
            chain_name (str, optional): Specific chain name, or None for all chains
            
        Returns:
            dict or list: Chain information
        """
        if chain_name:
            if chain_name not in self.chain_dict:
                raise ValueError(f"Chain '{chain_name}' does not exist")
            return self.chain_dict[chain_name]
        else:
            return {
                'chains': self.list_of_chains,
                'chain_count': len(self.list_of_chains),
                'finalized': self._finalized
            }
   
    
    def enable_chain(self, chain_name):
        """
        Enable a chain and reset all its elements
        
        Args:
            chain_name (str): Name of the chain to enable
            
        Raises:
            ValueError: If chain doesn't exist
            TypeError: If chain_name is not a string
            RuntimeError: If system is not finalized
        """
      
        if not isinstance(chain_name, str):
            raise TypeError("chain_name must be a string")
        
        if not self._finalized:
            raise RuntimeError("ChainFlow must be finalized before enabling chains")
        
        if chain_name not in self.chain_dict:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        
        # Enable the chain
        self.chain_dict[chain_name]['active'] = True
        self.event_system.clear_callback_events(chain_name)
        
        # Enable all elements in the chain and reset their initialization status
        for element in self.chain_dict[chain_name]['element_list']:
            element['enable'] = True
            element['initialized'] = False
      
    def is_chain_active(self,chain_name):
        if chain_name not in self.chain_dict:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        return self.chain_dict[chain_name]['active']
    
    def disable_chain(self, chain_name):
        """
        Disable a chain and execute termination functions for active elements
        
        Args:
            chain_name (str): Name of the chain to disable
            
        Raises:
            ValueError: If chain doesn't exist
            TypeError: If chain_name is not a string
            RuntimeError: If system is not finalized
        """
        
        if not isinstance(chain_name, str):
            raise TypeError("chain_name must be a string")
        
        if not self._finalized:
            raise RuntimeError("ChainFlow must be finalized before disabling chains")
        
        if chain_name not in self.chain_dict:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        if self.chain_dict[chain_name]['active'] == False:
            return
        self.chain_dict[chain_name]['active'] = False
        self.event_system.clear_callback_events(chain_name)
        # Get the chain data
        chain_data = self.chain_dict[chain_name]
        
        # Process elements in reverse order (last to first)
        element_list = chain_data['element_list']
        terminated_count = 0
        
        for element in reversed(element_list):
            
            # Check if element is active (enabled and initialized)
            if element['enable'] and element['initialized']:
                # Execute termination function if it exists
                if element['termination_function'] is not None:
                    try:
                        
                        element["current_chain"] = chain_name
                        element['termination_function'](element)
                        terminated_count += 1
                    except Exception as e:
                        raise e
                
                # Set element as no longer initialized since we're terminating it
                element['initialized'] = False
            
            # Disable the element
            element['enable'] = False
        
     
    
       
    def disable_all_chains(self):
        for chain_name in self.list_of_chains:
            self.disable_chain(chain_name)
        
        
    def send_named_queue_event(self,chain_name: str, event: Event):
        """
        Send a event to queue tied to a chain
        Args:
            chain_name (str): Name of the chain to send the event to
            event (Event): Event to send
            
        Raises:
            ValueError: If chain doesn't exist
        """
        if not isinstance(chain_name, str):
            raise TypeError("chain_name must be a string")
        if not isinstance(event, Event):
            raise TypeError("event must be an instance of Event")
        if event.event_id not in self.event_id_dict.event_id_dict:
            raise ValueError(f"Event ID '{event.event_id}' is not a valid  event")
        if chain_name not in self.chain_dict:
            raise ValueError(f"Chain '{chain_name}' does not exist")
        if not self.chain_dict[chain_name]['active']:
            raise ValueError(f"Chain '{chain_name}' is not active")
        self.event_system.add_callback_event(chain_name, event)
        
    def send_system_event(self, event: Event):
        """
        Send a system event 
        """
     
        if not isinstance(event, Event):
            raise TypeError("event must be an instance of Event")
        if event.event_id not in self.event_id_dict.event_id_dict:
            raise ValueError(f"Event ID '{event.event_id}' is not a valid  event")
        self.event_system.add_normal_event(event)
        
    def reset_system(self):
        self.send_system_event(Event("CF_SYSTEM_RESET"))
    def stop_system(self):
        self.send_system_event(Event("CF_SYSTEM_STOP"))
    
    def initialize_chains(self):
        """
        Initialize all chains based on their auto_flag setting
        
        For chains with auto_flag == True: enable the chain
        For chains with auto_flag == False: disable the chain
        
        Raises:
            RuntimeError: If system is not finalized
        """
        if not self._finalized:
            raise RuntimeError("ChainFlow must be finalized before initializing chains")
        
        enabled_chains = []
        disabled_chains = []
        self.event_system.clear_normal_events()
        # Process each chain in the order they were defined
        for chain_name in self.list_of_chains:
            chain_data = self.chain_dict[chain_name]
            auto_flag = chain_data['auto_flag']
            
            if auto_flag:
                # Enable chains with auto_flag == True
                self.enable_chain(chain_name)
                enabled_chains.append(chain_name)
            else:
                # Disable chains with auto_flag == False
                self.disable_chain(chain_name)
                disabled_chains.append(chain_name)
        
    def execute_system_event_loop(self):
        while self._system_active:
            self.execute_system_event()
            if self.event_system.normal_events.size() == 0:
                break
            
            
    def execute_system_event(self):
        """
        Execute the system event
        return True if event processing is to continue, False if it is to stop
        """
        event = self.event_system.get_next_normal_event()
        
        if event is not None:
            
            if event.event_id == "CF_TERMINATE_SYSTEM":
                self.disable_all_chains()
                self._system_active = False

            elif event.event_id == "CF_RESET_SYSTEM":
                print("made it here ------------------->")
                self.disable_all_chains()
                self.initialize_chains()
            
                
            self._system_active = False
            for chain_name in self.list_of_chains:
                if self.chain_dict[chain_name]['active']:
                    self.execute_chain_event(chain_name,event)
        else:
            pass
       
        
    
    def execute_chain_event(self, chain: str, event: Event):
        self._current_chain = chain
        if not self.chain_dict[chain]['active']:
            return
        while self.event_system.has_callback_events(chain):
            event_cb = self.event_system.get_next_callback_event(chain)
            if event is not None:
                self.execute_chain_element(chain,event_cb)
          
        self.execute_chain_element(chain,event)
        
        while self.event_system.has_callback_events(chain):
            event_cb = self.event_system.get_next_callback_event(chain)
        
            if event is not None:
                self.execute_chain_element(chain,event_cb)
     
    def execute_chain_element(self, chain: str, event: Event):
        for element in self.chain_dict[chain]['element_list']:
            element["current_chain"] = chain
            if element['enable'] == False:
                continue
            if element['enable'] and element['initialized'] == False:
                element['initialized'] = True
                if element['initialization_function'] is not None:
                    element['initialization_function'](element)
            self._system_active = True
            return_code = element['process_function'](element,event)
            continue_flag = self.analyze_return_code(chain,element,return_code)
            if not continue_flag:
                break

 

    def analyze_return_code(self, chain: str, element: dict, return_code: str):
        valid_return_codes = ["CF_HALT", "CF_CONTINUE", "CF_DISABLE", "CF_RESET", "CF_TERMINATE"]
        if type(return_code) is not str:
            raise TypeError("return_code must be a string")
        if return_code not in valid_return_codes:
            raise ValueError(f"Invalid return code: {return_code}")
        continue_flag = False
        if return_code == "CF_HALT":
            return False
        elif return_code == "CF_CONTINUE":
            return True
        elif return_code == "CF_DISABLE":
            element['enable'] = False
            element['initialized'] = False
            return True
        elif return_code == "CF_RESET":
            self.disable_chain(chain)
            self.enable_chain(chain)
            return False
        elif return_code == "CF_TERMINATE":
         
            self.disable_chain(chain)
            return False
            
      
        
    def cf_engine_start(self):
        """
        Start the chain flow engine
        """
       
   

        self.time_stamp = time.time()
        self.ref_second = int(self.time_stamp % 60)
        self.ref_minute = int(self.ref_second / 60)
        self.ref_hour = int(self.ref_second / 3600)
        self.ref_day = int(self.ref_second / 86400)
        

        
        while True:
        
        
            self.initialize_chains()
            
            self._system_active = True
            while True:
                
                if self._system_active == False:
                   return
                self.time_tick() #time delay function  
                self.ref_time_stamp = self.time_stamp
                self.time_stamp = time.time()
                self.current_second = int(self.time_stamp % 60)
                self.current_minute = int(self.current_second / 60)
                self.current_hour = int(self.current_second / 3600)
                self.current_day = int(self.current_second / 86400)
                   
                self.time_stamp =time.time()
                event = Event("CF_TIMER_EVENT",{'delta_time':self.time_stamp - self.ref_time_stamp,'time_stamp':self.time_stamp})
                self.send_system_event(event)
             
                
            
                if self.current_second != self.ref_second:
                    self.ref_second = self.current_second
                    event = Event("CF_SECOND_EVENT",{'second':self.current_second,'time_stamp':self.time_stamp})
                    self.send_system_event(event)
                
                if self.current_minute != self.ref_minute:
                    self.ref_minute = self.current_minute
                    event = Event("CF_MINUTE_EVENT",{'minute':self.current_minute,'time_stamp':self.time_stamp})
                    self.send_system_event(event)
            
                if self.current_hour != self.ref_hour:
                    self.ref_hour = self.current_hour
                    event = Event("CF_HOUR_EVENT",{'hour':self.current_hour,'time_stamp':self.time_stamp})
                    self.send_system_event(event)
                
                if self.current_day != self.ref_day:
                    self.ref_day = self.current_day
                    event = Event("CF_DAY_EVENT",{'day':self.current_day,'time_stamp':self.time_stamp})
                    self.send_system_event(event)
                    
                self.execute_system_event_loop()
       
        
    def cf_engine_stop(self):
        """
        Stop the chain flow engine
        """
        
    def __repr__(self):
        return f"ChainFlow(chains={len(self.list_of_chains)})"

  

