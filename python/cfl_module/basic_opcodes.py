
from datetime import datetime
from asm_support_functions import Support_Functions
from cf_events import Event_id_dict
from cf_events import Event
class Basic_Opcodes(Support_Functions):
  def __init__(self,cf):
      self.cf = cf
      self.support_functions = Support_Functions(cf)
      self.event_id_dict = Event_id_dict()
 
      
      
  def null_function(self,element_data,event=None):
      return "CF_DISABLE"

  def null_function_continue(self,element_data,event=None):
      return "CF_CONTINUE"
  
 
      
 
  
  def exec_output_fn(self,element_data,event=None):
    message = element_data['data']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")
    
  def exec_event_filter_fn(self,element_data,event):
    
    chain_name = element_data['current_chain']
    event_list = element_data['data']
    for event_id in event_list:
      if event.event_id == event_id:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {chain_name} {event.event_id} event received")  
        
    return "CF_CONTINUE"
    
  def exec_op_code_return_code(self,element_data,event=None):
    return element_data['data']
    
  def asm_event_filter(self,event_list,name = None):
    self.cf.add_element(process_function=self.exec_event_filter_fn,
                        initialization_function=None,
                        termination_function=None,
                        data=event_list, name=name)


  def asm_one_shot_handler(self,one_shot_fn,one_shot_data,name = None):
     self.cf.add_element(process_function=self.null_function,
                         initialization_function=one_shot_fn,
                         termination_function=None,
                         data=one_shot_data, name=name)
  
  def asm_bidirectional_one_shot_handler(self,one_shot_fn,termination_fn,one_shot_data,name = None):
     self.cf.add_element(process_function=self.null_function_continue,
                         initialization_function=one_shot_fn,
                         termination_function=termination_fn,
                         data=one_shot_data, name=name)
  
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
    self.asm_send_system_event("CF_RESET_SYSTEM",name)
   
  def exec_send_system_event(self,element_data):
  
    self.cf.send_system_event(element_data['data'])
   
  def asm_send_system_event(self,event_id,event_data=None,name = None):
     event = Event(event_id,event_data)
     
     self.asm_one_shot_handler(self.exec_send_system_event,event,name)
  
  def exec_send_named_event(self,data):
    element_data = data["data"]

    event = element_data["event"]
    chain_name = element_data["chain_name"]
  
    self.cf.send_named_queue_event(chain_name,event)
  
  def asm_send_named_event(self,chain_name,event_id,event_data=None,name = None):
    event = Event(event_id,event_data)
    self._check_for_valid_chain_name(chain_name)
    self.asm_one_shot_handler(self.exec_send_named_event,{"event":event,"chain_name":chain_name},name)
  
    
    
  

    
    def wait_for_chain_list_to_complete(self,chain_list, bool_fn = None,match_list = None,number_of_chains = None):
        outcome_list = []
        for chain_name in chain_list:
            if self.is_chain_active(chain_name) == True:
                outcome_list.append(False)
            else:
                outcome_list.append(True)
        if bool_fn is not None:
            return bool_fn(outcome_list,match_list,number_of_chains)
        else:
            return self.chain_termination_all(outcome_list,match_list,number_of_chains) 
  
 
    def exec_wait_to_chain_completion(self,element_data,event):
      if event.event_id == "CF_TIMER_EVENT":
        if "filter_fn" not in element_data['data']:
          element_data['data']['filter_fn'] = None
        if "match_list" not in element_data['data']:
          element_data['data']['match_list'] = None
        if "number_of_chains" not in element_data['data']:
          element_data['data']['number_of_chains'] = None
        chain_list = element_data['data']
        filter_fn = element_data['data']['filter_fn']
        match_list = element_data['data']['match_list']
        number_of_chains = element_data['data']['number_of_chains']
        if self.cf.wait_for_chain_list_to_complete(chain_list,filter_fn,match_list,number_of_chains) == True:
            return "CF_HALT"
        else:
            return "CF_DISABLE"
      else:
        return "CF_HALT" 
  
  def exec_enable_chains(self,element_data):
    chain_list = element_data['data']["chain_list"]
    print('enable chains',chain_list)
    for chain_name in chain_list:
      print('enable chain',chain_name)
      self.cf.enable_chain(chain_name)
  
  def exec_disable_chains(self,element_data):
    chain_list = element_data['data']["chain_list"]

    for chain_name in chain_list:
      self.cf.disable_chain(chain_name)
      
  
 
  def asm_enable_chains(self,chain_list,name = None):
  
    self._check_for_valid_chains(chain_list)
    self.asm_one_shot_handler(self.exec_enable_chains,{"chain_list":chain_list},name)
    
  def asm_disable_chains(self,chain_list,name = None):
    
    self._check_for_valid_chains(chain_list)
    self.cf.add_element(process_function=self.null_function,
                        initialization_function=self.exec_disable_chains,
                        termination_function=self.exec_disable_chains,
                        data={"chain_list":chain_list}, name=name)
          
   
  def asm_enable_disable_chains(self,chain_list,name = None):
    self._check_for_valid_chains(chain_list)
    self.cf.add_element(process_function=self.null_function,
                        initialization_function=self.exec_enable_chains,
                        termination_function=self.exec_disable_chains,
                        data={"chain_list":chain_list}, name=name)
  
  def exec_exception_handler_init(self,element_data,event=None):
    print('event_data',element_data)
    event_list = element_data['data']['event_list']
    count = element_data['data']['count']
    bool_fn = element_data['data']['bool_fn']
    bool_data = element_data['data']['bool_data']
    chain_list = element_data['data']['chain_list']
    element_data['data']['event_count'] = 0
    if bool_fn is not None:
      bool_fn(bool_data,"CF_INIT_EVENT")
    
  def exec_exception_handler(self,element_data,event):
    event_list = element_data['data']['event_list']
    count = element_data['data']['count']
    bool_fn = element_data['data']['bool_fn']
    bool_data = element_data['data']['bool_data']
    chain_list = element_data['data']['chain_list']
    event_count = element_data['data']['event_count']
    failure_fn = element_data['data']['failure_fn']
    failure_data = element_data['data']['failure_data']
    reset_flag = element_data['data']['reset_flag']
    if failure_fn is  None:
      failure_fn = self.exec_output_fn
    if failure_data is  None:
      failure_data = {"data": "CF_EXCEPTION_HANDLER_FAILURE"}
   
    if event.event_id in event_list:
    
      event_count += 1
      
      element_data['data']['event_count'] += 1
      if event_count >= count:
        for chain_name in chain_list:
          self.cf.disable_chain(chain_name)
       
        failure_fn(failure_data)
        if reset_flag == True:
          for chain_name in chain_list:
            self.cf.enable_chain(chain_name)
        return "CF_DISABLE"
    
    if bool_fn is not None:
          if bool_fn(bool_data,event) == False:
            self.cf.disable_chain(chain_list)
            failure_fn(failure_data)
            if reset_flag == True:
              for chain_name in chain_list:
                self.cf.enable_chain(chain_name)
            return "DISABLE"
          else:
            return "CF_CONTINUE"
    else:
      return "CF_CONTINUE"
    
  def exec_exception_termination(self,element_data,event=None):
    bool_fn = element_data['data']['bool_fn']
    bool_data = element_data['data']['bool_data']
    chain_list = element_data['data']['chain_list']
    if bool_fn is not None:
      bool_fn(bool_data,"CF_TERMINATE")
    for chain_name in chain_list:
      self.cf.disable_chain(chain_name)
    

  def asm_exception_handler(self,event_list,count,bool_fn,bool_data,chain_list,failure_fn = None,failure_data = None,reset_flag = False,name = None):
      if chain_list is not None:
        self._check_for_valid_chains(chain_list)
        termination_function = self.exec_exception_termination
      else:
        termination_function = self.null_function
      if type(count) is not int:
        raise TypeError("count must be an integer")
      if bool_fn is not None and type(bool_fn) is not function:
        raise TypeError("bool_fn must be a function")
      if type(event_list) is not list:
        raise TypeError("event_list must be a list")
      if failure_fn is not None and type(failure_fn) is not function:
        raise TypeError("failure_fn must be a function")
      if type(reset_flag) is not bool:
        raise TypeError("reset_flag must be a boolean")
    
      element_data = {"event_list":event_list,"count":count,"bool_fn":bool_fn,"bool_data":bool_data,"chain_list":chain_list,
                      "failure_fn":failure_fn,"failure_data":failure_data,"reset_flag":reset_flag}
      self.cf.add_element(process_function=self.exec_exception_handler,
                        initialization_function=self.exec_exception_handler_init,
                        termination_function=termination_function,
                        data=element_data, name=name)
      
      
  def exec_join_or(self,element_data,event=None):
    if event.event_id is not "CF_TIMER_EVENT":
      return "CF_HALT"
    chain_list = element_data['data']['chain_list']
    match_list = element_data['data']['match_list']
    for chain_name in chain_list:
      active = self.cf.is_chain_active(chain_name)
      if active == True:
        for chain_name in chain_list:
          self.cf.disable_chain(chain_name)
        return "CF_DISABLE"
      
    return "CF_CONTINUE"
      
      
      
 
  def asm_chain_join_or(self,chain_list,match_list=None,name = None):
    if match_list is not None and type(match_list) is not list:
      raise TypeError("match_list must be a list")
    if match_list is  None:
      match_list = chain_list
    if type(chain_list) is not list:
      raise TypeError("chain_list must be a list")
    self._check_for_valid_chains(chain_list)
    for match_item in match_list:
      if match_item not in chain_list:
        raise ValueError(f"match_item {match_item} not in chain_list")
        
    element_data = {"chain_list":chain_list,"match_list":match_list}
    self.cf.add_element(process_function=self.exec_join_or,
                        initialization_function=self.null_function,
                        termination_function=self.null_function,
                        data=element_data, name=name)
    
  def exec_join_and(self,element_data,event=None):
    if event.event_id is not "CF_TIMER_EVENT":
      return "CF_HALT"
    chain_list = element_data['data']['chain_list']
    match_list = element_data['data']['match_list']
    for chain_name in chain_list:
        active = self.cf.is_chain_active(chain_name)
        if active == True:
          return "CF_DISABLE"
        
    return "CF_CONTINUE"
        
              
    
  def asm_chain_join_and(self,chain_list,match_list = None,name = None):
      
      if match_list is not None and type(match_list) is not list:
        raise TypeError("match_list must be a list")
      if match_list is None:
        match_list = chain_list
      if type(chain_list) is not list:
        raise TypeError("chain_list must be a list")
      self._check_for_valid_chains(chain_list)
      for match_item in match_list:
        if match_item not in chain_list:
          raise ValueError(f"match_item {match_item} not in chain_list")
          
      element_data = {"chain_list":chain_list,"match_list":match_list}
      self.cf.add_element(process_function=self.exec_join_and,
                          initialization_function=self.null_function,
                          termination_function=self.null_function,
                          data=element_data, name=name)  


    
  def exec_join_match_n_out_of_m_init(self,element_data,event=None):
    element_data['data']['match_count'] = 0
    
  def exec_join_match_n_out_of_m_termination(self,element_data,event=None):
    chain_list = element_data['data']['chain_list']
    for chain_name in chain_list:
      self.cf.disable_chain(chain_name)
      
  def exec_join_match_n_out_of_m(self,element_data,event=None):
    if event.event_id is not "CF_TIMER_EVENT":
      return "CF_HALT"
    chain_list = element_data['data']['chain_list']
    match_list = element_data['data']['match_list']
    match_limit = element_data['data']['match_limit']
    match_count = element_data['data']['match_count']
    for chain_name in chain_list:
      active = self.cf.is_chain_active(chain_name)
      if active == True:
        match_count += 1
        if match_count >= match_limit:
          for chain_name in chain_list:
            self.cf.disable_chain(chain_name)
          return "CF_DISABLE"
        else:
          return "CF_HALT"
        
    return "CF_HALT"
    
      
    
  def asm_chain_join_match_n_out_of_m(self,chain_list,match_list=None,match_limit=1,name = None):
    if match_list is not None and type(match_list) is not list:
      raise TypeError("match_list must be a list")
    if match_list is  None:
      match_list = chain_list
    if type(chain_list) is not list:
      raise TypeError("chain_list must be a list")
    if type(match_limit) is not int:
      raise TypeError("match_limit must be an integer")
    self._check_for_valid_chains(chain_list)
    element_data = {"chain_list":chain_list,"match_list":match_list,"match_limit":match_limit}
    self.cf.add_element(process_function=self.exec_join_match_n_out_of_m,
                        initialization_function = self.exec_join_match_n_out_of_m_init,
                        termination_function = self.exec_join_match_n_out_of_m_termination,
                        data=element_data, name=name)
    

