class CF_Watch_Dog_Test():
    def __init__(self,cf,op,Event):
        self.cf = cf
        self.op = op
        self.event = Event
        self.test_sequence_dict = {}
        self.test_sequence_dict["test_watch_dog_steady_state"] = self.test_watch_dog_steady_state
        self.test_sequence_dict["test_watch_dog_terminate"] = self.test_watch_dog_terminate
        self.test_sequence_dict["test_watch_dog_start_stop_start_terminate"] = self.test_watch_dog_start_stop_start_terminate
        self.test_sequence_dict["test_watch_dog_reset"] = self.test_watch_dog_reset
    
        
    def run_test_sequence(self,test_sequence_name):
      
        if test_sequence_name in self.test_sequence_dict:
            print("sequence name",test_sequence_name)
            print("\n\nrunning test sequence",test_sequence_name)
            self.test_sequence_dict[test_sequence_name]()
            print("end of test sequence\n\n",test_sequence_name)
        
        else:
            raise ValueError(f"Test sequence {test_sequence_name} not found")
        
    def run_all_test_sequences(self):
        
        for test_sequence_name in self.test_sequence_dict:        
            self.run_test_sequence(test_sequence_name)
    
    
    def log_error_message(self,error_data):
        print(f"Error: {error_data}")
        
    def wd_failure(self,data):
        print("Watch dog failure",data)
        print("terminating test")
        event = self.event("CF_TERMINATE_SYSTEM",None)
        self.cf.send_system_event(event)
        
    def wd_reset(self,data):
        print("Watch dog reset",data)
        print("resetting test")
       
        
        
    def test_watch_dog_steady_state(self):
        self.cf.reset_cf()
        self.cf.event_id_dict.add_event_id("WD_PAT_EVENT","Watch dog pattern event")
        self.cf.event_id_dict.add_event_id("WD_PAT_START_EVENT","Watch dog pattern start event")
        self.cf.event_id_dict.add_event_id("WD_CANCEL_EVENT","Watch dog cancel event")
        
        self.cf.add_reserved_chain_name(["strobe_watch_dog_test"])
        
        self.cf.define_chain("terminate_test",auto_flag=True)
        self.op.asm_log_message("Starting terminate test")
        self.op.asm_wait_time(10.0)
        self.op.asm_terminate_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("watch_dog_steady_state_test",auto_flag=True)
        self.op.asm_log_message("Starting watch dog steady state test")
        self.op.asm_watch_dog(pat_event = "WD_PAT_EVENT",pat_start_event = "WD_PAT_START_EVENT",cancel_event = "WD_CANCEL_EVENT",
                              pat_time_event = "CF_SECOND_EVENT",pat_time_out = 5 ,reset_flag = False,failure_fn = self.wd_failure,failure_data ="wd failure after 5 seconds")
        self.op.asm_enable_disable_chains(chain_list = ["strobe_watch_dog_test"])
        self.cf.end_chain()
        
        self.cf.define_chain("strobe_watch_dog_test",auto_flag = False)
        self.op.asm_log_message("Starting strobe watch dog test")
        self.op.asm_wait_time(1.0)
        self.op.asm_send_named_event("watch_dog_steady_state_test","WD_PAT_EVENT")

        self.op.asm_reset()
        self.cf.end_chain()
        
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Watch dog steady state test complete\n\n")
     
    def test_watch_dog_reset(self):
        self.cf.reset_cf()
        self.cf.event_id_dict.add_event_id("WD_PAT_EVENT","Watch dog pattern event")
        self.cf.event_id_dict.add_event_id("WD_PAT_START_EVENT","Watch dog pattern start event")
        self.cf.event_id_dict.add_event_id("WD_CANCEL_EVENT","Watch dog cancel event")
        
        self.cf.add_reserved_chain_name(["strobe_watch_dog_test"])
        
        self.cf.define_chain("terminate_test",auto_flag=True)
        self.op.asm_log_message("Starting terminate test")
        self.op.asm_wait_time(12.0)
        self.op.asm_terminate_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("watch_dog_steady_state_test",auto_flag=True)
        self.op.asm_log_message("Starting watch dog steady state test")
        self.op.asm_watch_dog(pat_event = "WD_PAT_EVENT",pat_start_event = "WD_PAT_START_EVENT",cancel_event = "WD_CANCEL_EVENT",
                              pat_time_event = "CF_SECOND_EVENT",pat_time_out = 5 ,reset_flag = True,failure_fn = self.wd_reset,failure_data ="wd failure after 5 seconds")
        
        self.cf.end_chain()
        
       
        
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Watch dog steady state test complete\n\n")   
        
    def test_watch_dog_terminate(self):
        self.cf.reset_cf()
        self.cf.event_id_dict.add_event_id("WD_PAT_EVENT","Watch dog pattern event")
        self.cf.event_id_dict.add_event_id("WD_PAT_START_EVENT","Watch dog pattern start event")
        self.cf.event_id_dict.add_event_id("WD_CANCEL_EVENT","Watch dog cancel event")
        
        self.cf.add_reserved_chain_name(["strobe_watch_dog_test"])
        
       
        
        self.cf.define_chain("watch_dog_steady_state_test",auto_flag=True)
        self.op.asm_log_message("Starting watch dog steady state test")
        self.op.asm_watch_dog(pat_event = "WD_PAT_EVENT",pat_start_event = "WD_PAT_START_EVENT",cancel_event = "WD_CANCEL_EVENT",
                              pat_time_event = "CF_SECOND_EVENT",pat_time_out = 5 ,reset_flag = False,failure_fn = self.wd_failure,failure_data ="wd failure after 5 seconds")
        self.op.asm_enable_disable_chains(chain_list = ["strobe_watch_dog_test"])
        self.cf.end_chain()
        
        self.cf.define_chain("strobe_watch_dog_test",auto_flag = False)
        self.op.asm_log_message("Starting strobe watch dog test")
        self.op.asm_wait_time(1.0)
        self.op.asm_send_named_event("watch_dog_steady_state_test","WD_PAT_EVENT")
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Watch dog steady state test complete\n\n")
        
    def test_watch_dog_start_stop_start_terminate(self):
        self.cf.reset_cf()
        self.cf.event_id_dict.add_event_id("WD_PAT_EVENT","Watch dog pattern event")
        self.cf.event_id_dict.add_event_id("WD_PAT_START_EVENT","Watch dog pattern start event")
        self.cf.event_id_dict.add_event_id("WD_CANCEL_EVENT","Watch dog cancel event")
        self.cf.event_id_dict.add_event_id("WD_START_EVENT","Watch dog start event")
        
        self.cf.add_reserved_chain_name(["strobe_watch_dog_test"])
        
       
        
        self.cf.define_chain("watch_dog_steady_state_test",auto_flag=True)
        self.op.asm_log_message("Starting watch dog steady state test")
        self.op.asm_watch_dog(pat_event = "WD_PAT_EVENT",pat_start_event = "WD_START_EVENT",cancel_event = "WD_CANCEL_EVENT",
                              pat_time_event = "CF_SECOND_EVENT",pat_time_out = 5 ,reset_flag = False,failure_fn = self.wd_failure,failure_data ="wd failure after 5 seconds")
        self.op.asm_enable_disable_chains(chain_list = ["strobe_watch_dog_test"])
        self.cf.end_chain()
        
        self.cf.define_chain("strobe_watch_dog_test",auto_flag = False)
        self.op.asm_log_message("Starting strobe watch dog test")
        self.op.asm_wait_time(1.0)
        self.op.asm_log_message("Sending watch dog pattern event")
        self.op.asm_send_named_event("watch_dog_steady_state_test","WD_PAT_EVENT")
        self.op.asm_wait_time(3.0)
        self.op.asm_log_message("Sending watch dog cancel event")
        self.op.asm_send_named_event("watch_dog_steady_state_test","WD_CANCEL_EVENT")
        self.op.asm_wait_time(6.0)
        self.op.asm_log_message("Sending watch dog start event")
        self.op.asm_send_named_event("watch_dog_steady_state_test","WD_START_EVENT")
        self.op.asm_log_message("Waiting for watch dog to fail")
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Watch dog steady state test complete\n\n")
        