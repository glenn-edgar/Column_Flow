
import time
class CF_Wait_Test():
    def __init__(self,cf,op):  #op is opcodes object
        self.cf = cf
        self.op = op
        self.test_sequence_dict = {}
        self.test_sequence_dict["test_wait_delay"] = self.test_wait_delay
        self.test_sequence_dict["test_wait_for_event_pass"] = self.test_wait_for_event_pass
        self.test_sequence_dict["test_wait_for_event_fail_reset"] = self.test_wait_for_event_fail_reset
        self.test_sequence_dict["test_wait_for_event_fail_terminate"] = self.test_wait_for_event_fail_terminate
    
        
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
        
    
    
    def test_wait_delay(self):
         print("\n\ntest_wait_delay")
         self.cf.reset_cf()
         self.cf.define_chain("wait_delay_test",auto_flag=True)
         self.op.asm_log_message("Starting 10 second delay")
         self.op.asm_wait_time(10.0)
         self.op.asm_log_message("--------------------------------> terminate event sent")
         self.op.asm_terminate()
         self.cf.end_chain()
         #system terminates because no active chains
         self.cf.finalize()
         self.cf.cf_engine_start()
         print("Wait delay test complete\n\n")
         
    def test_wait_for_event_pass(self):
         print("\n\ntest_wait_for_event_pass")
         self.cf.reset_cf()
         self.cf.define_chain("wait_for_event_pass_test",auto_flag=True)
         self.op.asm_log_message("Starting wait for event pass test")
         self.op.asm_wait_for_event(event_id = "CF_SECOND_EVENT",event_count = 10)
         self.op.asm_log_message("Wait for event pass test complete")
         self.op.asm_terminate()
         self.cf.end_chain()
         #system terminates because no active chains
         
         self.cf.finalize()
         self.cf.cf_engine_start()
         print("Wait for event pass test complete\n\n")
    
    
    def test_wait_for_event_fail_reset(self):
        print("\n\ntest_wait_for_event_fail_reset")
        self.cf.reset_cf()
        self.cf.define_chain("terminate_program",auto_flag=True)
        self.op.asm_log_message("Starting terminate program")
        self.op.asm_wait_time(25.0)
        self.op.asm_log_message("--------------------------------> terminate system")
        self.op.asm_terminate_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        
        self.cf.define_chain("wait_for_event_fail_reset_test",auto_flag=True)
        self.op.asm_log_message("Starting wait for event fail reset test")
        self.op.asm_wait_for_event(event_id = "CF_SECOND_EVENT",event_count =5,reset_flag = True,timeout = 5,time_out_event = "CF_TIMER_EVENT",
                                   error_fn = self.log_error_message, error_data = "Error not received within timeout")
        self.op.asm_log_message("this message should not be printed")
        self.op.asm_terminate()
        self.cf.end_chain()
        #system terminates because no active chains
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Wait for event fail reset test complete\n\n")
        
        
    
    def test_wait_for_event_fail_terminate(self):
        print('starting test_wait_for_event_fail_terminate')
        print("\n\ntest_wait_for_event_fail_terminate")
        self.cf.reset_cf()
        self.cf.define_chain("wait_for_event_fail_terminate_test",auto_flag=True)
        self.op.asm_log_message("Starting wait for event fail terminate test")
        self.op.asm_wait_for_event(event_id = "CF_SECOND_EVENT",event_count =1000,reset_flag = False,timeout = 50,
                                   error_fn = self.log_error_message, error_data = "terminating chain")
        self.op.asm_log_message("this message should not be printed")
        self.op.asm_terminate()
        self.cf.end_chain()
        #system terminates because no active chains
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("Wait for event fail terminate test complete\n\n")
        