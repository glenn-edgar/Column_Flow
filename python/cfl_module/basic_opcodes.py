
from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event_id_dict
from cf_events import Event
class Basic_Opcodes(Support_Functions):
  def __init__(self,cf):
      self.cf = cf
      self.support_functions = Support_Functions(cf)
      self.event_id_dict = Event_id_dict()
 
  def null_function(self,element_data,event):
      return "CF_DISABLE"

  def exec_wait_to_chain_completion(self,element_data,event):
      if event.event_index == "CF_TIMER_EVENT":
        chain_list = element_data['data']
        for chain_name in chain_list:
          if self.cf.chain_dict[chain_name].active == True:
            return "CF_HALT"
        return "CF_DISABLE"
      else:
        return "CF_HALT"
      
  def exec_enable_chains(self,element_data,event):
    chain_list = element_data['data']
    for chain_name in chain_list:
      self.cf.enable_chain(chain_name)
  
  def exec_disable_chains(self,element_data,event):
    chain_list = element_data['data']
    for chain_name in chain_list:
      self.cf.disable_chain(chain_name)
  
  
  def exec_output_fn(self,element_data):
    message = element_data['data']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
  def exec_op_code_return_code(self,element_data,event):
    return element_data['data']
    

  def asm_one_shot_handler(self,one_shot_fn,one_shot_data,one_shot_name = None):
     self.cf.add_element(process_function=self.null_function,
                         initialization_function=one_shot_fn,
                         termination_function=None,
                         data=one_shot_data, name=one_shot_name)
  
  def asm_bidirectional_one_shot_handler(self,one_shot_fn,termination_fn,one_shot_data,one_shot_name = None):
     self.cf.add_element(process_function=self.null_function,
                         initialization_function=one_shot_fn,
                         termination_function=termination_fn,
                         data=one_shot_data, name=one_shot_name)
  
  def asm_log_message(self,message,name = None):
    
    if type(message) is not str:
      raise TypeError("message must be a string")
    self.asm_one_shot_handler(self.exec_output_fn,message,name)


  def asm_reset(self,name = None):
    self.cf.add_element(process_function=self.exec_op_code_return_code,
                        initialization_function=None,
                        termination_function=None,
                        data="CF_RESET", name=name)

  def asm_terminate(self,name = None):
    self.cf.add_element(process_function=self.exec_op_code_return_code,
                        initialization_function=None,
                        termination_function=None,
                        data="CF_TERMINATE", name=name)
    
  def asm_halt(self,name = None):
    self.cf.add_element(process_function=self.exec_op_code_return_code,
                        initialization_function=None,
                        termination_function=None,
                        data="CF_HALT", name=name)
    
  def asm_terminate_system(self,name = None):
    self.asm_send_system_event("CF_TERMINATE_SYSTEM",None,name)
    
  def asm_reset_system(self,name = None):
    self.asm_send_system_event("","CF_RESET_SYSTEM",name)
   
  def exec_send_system_event(self,element_data):
  
    self.cf.send_system_event(element_data['data'])
   
  def asm_send_system_event(self,event_id,event_data=None,name = None):
     event = Event(event_id,event_data)
     self.asm_one_shot_handler(self.exec_send_system_event,event,name)
  
  def exec_send_named_event(self,element_data,event):
    print("element_data",element_data['data'])
    event = element_data['data']
    self.cf.send_named_event(self,element_data["chain_name"],event)
  
  def asm_send_named_event(self,chain_name,event_id,event_data=None,name = None):
    event = Event(event_id,event_data)
    self._check_for_valid_chain_name(chain_name)
    self.asm_one_shot_handler(self.exec_send_named_event,{"event":event,"chain_name":chain_name},name)
  
    
    
  
  
  
  def exec_set_column_state(self,element_data,event):
    if type(element_data) is not int:
        raise TypeError("state must be a boolean")
    self.cf.set_column_state(element_data)
    
  def asm_set_column_state(self,state):
      self.asm_one_shot_handler(self.exec_set_column_state,state,"Set_Column_State")
    
  
  
 
  def asm_enable_chains(self,chain_list,name = None):
    
    self._check_for_valid_chains(chain_list)
    self.cf.one_shot_handler(self.exec_enable_chains,chain_list,name)
    
  def asm_disable_chains(self,chain_list,name = None):
    
    self._check_for_valid_chains(chain_list)
    self.cf.one_shot_handler(self.exec_disable_chains,chain_list,name)
    
   
  def asm_enable_disable_chains(self,chain_list,name = None):
    self._check_for_valid_chains(chain_list)
    self.add_bidirectional_one_shot_handler(self.exec_enable_chains,self.exec_disable_chains,chain_list,name)

  def asm_enable_wait_chains(self,chain_list,name = None):
    self._check_for_valid_chains(chain_list)

    self.add_element(process_function=self.exec_wait_to_chain_completion,
                     initialization_function= self.exec_enable_chains,
                     termination_function= self.exec_disable_chains,
                     data=chain_list, name=name)
  
  def asm_join_chains(self,chain_list,name = None):
    self._check_for_valid_chains(chain_list)
    
    self.add_element(process_function=self.exec_wait_to_chain_completion,
                     initialization_function= None,
                     termination_function= self.exec_disable_chains,
                     data=chain_list, name=name)
  
  



