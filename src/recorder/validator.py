import re

from collections import namedtuple
from datahandling.RecordedSession import RecordedSession
from recorder.session_config import sessions

# Define our named tuples, we use these structures in-order to decouple
# the validation routines from the structures used to process the actual
# data.
SessionNT = namedtuple('SessionNT', ['id', 'components'], verbose = False)
ComponentNT = namedtuple('ComponentNT', ['id', 'items'], verbose = False)
ItemNT = namedtuple('ItemNT', ['id'], verbose = False)


class Validator(object):
    

    def get_ideal_view(self, base_name):
        """ This method loads the ideal model state using the session configuration information. This
        state includes the Session, Component and Items. """
        
        return_dict = {}
        session_id = self.extract_session_id(base_name)
        
        if session_id is None:
            return return_dict
        
        for session in sessions:
            sessionNT = SessionNT(id = str(session.GetId()), components = [])
            comp = session.firstComponent()
            
            while comp != False:
                comp.LoadItems()
                compNT = ComponentNT(str(comp.GetId()), items = [])
                sessionNT.components.append(compNT)
                for item in comp.getItems():
                    itemNT = ItemNT(str(item.GetId()))
                    compNT.items.append(itemNT)
                
                comp = session.getNextComponent()
            
            if sessionNT.id == session_id: 
                return_dict[session_id] = sessionNT 
        
        return return_dict
    

    def get_manifest_view(self, manifest_path, base_name):
        """ This method takes a manifest file and constructs a structure representative of the munged list """
        
        munged_list = self.__load_manifest__(manifest_path, base_name)
        return self.__convert_mungedlist__(munged_list)

    
    def get_actual_view(self, manifest_path, base_name):
        """ This method generates an in-memory manifest file which is used to construct
        a view of what the output currently looks like."""
        
        munged_list = self.__gen_manifest__(manifest_path, base_name)
        return self.__convert_mungedlist__(munged_list)
    
    
    def extract_session_id(self, base_name):
        """ This method extracts the session id from the base folder name. It is a duplicate
        of the parse_basename_into_properties method in RecordedSession. We had to duplicate
        it because that particular method could not be re-used """
        
        parse_it = re.compile(r'Spkr(\d*)_(\d*)_Session([1234ab]+)')
        match = parse_it.search(base_name)
        if match:
            groups = match.groups()
            return groups[2]
        
        return None
    
    
    def __add_component_to_session(self, session, component_id):
        """ Adds a component to a session if the session does not have the component """
        components = filter(lambda component: component.id == component_id, session.components)
        if len(components) == 0:
            session.components.append(ComponentNT(id = component_id, items = [])) 
    
     
                
    def __add_item_to_component(self, component, item_id):
        """ Adds an item to a component if the component does not have the item """
        items = filter(lambda item: item.id == item_id, component.items)
        if len(items) == 0:
            component.items.append(ItemNT(id = str(int(item_id))))
        
        
    def __convert_mungedlist__(self, munged_list):
        """ Iterate through each item in the list and construct a structure representative of 
        what is in the manifest """
        sessions = {}
        
        for item in munged_list:
            item_split_vals = item.split('_')
            session_id = item_split_vals[2]
            
            if sessions.has_key(session_id) == False:
                session = SessionNT(id=session_id, components=[])
                sessions[session_id] = session
            else:
                session = sessions[session_id]
                
            self.__add_component_to_session(session, item_split_vals[3])
            
            for component in session.components:
                if component.id == item_split_vals[3]:
                    self.__add_item_to_component(component, item_split_vals[4])
                    
                         
        return sessions
    
                    
    def __gen_manifest__(self, manifest_path, base_name):
        """ This generates a dynamic manifest file without writing the manifest to disk, this
        method then uses the dynamically generated manifest to return a list of what
        the disk structure looks like, i.e. the real view """
        
        rs = RecordedSession(manifest_path, base_name)
        lines = rs.gen_manifest(True, None, False)
        
        result = []

        for line in lines.split('\n'):
            if not line.startswith("@") and not len(line.strip()) == 0:
                result.append(line.strip())
       
        return result
    
    
    def __load_manifest__(self, manifest_path, base_name):
        """ This method loads the manifest and constructs an alternative structure of Session, Component and Item """
        rs = RecordedSession(manifest_path, base_name)
        return rs.read_manifest()
