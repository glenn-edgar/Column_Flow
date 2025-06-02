from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event_id_dict
import time

class Wait_Opcodes(Support_Functions):
    def __init__(self,cf):
        self.cf = cf
        self.support_functions = Support_Functions(cf)
        self.event_id_dict = Event_id_dict()

    def exec_wait_init(self,element_data_total):
        element_data = element_data_total["data"]
        element_data["time_out_count"] = 0

        if element_data["initialization_function"] is not None:
            element_data["initialization_function"](element_data["fn_data"])

    def exec_wait_term(self,element_data_total):
        element_data = element_data_total["data"]
        if element_data["termination_function"] is not None:
            element_data["termination_function"](element_data["fn_data"])


 
    def exec_wait(self, element_data_total, event):
        try:
            # Validate input
            if not isinstance(element_data_total, dict) or "data" not in element_data_total:
                raise ValueError("element_data_total must be a dict with 'data' key")
            
            element_data = element_data_total["data"]
            
           
            
            # Check process_function
            if callable(element_data["process_function"]):
                if element_data["process_function"](element_data["fn_data"], event) is True:
                    return "CF_DISABLE"
            else:
                raise TypeError("process_function must be callable")
            
            # Handle timeout
            if element_data["timeout"] is not None:
                if event.event_id == element_data["time_out_event"]:
                   element_data["time_out_count"] += 1
                   if element_data["time_out_count"] >= element_data["timeout"]:
                       
                    # Execute error_function if it exists and is callable
                    if element_data["error_function"] is not None:
                        if callable(element_data["error_function"]):
                            element_data["error_function"](element_data["error_data"])
                        else:
                            raise TypeError("error_function must be callable")
                        if element_data["reset_flag"] is True:
                            return "CF_RESET"
                        else:
                        
                            return "CF_TERMINATE"
   
            return "CF_HALT"
    
        except Exception as e:
            # Log error and re-raise or handle as needed
            raise RuntimeError(f"Error in exec_wait: {str(e)}")
    def asm_wait(self,wait_fn,wait_fn_init,wait_fn_term,fn_data, reset_flag = False, timeout=None,time_out_event="CF_TIMER_EVENT",error_fn = None,error_data = None,name=None):
        element_data = {}
        element_data["fn_data"] = fn_data
        element_data["reset_flag"] = reset_flag
        element_data["timeout"] = timeout
        element_data["time_out_event"] = time_out_event
        element_data["initialization_function"] = wait_fn_init
        element_data["termination_function"] = wait_fn_term
        element_data["process_function"] = wait_fn
        element_data["error_function"] = error_fn
        element_data["error_data"] = error_data
        self.cf.add_element(process_function=self.exec_wait,
                            initialization_function=self.exec_wait_init,
                            termination_function=self.exec_wait_term,
                            data=element_data, name=name)
       
        
    
    def exec_wait_for_event(self,element_data,event_data):
      
        if(element_data["event_id"] == event_data.event_id):
            element_data["received"] += 1
            if(element_data["received"] >= element_data["event_count"]):
                return True
        else:
            return False
        
    def exec_wait_for_event_init(self,element_data):
    
        element_data["received"] = 0

    def asm_wait_for_event(self,event_id,event_count = 1,reset_flag = False,timeout=None,error_fn = None,time_out_event ="CF_TIMER_EVENT",error_data = None,name=None):
        element_data = {}
        element_data["event_id"] = event_id
        element_data["event_count"] = event_count
        self.asm_wait(self.exec_wait_for_event,self.exec_wait_for_event_init,None,element_data,reset_flag,timeout,time_out_event,error_fn,error_data,name)
    
    def exec_time_delay_init(self,element_data):
    
        element_data["data"]["start_time"] = time.time()
        
        
    def exec_time_delay(self,element_data,event):

        
        if event.event_id == "CF_TIMER_EVENT":
            data = element_data["data"]
           
            if time.time() > data["time_delay"] +data["start_time"]:
              
                return "CF_DISABLE"
        return "CF_HALT"
    
    def asm_wait_time(self,time_delay,name=None):
        element_data = {}
        element_data["time_delay"] = time_delay #time delay in seconds
    
        self.cf.add_element(process_function=self.exec_time_delay,
                            initialization_function=self.exec_time_delay_init,
                            termination_function=None,
                            data=element_data, name=name)
 