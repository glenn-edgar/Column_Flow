from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event, Event_id_dict



class Watch_Dog_Opcodes(Support_Functions):
    def __init__(self,cf):
        self.cf = cf
        self.support_functions = Support_Functions(cf)
        self.event_id_dict = Event_id_dict()
       
        
        
    def exec_watch_dog_init(self,element_data):
        element_data["pat_count"] = 0
        if element_data["init"] is not None:
            element_data["init"](element_data["fn_data"])

    

    def exec_watch_dog(self,element_data,event):
        if element_data["pat_event"] == event["event_id"]:
            element_data["pat_count"] = 0;
        if event["event_id"] == element_data["cancel_event"]:
            return "CF_DISABLE"
        if event["event_id"] == "CF_TIME":
            element_data["pat_count"] += 1
            if element_data["pat_count"] >= element_data["pat_time_out"]:
                if element_data["reset_flag"] == True:
                    return "CF_RESET"
                else:
                    return "CF_TERMINATE"
        return "CF_CONTINUE"
    
    
    
    # pat_event and cancel_event are user defined so that muliple watch dogs can be in same chain of column
    
    def asm_watch_dog(self,pat_event,cancel_event,pat_time_out,reset_flag = False,name=None):
        element_data = {}
        element_data["pat_event"] = pat_event
        element_data["cancel_event"] = cancel_event
        element_data["pat_time_out"] = pat_time_out
        element_data["reset_flag"] = reset_flag
        self.cf.add_element(process_function=self.exec_watch_dog,
                            initialization_function=self.exec_watch_dog_init,
                            termination_function=None,
                            data=element_data, name=name)
        