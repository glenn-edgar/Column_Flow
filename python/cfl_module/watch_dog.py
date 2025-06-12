from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event, Event_id_dict



class Watch_Dog_Opcodes(Support_Functions):
    def __init__(self,cf):
        self.cf = cf
        self.support_functions = Support_Functions(cf)
        self.event_id_dict = Event_id_dict()
    
        
        
    def exec_watch_dog_init(self,data):
        element_data = data["data"]
        element_data["pat_count"] = 0
        element_data["pat_state"] = True
    

    def exec_watch_dog(self,data,event):
        element_data = data["data"]
        if element_data["pat_state"] == True:
           return self.handle_watch_dog_on(element_data,event)
        else:
           return self.handle_watch_dog_off(element_data,event)
            
            
    def handle_watch_dog_on(self,element_data,event):
        if event.event_id == element_data["pat_event"]:
            element_data["pat_count"] = 0;
            return "CF_HALT"
        if event.event_id == element_data["cancel_event"]:
            element_data["pat_state"] = False
            return "CF_HALT"
        if event.event_id == element_data["time_event"]:
            element_data["pat_count"] += 1
            if element_data["pat_count"] >= element_data["pat_time_out"]:
                if "failure_fn" in element_data and element_data["failure_fn"] is not None:
                    element_data["failure_fn"](element_data["failure_data"])
                if element_data["reset_flag"] == True:
    
                    return "CF_RESET"
                else:
                    return "CF_TERMINATE"
        return "CF_CONTINUE"
    
    def handle_watch_dog_off(self,element_data,event):
        if event.event_id == element_data["start_event"]:
            element_data["pat_state"] = True
            element_data["pat_count"] = 0
            return "CF_HALT"
        return "CF_CONTINUE"
            
            
    
    
    
    # pat_event and cancel_event are user defined so that muliple watch dogs can be in same chain of column
    
    def asm_watch_dog(self,pat_event,pat_start_event,cancel_event,pat_time_event,pat_time_out,reset_flag = False,failure_fn=None,failure_data=None,name=None):
        element_data = {}
        element_data["pat_event"] = pat_event
        element_data['start_event'] = pat_start_event
        element_data["cancel_event"] = cancel_event
        element_data["time_event"] = pat_time_event
        element_data["pat_time_out"] = pat_time_out
        element_data["reset_flag"] = reset_flag
        element_data["failure_fn"] = failure_fn
        element_data["failure_data"] = failure_data
        assert pat_event is not None, "pat_event is required"
        assert pat_start_event is not None, "pat_start_event is required"
        assert cancel_event is not None, "cancel_event is required"
        assert pat_time_event is not None, "pat_time_event is required"
        assert pat_time_out is not None, "pat_time_out is required"
        assert reset_flag is not None, "reset_flag is required"
        
        self.cf.add_element(process_function=self.exec_watch_dog,
                            initialization_function=self.exec_watch_dog_init,
                            termination_function=None,
                            data=element_data, name=name)
        