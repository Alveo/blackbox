from config import configinit, config
import wx
import os
from explorer.mainexplorerframe import MainExplorerFrame

def main():     
    app = wx.App(False)  # Create a new app, don't redirect stdout/stderr to a window.
    
    # Get the start path from the config file
    configinit()
    initial_path = config('PATH_RECORDINGS')
    
    if not os.path.exists(initial_path):
        initial_path = ""
    
    MainExplorerFrame(initial_path, None, "Austalk Explorer") # A Frame is a top-level window.
    app.MainLoop()
    
if __name__ == "__main__":
    main()
    
    