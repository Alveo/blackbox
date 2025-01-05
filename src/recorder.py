import wx

from recorder import Const, Frame,  Protocol

# Every wxWidgets application must have a class derived from wx.App
class GUI_App(wx.App):
    """ SSCP GUI main application that initialises the windows and positions them on the screens """

    def OnInit(self):
        """ Called by wx.App to initialise the environment """

        # Create an instance of Speaker Display
        speaker = Frame.SpeakerFrame(None)

        # Create an instance of RA Display
        RA = Frame.RAFrame(None)

        # Tell wxWindows that RA DIsplay is the main window
        self.SetTopWindow(RA)

        # Protocol to be used by the different screens
        self.controller = Protocol.Controller(
            raFrame=RA,
            speakerFrame=speaker
        )

        # Create a key down event handler at the application level
        # such that widget focus is irrelevant
        self.Bind(wx.EVT_KEY_DOWN, self.__OnKeyDown)

        # Return a success flag
        return True

    def __OnKeyDown(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_SPACE:
            # Yes/No Layouts
            if self.controller.GetSession().GetCurrentComponent().GetLayout() == Const.LAYOUT_YES_NO:
                # Control (CMD on Mac) space is No, plain space is Yes
                if event.CmdDown():
                    self.controller.EventDispatcher(Const.EVENT_STOP_NO)
                else:
                    self.controller.EventDispatcher(Const.EVENT_STOP_YES)
            # Other layouts
            else:
                self.controller.EventDispatcher(Const.EVENT_STOP)
        elif key == wx.WXK_LEFT:
            self.controller.EventDispatcher(Const.EVENT_PREVIOUS)
        elif key == wx.WXK_RIGHT:
            self.controller.EventDispatcher(Const.EVENT_NEXT)
        elif key == wx.WXK_UP:
            self.controller.EventDispatcher(Const.EVENT_PREVIOUS_COMPONENT)
        elif key == wx.WXK_DOWN:
            self.controller.EventDispatcher(Const.EVENT_NEXT_COMPONENT)
        elif key == wx.WXK_ESCAPE:
            self.controller.EventDispatcher(Const.EVENT_PAUSE)


    def OnExit(self):
        """ Things to do when leaving the program """


# Executes the application
if __name__ == '__main__':

    app = GUI_App(0)     # Create an instance of the application class
    app.MainLoop()     # Tell it to start processing events
