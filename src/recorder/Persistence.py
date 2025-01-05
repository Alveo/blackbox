
from Const import *
from Domain import *
from session_config import *
import string

def ComponentName(cid):
    """Given a component id, return the verbose name of the component
    or "Unknown Component" if we can't find it"""

    # id should be an integer
    if type(cid) == unicode:
        try:
            cid = string.atoi(cid)
        except:
            # we can't find it if it's not an integer
            return "Unknown Component"

    comp =  Component.GetInstance(int(cid))
    if comp is not None:
        return comp.GetName()

    return "Unknown Component"

def ItemPrompt(cid, itemid):
    """Given a component id and an item id (both integers), return the prompt text for the item"""
    
    comp =  Component.GetInstance(int(cid))
    if comp == None or int(itemid) > len(comp):
        return "UNKNOWN PROMPT"

    return comp[int(itemid)].GetPrompt()

