import wx

from sessionnavigation import SessionNavigation
from propertywindow import PropertyWindow

class MainExplorerFrame(wx.Frame):
    
    def __init__(self, initialPath, parent, title):
        
        # Initialise frame
        # We are using default sizes for the frames signified by the -1, -1
        wx.Frame.__init__(self, parent, title=title, size=(900, 700))
        self.Show(True)
        
        # Create the splitter window.
        splitter = wx.SplitterWindow(self, style=wx.SP_3D)
        splitter.SetMinimumPaneSize(1)

        self.expTree = SessionNavigation(splitter, initialPath)

        # Create the editor on the right.
        self.editor = PropertyWindow(self.expTree, splitter, style=wx.TE_MULTILINE)      

        # Add a status bar to the bottom of the primary frame
        self.CreateStatusBar()
        
        # Setting up the menu
        fileMenu = wx.Menu()
        helpMenu = wx.Menu()
        menuSelectDir = fileMenu.Append(wx.ID_FILE, "&Select Directory", "Select Starting Point")
        menuExit = fileMenu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")
        menuAbout = helpMenu.Append(wx.ID_ABOUT, "&About", " Information about this program")
        
        # Creating the menuBar
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")
        
        self.SetMenuBar(menuBar)

        # Set event handlers
        self.Bind(wx.EVT_MENU, self._OnSetRootDir, menuSelectDir)
        self.Bind(wx.EVT_MENU, self._onAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self._onExit, menuExit)      

        # Install the tree and the editor.
        splitter.SplitVertically(self.expTree, self.editor)
        splitter.SetSashPosition(400, True)
        
        self.Show()
            
    def _onAbout(self, event):
        """ Eventhandler for presenting the about dialog window """
        dlg = wx.MessageDialog(self, "An windows style explorer for blackbox session recordings", "Blackbox Explorer", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def _onExit(self, event):
        """ Eventhandler for shutting down the application """
        self.Close(True)

    def _OnSetRootDir(self,e):
        """ Event handler for selecting the root directory """
        self.dirname = ''
        dlg = wx.DirDialog(self, "Choose a Directory", self.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = dlg.GetPath()
            self.expTree.render(self.dirname)
        dlg.Destroy()