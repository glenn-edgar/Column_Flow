
from .wait_test import CF_Wait_Test
from .verify_test import CF_Verify_Test
class CFL_test_driver:
    def __init__(self,cf,op):
        self.cf = cf
        self.op = op
        self.cf_wait_test = CF_Wait_Test(cf,op)
        self.cf_verify_test = CF_Verify_Test(cf,op)
        self.test_sequence_dict = {}
        self.test_sequence_dict["wait"] = self.cf_wait_test
        self.test_sequence_dict["verify"] = self.cf_verify_test
        
    def list_test_sequences(self):
        return self.test_sequence_dict
    
    def run_test_sequence(self,test_sequence_name,test_id = None):
        if test_id is None:
            self.test_sequence_dict[test_sequence_name].run_all_test_sequences()
        else:
            self.test_sequence_dict[test_sequence_name].run_test_sequence(test_id)
        

        
        
        
