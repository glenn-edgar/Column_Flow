import time

class CF_Basic_Tests():
    def __init__(self,cf,op,Event):
        self.cf = cf
        self.op = op
        self.event = Event
        self.test_sequence_dict = {}
        self.test_sequence_dict["test_chain_management"] = self.test_chain_management
        self.test_sequence_dict["test_system_reset"] = self.test_system_reset
           
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
        
    """
    This file test the following opcodes:
    asm_one_shot_handler(self,one_shot_fn,one_shot_data,one_shot_name = None):
    asm_bidirectional_one_shot_handler(self,one_shot_fn,termination_fn,one_shot_data,one_shot_name = None):
    asm_log_message(self,message,name = None):
    asm_reset(self,name = None) -- test in other files
    asm_terminate(self,name = None):
    asm_halt(self,name = None):
    asm_terminate_system(self,name = None) -- tested in other files
    asm_reset_system(self,name = None):
    asm_send_system_event(self,event_id,event_data=None,name = None):
    asm_send_named_event(self,chain_name,event_id,event_data=None,name = None):
    asm_enable_chains(self,chain_list,name = None):
    asm_disable_chains(self,chain_list,name = None):
    asm_enable_disable_chains(self,chain_list,name = None):
    asm_enable_wait_chains(self,chain_list,name = None):
    asm_join_chains(self,chain_list,name = None):
    
    """
    def initialization_one_shot_handler(self,data):
        print("initialization_one_shot_handler",data["data"])
        
    
    def termination_one_shot_handler(self,data):
        print("termination_one_shot_handler",data["data"])
    
    def output_one_shot_handler(self,data):
        print("output_one_shot_handler",data["data"])
    
    def test_chain_management(self):
        self.cf.reset_cf()
        self.cf.event_id_dict.add_event_id("test_event_1","Test event 1")
        self.cf.event_id_dict.add_event_id("test_event_2","Test event 2")
        self.cf.event_id_dict.add_event_id("test_event_3","Test event 3")
        
        self.cf.add_reserved_chain_name(["sub_chain_1","sub_chain_2","sub_chain_3","sub_chain_4"])
        self.cf.define_chain("top_level_chain",auto_flag=True)
        self.op.asm_log_message("\n\nStarting top level chain")
        self.op.asm_enable_chains(chain_list = ["sub_chain_1","sub_chain_2"])
        self.op.asm_wait_time(3.0)
        self.op.asm_disable_chains(chain_list = ["sub_chain_1","sub_chain_2"])
        self.op.asm_log_message("sub_chain_1 and sub_chain_2 disabled\n\n")
        self.op.asm_log_message("sub_chain_3 enabled\n\n")
        self.op.asm_enable_chains(chain_list = ["sub_chain_3"])
        self.op.asm_wait_time(3.0)
        self.op.asm_disable_chains(chain_list = ["sub_chain_3"])
        self.op.asm_log_message("sub_chain_3 disabled\n\n")
        self.op.asm_log_message("sub_chain_4 enabled\n\n")
        self.op.asm_enable_chains(chain_list = ["sub_chain_4"])
        self.op.asm_wait_time(3.0)
        self.op.asm_disable_chains(chain_list = ["sub_chain_1","sub_chain_2"])
        self.op.asm_join_chains(chain_list = ["sub_chain_4"])
        self.op.asm_log_message("sub_chain_4 joined\n\n")
        self.op.asm_log_message("Top level chain complete\n\n")
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("sub_chain_1")
        self.op.asm_log_message("Starting sub chain 1")
        self.op.asm_bidirectional_one_shot_handler(self.initialization_one_shot_handler,self.termination_one_shot_handler,"chain 1 bidirectional test data")        
        self.op.asm_one_shot_handler(self.output_one_shot_handler,"chain 1 one shot test data")
        self.op.asm_event_filter(event_list = ["test_event_1","test_event_2","test_event_3"])
        self.op.asm_wait_time(1.0)
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("sub_chain_2")
        self.op.asm_log_message("Starting sub chain 2")
        self.op.asm_event_filter(event_list = ["test_event_1","test_event_2","test_event_3"])
        self.op.asm_send_system_event(event_id = "test_event_1",event_data = "test event 1 data")
        self.op.asm_send_named_event(chain_name = "sub_chain_2",event_id = "test_event_2",event_data = "test event 2 data")
        self.op.asm_send_named_event(chain_name = "sub_chain_2",event_id = "test_event_3",event_data = "test event 3 data")
        
        self.op.asm_send_named_event(chain_name = "sub_chain_1",event_id = "test_event_2",event_data = "test event 2 data")
        self.op.asm_send_named_event(chain_name = "sub_chain_1",event_id = "test_event_3",event_data = "test event 3 data")
        self.op.asm_wait_time(1.0)
        self.op.asm_halt()
        self.cf.end_chain()
        
        self.cf.define_chain("sub_chain_3")
        self.op.asm_log_message("Starting sub chain 3")
        
        self.op.asm_enable_disable_chains(chain_list = ["sub_chain_1","sub_chain_2"])
        self.op.asm_halt()
        self.cf.end_chain()
        
        self.cf.define_chain("sub_chain_4")
        self.op.asm_log_message("Starting sub chain 4")
        self.op.asm_enable_chains(chain_list = ["sub_chain_1","sub_chain_2"])
        self.op.asm_join_chains(chain_list = ["sub_chain_1","sub_chain_2"])
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Basic tests complete\n\n")
        
    def monitor_system_reset(self,data):
         self.reset_count += 1
         print("reset count for system reset test",self.reset_count)
         time.sleep(1)
         if self.reset_count > 1:
             exit()
    
    def test_system_reset(self):
        self.cf.reset_cf()
        self.reset_count = 0
        self.cf.define_chain("test_system_reset",auto_flag=True)
        self.op.asm_log_message("Starting test system reset")
        self.op.asm_one_shot_handler(self.monitor_system_reset, "monitor system reset")
        self.op.asm_reset_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("System reset test complete\n\n")
        
        
        
        
    