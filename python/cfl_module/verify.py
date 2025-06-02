from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event_id_dict

class Verify_Opcodes(Support_Functions):
    def __init__(self,cf):
        self.cf = cf
        self.support_functions = Support_Functions(cf)
        self.event_id_dict = Event_id_dict()

    def exec_verify(self,element_data,event):
        if element_data["fn"](element_data["fn_data"],event) == True:
            return "CF_CONTINUE"
        if element_data["failure_fn"] is not None:
            element_data["failure_fn"](element_data["failure_data"])
        if element_data["reset_flag"] == True:
            return "CF_RESET"
        else:
            return "CF_TERMINATE"
        
        if element_data["timeout"] is not None:
            if event.event_id == element_data["time_out_event"]:    
                element_data["time_out_count"] += 1
                if element_data["time_out_count"] >= element_data["timeout"]:
                    if element_data["failure_fn"] is not None:
                        element_data["failure_fn"](element_data["failure_data"])
                    if element_data["reset_flag"] == True:
                        return "CF_RESET"
                    else:
                        return "CF_TERMINATE"
            return "CF_CONTINUE"
        
        
    def exec_verify_init(self,element_data):
        element_data["start_time"] = datetime.now()
        if element_data["init"] is not None:
            element_data["init"](element_data["fn_data"])
        if element_data["timeout"] is not None:
            element_data["time_out_count"] = 0
            
    def exec_verify_term(self,element_data):
        if element_data["term"] is not None:
            element_data["term"](element_data["fn_data"])



    def asm_verify(self,verify_fn ,verify_fn_init = None,verify_fn_term = None,fn_data=None,
                   reset_flag = False,timeout = None,time_out_event = "CF_TIMER_EVENT",failure_fn = None, failure_data = None, name=None):
        element_data = {}
        element_data["fn_data"] = fn_data
        element_data["reset_flag"] = reset_flag
        
        element_data["init"] = verify_fn_init
        element_data["term"] = verify_fn_term
        element_data["fn"] = verify_fn
        element_data["failure_fn"] = failure_fn
        element_data["failure_data"] = failure_data
        element_data["timeout"] = timeout
        self.cf.add_element(process_function=self.exec_verify,
                            initialization_function=self.exec_verify_init,
                            termination_function=self.exec_verify_term,
                            data=element_data, name=name)


    

        