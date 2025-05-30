
from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event_id_dict

class Wait_Opcodes(Support_Functions):
    def __init__(self,cf):
        self.cf = cf
        self.support_functions = Support_Functions(cf)
        self.event_id_dict = Event_id_dict()

    def exec_wait_init(self,element_data_total):
        element_data = element_data_total["data"]
        element_data["start_time"] = datetime.now()

        if element_data["initialization_function"] is not None:
            element_data["initialization_function"](element_data["fn_data"])

    def exec_wait_term(self,element_data_total):
        element_data = element_data_total["data"]
        if element_data["termination_function"] is not None:
            element_data["termination_function"](element_data["fn_data"])


    def exec_wait(self,element_data_total ,event):
        element_data = element_data_total["data"]
        if element_data["process_function"](element_data["fn_data"],event) == True:
            return "CF_DISABLE"
        if element_data["timeout"] is not None:
            if datetime.now() - element_data["start_time"] > element_data["timeout"]:
                if element_data["reset_flag"] == True:
                  return "CF_RESET"
                else:
                  return "CF_TERMINATE"
        else:
            return "CF_HALT"
      
    def asm_wait(self,wait_fn,wait_fn_init,wait_fn_term,fn_data, reset_flag = False, timeout=None,name=None):
        element_data = {}
        element_data["fn_data"] = fn_data
        element_data["reset_flag"] = reset_flag
        element_data["timeout"] = timeout
        element_data["initialization_function"] = wait_fn_init
        element_data["termination_function"] = wait_fn_term
        element_data["process_function"] = wait_fn
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

    def asm_wait_for_event(self,event_id,event_count = 1,reset_flag = False,timeout=None,name=None):
        element_data = {}
        element_data["event_id"] = event_id
        element_data["event_count"] = event_count
        self.asm_wait(self.exec_wait_for_event,self.exec_wait_for_event_init,None,element_data,reset_flag,timeout,name)
        
        
    def asm_wait_for_time_out(self,event_count = 1,name=None):
        self.asm_wait_for_event("CF_TIMER_EVENT",event_count,False,None,name)