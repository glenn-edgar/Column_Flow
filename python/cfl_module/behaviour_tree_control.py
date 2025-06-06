from behavior_tree_data import FullLtreeStorage


class Behavior_Tree_Control(FullLtreeStorage):
    def __init__(self,cf):
        FullLtreeStorage.__init__(self)
        self.cf = cf
        self.path_list = []
        self.chain_list = []
        self.chain_data = {}
        self.chain_data_path = {}
        
    
    def add_composite_element(self, chain_name, data ):
        if chain_name in self.chain_list:
            raise ValueError(f"Chain {chain_name} already exists")
        self.chain_list.append(chain_name)
        self.path_list.append(chain_name)
        path_string = ".".join(self.path_list)
        self.chain_data_path[chain_name] = path_string
        self.chain_data[chain_name] = data
        self.store(path_string, data)
        return path_string
    
   
    
    def leave_composite_element(self):
        self.path_list.pop()
    
    def add_leaf_element(self, chain_name, data ):
        if chain_name  in self.chain_list:
            raise ValueError(f"Chain {chain_name} already exists")
        self.path_list.append(chain_name)
        self.chain_list.append(chain_name)
        path_string = ".".join(self.path_list)
        self.chain_data_path[chain_name] = path_string
        self.chain_data[chain_name] = data
        self.store(path_string, data)
        self.path_list.pop()
        return path_string
        
    
    def get_chain_data(self, chain_name):
        return self.chain_data[chain_name]
    
    def get_chain_data_path(self, chain_name):
        return self.chain_data_path[chain_name]
    
    def store_chain_data(self, chain_name, data):
        self.chain_data[chain_name] = data
        self.store(self.chain_data_path[chain_name], data)
        
    
    def get_chain_list(self):
        return self.chain_list
    
    def finalize(self):
        if len(self.path_list) > 0:
            raise ValueError("Path list is not empty")
        
    
if __name__ == "__main__":
    from chain_flow import ChainFlow
    def tick():
        pass
    cf = ChainFlow(tick)
    bc = Behavior_Tree_Control(cf)
    bc.add_composite_element("chain1", "data1")
    bc.add_leaf_element("chain2", "data2")
    bc.leave_composite_element()
    print(bc.get_chain_data("chain1"))
    print(bc.get_chain_list())
    print(bc.get_chain_data_path("chain1"))
    bc.finalize()
    
    
    

    
         