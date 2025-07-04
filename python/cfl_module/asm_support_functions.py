

class Support_Functions:
  def __init__(self,cf):
      self.cf = cf

 
  def _check_for_valid_chain_name(self,chain_name):
    
      if chain_name not in self.cf.reserved_chain_names:
          raise ValueError(f"Chain name '{chain_name}' is not valid")
      return True

  def _check_for_valid_chains(self,chain_names):
    if type(chain_names) is not list:
        raise TypeError("chain_names must be a list")
    for chain_name in chain_names:
        if chain_name not in self.cf.reserved_chain_names:
            raise ValueError(f"Chain name {chain_name} is not valid")
    return True

  def list_all_asm(self):
    methods = [method for method in dir(self) 
           if method.startswith('asm_') and callable(getattr(self, method))]
    return sorted(methods)
  
  def list_all_exec(self):
    """Return all methods that start with exec_ """
    class_methods = vars(self.__class__)
    
    # Filter for methods that actually start with exec_
    methods = [method for method in class_methods 
                     if method.startswith('exec_') and callable(getattr(self.__class__, method))]
    
    return sorted(methods)
  
  def null_function_disable(self,element_data,event):
    return "CF_DISABLE"
  
  def null_function_continue(self,element_data,event):
    return "CF_CONTINUE"
  
  def null_function_halt(self,element_data,event):
    return "CF_HALT"
  
  def null_function_reset(self,element_data,event):
    return "CF_RESET"
  
  def null_function_terminate(self,element_data,event):
    return "CF_TERMINATE"
  
  