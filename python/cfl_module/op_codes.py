
import time
from basic_opcodes import Basic_Opcodes
from wait import Wait_Opcodes
from verify import Verify_Opcodes
from watch_dog import Watch_Dog_Opcodes
from chain_flow import ChainFlow


class Opcodes(Basic_Opcodes,Wait_Opcodes,Verify_Opcodes,Watch_Dog_Opcodes):
    def __init__(self,cf):
        self.cf = cf
        Basic_Opcodes(self).__init__(cf)
        Wait_Opcodes(self).__init__(cf)
        Verify_Opcodes(self).__init__(cf)
        Watch_Dog_Opcodes(self).__init__(cf)
        self.asm_list = []
        self.asm_dict = {}
        self.exec_list = []
        self.exec_dict = {}
        self.build_asm_list()
        self.build_exec_list()
        
    def _build_and_check_opcode_list(self,call_list, master_call_dict,master_call_list):    
        for opcode in call_list:
            if master_call_dict.get(opcode) is None:
                master_call_dict[opcode] = opcode
                master_call_list.append(opcode)
            else:
                raise ValueError(f"Opcode {opcode} is already defined")
   
   
   
    def build_asm_list(self):
        self._build_and_check_opcode_list(Basic_Opcodes(self).list_all_asm(),self.asm_dict,self.asm_list)
        self._build_and_check_opcode_list(Wait_Opcodes(self).list_all_asm(),self.asm_dict,self.asm_list)
        self._build_and_check_opcode_list(Verify_Opcodes(self).list_all_asm(),self.exec_dict,self.exec_list)
        self._build_and_check_opcode_list(Watch_Dog_Opcodes(self).list_all_asm(),self.exec_dict,self.exec_list)
        
    def build_exec_list(self):
        self._build_and_check_opcode_list(Basic_Opcodes(self).list_all_exec(),self.exec_dict,self.exec_list)
        self._build_and_check_opcode_list(Wait_Opcodes(self).list_all_exec(),self.exec_dict,self.exec_list)
        self._build_and_check_opcode_list(Verify_Opcodes(self).list_all_exec(),self.exec_dict,self.exec_list)
        self._build_and_check_opcode_list(Watch_Dog_Opcodes(self).list_all_exec(),self.exec_dict,self.exec_list)
        
   
    
    def list_opcode_code(self):
        duplicate_check_value = {}
        return_value = []
        basic_opcodes = Basic_Opcodes(self).list_opcode_code()
        for opcode in basic_opcodes:
            if duplicate_check_value.get(opcode) is None:    
                duplicate_check_value[opcode] = opcode
                return_value.append(opcode)
            else:
                raise ValueError(f"Opcode {opcode} is already defined")
        wait_opcodes = Wait_Opcodes(self).list_opcode_code()
        for opcode in wait_opcodes:
            if duplicate_check_value.get(opcode) is None:    
                duplicate_check_value[opcode] = opcode
                return_value.append(opcode)
            else:
                raise ValueError(f"Opcode {opcode} is already defined")
        return return_value
    
if __name__ == "__main__":
    def time_tick():
        time.sleep(.1)
        return 0.1,time.time()
    cf = ChainFlow(time_tick)
    op_codes = Opcodes(cf)
    print(op_codes.asm_list)
    print(op_codes.exec_list)
    
    from test_directory.wait_test import CF_Wait_Test
    cf_wait_test = CF_Wait_Test(cf,op_codes)
    cf_wait_test.test_wait_delay()
    cf_wait_test.test_wait_for_event_pass()
    cf_wait_test.test_wait_for_event_fail_reset()
    cf_wait_test.test_wait_for_event_fail_terminate()
    
    
    
  