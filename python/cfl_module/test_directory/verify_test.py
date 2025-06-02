
import time


def true_fn(fn_data,event):
    return True

def false_fn(fn_data,event):
    print("false_fn".fn_data,event)
    return False

class CF_Verify_Test():
    def __init__(self,cf,op):  #op is opcodes object
        self.cf = cf
        self.op = op
        self.test_sequence_dict = {}
        self.test_sequence_dict["verify_test_pass"] = self.verify_test_pass
        self.test_sequence_dict["verify_test_fail_reset"] = self.verify_test_fail_reset
        self.test_sequence_dict["verify_test_fail_terminate"] = self.verify_test_fail_terminate
        self.test_sequence_dict["verify_test_timeout_reset"] = self.verify_test_timeout_reset
        self.test_sequence_dict["verify_test_timeout_terminate"] = self.verify_test_timeout_terminate
        
    def run_test_sequence(self,test_sequence_name):
      
        if test_sequence_name in self.test_sequence_dict:
            print("\n\nrunning test sequence",test_sequence_name)
            self.test_sequence_dict[test_sequence_name]()
            print("end of test sequence\n\n",test_sequence_name)
        
        else:
            raise ValueError(f"Test sequence {test_sequence_name} not found")
        
        
    def run_all_test_sequences(self):
        
        for test_sequence_name in self.test_sequence_dict:        
            self.run_test_sequence(test_sequence_name)
    

    
    def verify_test_pass(self):
        print("starting verify_test_pass")
        self.cf.reset_cf()
        self.cf.define_chain("end_test",auto_flag=True)
        self.op.asm_wait_time(10.0)
        self.op.asm_terminate_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("verify_test",auto_flag=True)
        self.op.asm_log_message("Starting verify test")
        self.op.asm_verify(verify_fn = true_fn)
        self.op.asm_wait_time(1.0)
        self.op.asm_halt()
        self.cf.end_chain()
        self.cf.finalize()
        self.cf.cf_engine_start()
        
        print("verify_test_pass complete\n\n")
    
    def verify_test_fail_reset(self):
        print("starting verify_test_fail_reset")
        self.cf.reset_cf()
        self.define_chain("end_test",auto_flag=True)
        self.op.asm_wait_time(10.0) # 10 seconds time out
        self.op.asm_terminate_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("verify_test",auto_flag=True)
        self.op.asm_log_message("Starting verify test")
        self.op.asm_time_delay(1.0)
        self.op.asm_verify(verify_fn = false_fn, fn_data = "test_data", reset_flag =True)
        self.op.asm_halt()
        self.cf.end_chain()
        self.cf.finalize()
        self.cf.cf_engine_start()
    
        print("verify_test_fail_reset complete\n\n")
    
    def verify_test_fail_terminate(self):
        print("starting verify_test_fail_terminate")
        self.cf.reset_cf()
        
        self.cf.define_chain("verify_test",auto_flag=True)
        self.op.asm_log_message("Starting verify test")
        self.op.asm_verify(verify_fn = false_fn, fn_data = "test_data", reset_flag =False)
        self.op.asm_wait_time(1.0)
        self.op.asm_halt()
        self.cf.end_chain()
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("verify_test_fail_terminate complete\n\n")
    
    def verify_test_timeout_reset(self):
        print("starting verify_test_timeout_reset")
            
        self.cf.reset_cf()
        self.define_chain("end_test",auto_flag=True)
        self.op.asm_wait_time(10.0)             #10 seconds time out
        self.op.asm_terminate_system()
        self.op.asm_terminate()
        self.cf.end_chain()
        
        self.cf.define_chain("verify_test_fail_time_out_terminate",auto_flag=True)
        self.op.asm_log_message("Starting verify test")
        self.op.asm_verify(verify_fn = true_fn,  reset_flag = True,timeout = 10.0) # time out is 1.0 seconds 
        self.op.asm_halt()
        self.cf.end_chain()   
        self.cf.finalize()
        self.cf.cf_engine_start()     
        
        print("verify_test_timeout_reset complete\n\n")
    
    def verify_test_timeout_terminate(self):
        print("starting verify_test_timeout_terminate")
        self.cf.reset_cf()
        self.cf.define_chain("verify_test_fail_time_out_terminate",auto_flag=True)
        self.op.asm_log_message("Starting verify test")
        self.op.asm_verify(verify_fn = true_fn,  reset_flag = False,timeout = 50.0) # time out is 5.0 seconds 
        self.op.asm_halt()
        self.cf.end_chain()
        self.cf.finalize()
        self.cf.cf_engine_start()
        print("verify_test_timeout_terminate complete\n\n")
    

    
    
    