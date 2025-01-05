import wx
from Const import *
import time, re
from config import config
from Domain import Participant


class SpeakerFrame(wx.Frame):

    def __init__(self, parent):
        """ Initialises the Speaker display.
        raframe is the RAFrame instance that controls us"""

        # need to import style after app is created
        import Style

        wx.Frame.__init__(self, parent=parent, style=wx.DEFAULT_FRAME_STYLE)

        self.SetTitle("AusTalk - Speaker")
        self.SetBackgroundColour(Style.background)
        if config("FULL_DISPLAY", "Yes") == "Yes" and wx.Display.GetCount() >= 2:
            # Initialise secondary screen
            screen2 = wx.Display(SPEAKER_DISPLAY)

            # Ensure screen is initialised correctly
            assert screen2.IsOk()

            # Get screen 2 geometry
            geo = screen2.GetGeometry()
            # Move Speaker Display to screen 2
            self.Move((geo.left, geo.top))
            self.SetClientRect(geo)

            self.ShowFullScreen(True)

        else:
            # set out size, should be full-screen if we're on
            # the black box, 1280x1024 for testing
            self.SetClientRect(wx.Rect(100,100,1280,1024))

        self.__prompt = wx.StaticBitmap(self, -1, name="Prompt")
        self.Show(True)


    def SetPromptImage(self, imagefile):
        """ Display a given image on the Speaker's screen """

        if not os.path.exists(imagefile):
            # substitute a default image
            imagefile = os.path.join(PATH_PROMPTS, PROMPT_BLANK)

        self.__prompt.SetBitmap(wx.Bitmap(imagefile, wx.BITMAP_TYPE_ANY))
        self.__prompt.CenterOnParent()
        self.__prompt.Refresh()



class ParticipantChooser(wx.Panel):
    """Make a control to allow choosing a participant"""

    def __init__(self, parent=None, name="Participant", label=None):

        # need to import style after app is created
        import Style

        wx.Panel.__init__(self, parent, name=name)

        self.SetBackgroundColour(Style.background)

        if not label:
            self.label = name
        else:
            self.label = label

        self.name = name
        self.animalcb = None
        self.colourcb = None
        self.__build()

        self.Fit()
        self.Show(True)


    def __build(self):
        """Create the UI"""

        from Domain import animals, colours

        # overall title
        lbl_name = wx.StaticText(self, -1, self.label)

        # colour chooser with a label
        lbl_colour = wx.StaticText(self, -1, "Colour: ")
        self.colourcb = wx.ComboBox(self, -1, choices=colours, name="Colour", style=wx.CB_READONLY)

        # animal chooser with a label
        lbl_animal = wx.StaticText(self, -1, "Animal: ")
        self.animalcb = wx.ComboBox(self, -1, choices=animals, name="Animal", style=wx.CB_READONLY)

        grid = wx.GridBagSizer(10, 5)
        grid.Add(lbl_name, (0,0), span=(1,2), flag=wx.EXPAND)
        grid.Add(lbl_colour, (1,0))
        grid.Add(self.colourcb, (1,1), flag=wx.EXPAND)
        grid.Add(lbl_animal, (2,0))
        grid.Add(self.animalcb, (2,1), flag=wx.EXPAND)

        self.SetSizer(grid)
        self.Layout()

    def get_selection(self):
        """Get the current participant selection
        as a tuple (colour, animal)"""

        from Domain import colourNameMap, animalNameMap

        if self.animalcb and self.colourcb:
            animal = self.animalcb.GetStringSelection()
            colour = self.colourcb.GetStringSelection()

            # we want to return ids, not names so do a reverse lookup
            if animal != '' and colour != '':
                return (colourNameMap[colour], animalNameMap[animal])

        return (None, None)


class RAFrame(wx.Frame):

    _listeners = []

    def __init__(self, parent=None, layout=LAYOUT_INITIAL):
        """ Initialises the RA display,
        parent is the parent window/frame
        layout is the initial layout to be set up, default 'Initial'"""

        import Style
        wx.Frame.__init__(self, parent, style=wx.DEFAULT_FRAME_STYLE)

        self.SetTitle("AusTalk - RA - Version %s" % config("VERSION", "Unknown"))
        self.SetBackgroundColour(Style.background)

        self.__promptWindowState = "Image"

        # work out our geometry based on whether we're in a two
        # screen or one screen environment
        if config("FULL_DISPLAY", "Yes") == "Yes" and wx.Display.GetCount() >= 2:
            # Initialise primary screen
            screen1 = wx.Display(RA_DISPLAY)

            # Ensure screen is initialised correctly
            assert screen1.IsOk()
            assert screen1.IsPrimary()

            # Get screen 1 geometry
            geo = screen1.GetGeometry()
            # Move RA Display to screen 1
            self.Move((geo.left, geo.top))
            self.SetClientRect(geo)
            # Change Frame to maximized state
            self.Maximize()
        else:
            # set out size, 1024x768 for testing
            self.SetClientRect(wx.Rect(0,0,1280,1024))

        # need to initialise component time to zero so we can display something
        self.SetComponentTime(0)
        self.SetComponentName('')
        self.SetSessionName('')

        self.Show(True)

        self.__enableWhenRecording = []
        self.__disableWhenRecording = []


        # use a larger font for the GUI
        largerfont = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Trebuchet MS')
        self.SetFont(largerfont)

        self.__IMG_ERROR = wx.Bitmap(IMG_ERROR, wx.BITMAP_TYPE_ANY)
        self.__IMG_CHECK = wx.Bitmap(IMG_CHECK, wx.BITMAP_TYPE_ANY)

    def Reset(self):
        """ Reinitialises the frame """
        self.DestroyChildren()

    ################################## LAYOUTS ##################################

    def SetLayout(self, layoutname):
        """Set the layout being displayed, layoutname is one of
        the layout names defined in Const.py.
        """

        assert layoutname in (LAYOUT_FIRST, LAYOUT_SECOND, LAYOUT_THIRD, LAYOUT_FOURTH, LAYOUT_INITIAL,  LAYOUT_YES_NO,
                              LAYOUT_MAPTASK, LAYOUT_DEFAULT,  LAYOUT_FINAL)

        if layoutname == LAYOUT_FIRST:
            self.__firstLayout()
        elif layoutname == LAYOUT_SECOND:
            self.__secondLayout()
        elif layoutname == LAYOUT_THIRD:
            self.__thirdLayout()
        elif layoutname == LAYOUT_FOURTH:
            self.__fourthLayout()
        elif layoutname == LAYOUT_INITIAL:
            self.__initialLayout()
        elif layoutname == LAYOUT_YES_NO:
            self.__yesnoLayout()
        elif layoutname == LAYOUT_MAPTASK:
            self.__maptaskLayout()
        elif layoutname == LAYOUT_DEFAULT:
            self.__defaultLayout()
        elif layoutname == LAYOUT_FINAL:
            self.__finalLayout()


    def __firstLayout(self):

        self.Reset()

        record_btn = wx.Button(self, -1, label="Record 60s Silence", name="RecordSilence")
        self.__BindNotifier(record_btn, EVENT_RECORD_SILENCE)

        btn1 = wx.Button(self, -1, label="Confirmed", name="Confirmed")
        self.__BindNotifier(btn1, EVENT_CONFIRMED_SETUP_1)



        bitmap = os.path.join(PATH_PROMPTS, PROMPT_SETUPINFO_1)
        bmp = wx.Bitmap(bitmap, wx.BITMAP_TYPE_ANY)
        bmpimg = wx.ImageFromBitmap(bmp)
        # resize from 960 720 to leave space for buttons
        #bmpimg = bmpimg.Rescale(900, 675, wx.IMAGE_QUALITY_HIGH)
        bmpimg = wx.StaticBitmap(self, wx.ID_ANY, bmpimg.ConvertToBitmap())

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bmpimg, flag=wx.CENTRE)
        vbox.Add(record_btn, flag=wx.CENTRE)
        vbox.Add(btn1, flag=wx.CENTRE)

        self.SetSizer(vbox)
        self.Layout()
        self.Refresh()

    def SetRecordingSilence(self, state):
        """Indicate whether we are recording silence or not.
        if state=True then we are, False we're not."""

        button = self.FindWindowByName("RecordSilence")

        if state:
            button.SetBackgroundColour("red")
        else:
            button.SetBackgroundColour(None)

        button.Update()

    def __secondLayout(self):

        self.Reset()

        btn1 = wx.Button(self, -1, label="Confirmed", name="Confirmed")
        self.__BindNotifier(btn1, EVENT_CONFIRMED_SETUP_2)



        bitmap = os.path.join(PATH_PROMPTS, PROMPT_SETUPINFO_2)
        bmp = wx.Bitmap(bitmap, wx.BITMAP_TYPE_ANY)
        bmpimg = wx.ImageFromBitmap(bmp)
        #960 720
        #bmpimg = bmpimg.Rescale(900, 675, wx.IMAGE_QUALITY_HIGH)
        bmpimg = wx.StaticBitmap(self, wx.ID_ANY, bmpimg.ConvertToBitmap())

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bmpimg, flag=wx.CENTRE)
        vbox.Add(btn1, flag=wx.CENTRE)

        self.SetSizer(vbox)
        self.Layout()
        self.Refresh()

    def __thirdLayout(self):

        self.Reset()


        confirmBtn = wx.Button(self, -1, label="Confirmed", name="Confirmed")
        self.__BindNotifier(confirmBtn, EVENT_CONFIRMED_SETUP_3)

        videoCheck = wx.Button(self, -1, "Check Video Frame", name="vCheck")
        self.__BindNotifier(videoCheck, EVENT_CHECK_VIDEO)
        videoSet1 = wx.Button(self, -1, "Camera 1 Settings", name="vSet1")
        self.__BindNotifier(videoSet1, EVENT_SET_VIDEO1)
        videoSet2 = wx.Button(self, -1, "Camera 2 Settings", name="vSet2")
        self.__BindNotifier(videoSet2, EVENT_SET_VIDEO2)

        buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        buttonBox.Add(videoCheck, 1, flag=wx.EXPAND)
        buttonBox.Add(videoSet1, 1, flag=wx.EXPAND)
        buttonBox.Add(videoSet2, 1, flag=wx.EXPAND)


        bitmap = os.path.join(PATH_PROMPTS, PROMPT_SETUPINFO_3)
        bmp = wx.Bitmap(bitmap, wx.BITMAP_TYPE_ANY)
        bmpimg = wx.ImageFromBitmap(bmp)
        #960 720
        #bmpimg = bmpimg.Rescale(900, 675, wx.IMAGE_QUALITY_HIGH)
        bmpimg = wx.StaticBitmap(self, wx.ID_ANY, bmpimg.ConvertToBitmap())


        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bmpimg, flag=wx.CENTRE)
        vbox.Add(buttonBox, flag=wx.EXPAND|wx.ALL)
        vbox.Add(confirmBtn, flag=wx.CENTRE)

        self.SetSizer(vbox)
        self.Layout()
        self.Refresh()

    def __fourthLayout(self):

        self.Reset()


        btn1 = wx.Button(self, -1, label="Confirmed", name="Confirmed")
        self.__BindNotifier(btn1, EVENT_CONFIRMED_SETUP_4)

        mAudio = wx.Button(self, -1, "Audio Levels", name="M-Audio")
        self.__BindNotifier(mAudio, EVENT_MAUDIO)

        bitmap = os.path.join(PATH_PROMPTS, PROMPT_SETUPINFO_4)
        bmp = wx.Bitmap(bitmap, wx.BITMAP_TYPE_ANY)
        bmpimg = wx.ImageFromBitmap(bmp)
        #960 720
        #bmpimg = bmpimg.Rescale(900, 675, wx.IMAGE_QUALITY_HIGH)
        bmpimg = wx.StaticBitmap(self, wx.ID_ANY, bmpimg.ConvertToBitmap())

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bmpimg, flag=wx.CENTRE)
        vbox.Add(mAudio, flag=wx.CENTRE)
        vbox.Add(btn1, flag=wx.CENTRE)


        self.SetSizer(vbox)
        self.Layout()
        self.Refresh()

    def __initialLayout(self):
        from Domain import Session

        self.Reset()

        part_ctl = ParticipantChooser(self, name="Speaker A", label="Participant at Main Table")


        btn_session = []
        for session in Session.GetInstances():
            btn = wx.Button(self, -1, label=session.GetName(), name=str(session.GetId()))
            btn_session.append(btn)
            # bind the button to generate an event
            self.Bind(wx.EVT_BUTTON,self.__OnSessionStart)

        # Layout Elements
        outer_hbox = wx.BoxSizer(wx.HORIZONTAL) # hbox1
        outer_vbox = wx.BoxSizer(wx.VERTICAL) # vbox1

        outer_hbox.Add(outer_vbox, 1, wx.CENTER, 0)

        button_box = wx.GridSizer(len(btn_session), 1, 5, 5)

        for btn in btn_session:
            button_box.Add(btn, 0, wx.EXPAND, 0)

        outer_vbox.Add(part_ctl, 1, wx.CENTER, 0)
        outer_vbox.Add(button_box, 0, wx.CENTER, 0)


        self.SetSizer(outer_hbox)
        self.Layout()



    def __mainLayout(self):
        """Generate the main RA screen layout, this has
        slots for all the main buttons etc. and is then modified for
        either the YesNo or Prompts layout
        Returns the controls container that will be used for the
        different task elements"""


        import Style

        # only build the layout if we haven't already done so
        controls = self.FindWindowByName("Controls")
        if controls:
            # we already did it, just empty out the controls panel
            controls.DestroyChildren()
            # remove some bindings
            self.Unbind(wx.EVT_COMBOBOX)
            return controls

        # otherwise we build the display
        self.Reset()

        # Create Elements
        header = wx.Panel(self, -1, name="Header")
        session = wx.StaticText(header, -1, name="Session", label="", style=wx.ALIGN_LEFT)
        participant = wx.StaticText(header, -1, name="Participant", label="Participant", style=wx.ALIGN_CENTER)
        time = wx.StaticText(header, -1, name="Time", label="", style=wx.ALIGN_RIGHT)

        header.SetBackgroundColour(Style.background)


        videoCheck = wx.Button(self, -1, "Check Video Frame", name="vCheck")
        self.__BindNotifier(videoCheck, EVENT_CHECK_VIDEO)

        videoSet1 = wx.Button(self, -1, "Camera 1 Settings", name="vSet1")
        self.__BindNotifier(videoSet1, EVENT_SET_VIDEO1)

        videoSet2 = wx.Button(self, -1, "Camera 2 Settings", name="vSet2")
        self.__BindNotifier(videoSet2, EVENT_SET_VIDEO2)

        mAudio = wx.Button(self, -1, "Audio Levels", name="M-Audio")

        finalise = wx.Button(self, -1, "Finalise Session", name="Finalise")
        exit = wx.Button(self, -1, "Exit", name="Exit")
        backend_messages = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP,  name="Messages")
        protocol = wx.TreeCtrl(self, -1, name="Protocol", style=wx.TR_HAS_BUTTONS|wx.TR_NO_LINES|wx.TR_LINES_AT_ROOT|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_ROW_LINES|wx.TR_DEFAULT_STYLE|wx.SUNKEN_BORDER)

        nextComponent = wx.Button(self, -1, "Skip to Next Component", name="NextComponent")

        component = wx.Panel(self, -1, name="Component")
        component.SetBackgroundColour(Style.background)

        promptpanel = wx.Panel(component, -1, name="PromptPanel")
        promptpanel.SetBackgroundColour(Style.background)

        state = wx.Panel(component, -1, name="State")
        state.SetBackgroundColour(Style.background)
        item = wx.StaticText(state, -1, "Item X of Y", name="Item", style=wx.ALIGN_CENTRE)
        recording_state = wx.StaticText(state, -1, "STOPPED", name="RecordingState", style=wx.ALIGN_CENTRE|wx.ALIGN_CENTER_VERTICAL)

        previous = wx.Button(component, -1, "Previous Item", name="Previous")
        controls = wx.Panel(component, -1, name="Controls")
        next = wx.Button(component, -1, "Next Item", name="Next")

        self.__BindNotifier(previous, EVENT_PREVIOUS)
        self.__BindNotifier(next, EVENT_NEXT)
        self.__BindNotifier(mAudio, EVENT_MAUDIO)
        self.__BindNotifier(finalise, EVENT_FINALISE)
        #self.__BindNotifier(nextComponent, EVENT_NEXT_COMPONENT)
        nextComponent.Bind(wx.EVT_BUTTON, self.__OnNextComponent)

        exit.Bind(wx.EVT_BUTTON, self.__OnExit)
        #protocol.Bind(wx.EVT_TREE_SEL_CHANGED, self.__OnTreeSelectionChange, protocol)

        # these buttons should be disabled when recording
        self.__disableWhenRecording = [previous, next, nextComponent, videoCheck, videoSet1, videoSet2, mAudio, finalise, exit]
        self.__enableWhenRecording = [] # [stop, yes, no]

        # Layout Elements
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox3 = wx.BoxSizer(wx.VERTICAL)
        vbox7 = wx.BoxSizer(wx.VERTICAL)
        # Component layout
        vbox4 = wx.BoxSizer(wx.VERTICAL)
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        vbox8 = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(participant, 1, wx.ALIGN_LEFT, 0)
        hbox1.AddStretchSpacer(1)
        hbox1.Add(session, 1, wx.ALIGN_RIGHT, 0)
        hbox1.Add(time, 1, wx.ALIGN_RIGHT, 0)

        vbox1.Add(header, 0, wx.ALL|wx.EXPAND, 5)
        vbox2.Add(component, 4, wx.ALL|wx.EXPAND, 5)

        vbox2.Add(backend_messages, 1, wx.EXPAND, 0)
        hbox2.Add(vbox2, 5, wx.EXPAND, 0)
        vbox1.Add(hbox2, 1, wx.EXPAND, 0)
        hbox.Add(vbox1, 5, wx.EXPAND, 0)
        vbox7.Add(protocol, 1, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(nextComponent, 0, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(finalise, 0, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(mAudio, 0, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(videoCheck, 0, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(videoSet1, 0, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(videoSet2, 0, wx.ALL | wx.EXPAND, 5)
        vbox7.Add(exit, 0, wx.ALL | wx.EXPAND, 5)
        hbox.Add(vbox7, 2, wx.EXPAND, 0)

        # Component layout
        vbox4.Add(promptpanel, 6, wx.ALL|wx.EXPAND, 5)
        vbox4.Add(state, 0, wx.ALL|wx.EXPAND, 10)
        hbox6.Add(previous, 1, wx.ALL|wx.EXPAND, 5)
        hbox6.Add(controls, 3, wx.EXPAND, 0)
        hbox6.Add(next, 1, wx.ALL|wx.EXPAND, 5)
        vbox4.Add(hbox6, 1, wx.EXPAND, 0)

        vbox8.Add(item, 0, wx.ALL|wx.EXPAND, 5)
        vbox8.Add(recording_state, 1, wx.EXPAND, 15)

        header.SetSizer(hbox1)
        header.Layout()

        component.SetSizer(vbox4)
        component.Layout()

        state.SetSizer(vbox8)
        state.Layout()

        self.SetSizer(hbox)
        self.Layout()

        return controls


    def __getPromptPanel(self):
        """Get the panel that contains the variable prompt area"""

        pp = self.FindWindowByName("PromptPanel")
        return pp

    def __getControlPanel(self):
        """Get the panel that contains the variable control buttons"""

        cp = self.FindWindowByName("Controls")
        return cp

    def __yesnoLayout(self):
        """Generate the screen layout for the Yes No question component"""

        # depends on mainlayout
        controls = self.__mainLayout()

        self.__setPromptPanelState("Image")

        start = wx.Button(controls, -1, "Start Recording", name="StartPause")
        yes = wx.Button(controls, -1, "Done (Answer Yes)", name="Yes")
        no = wx.Button(controls, -1, "Done (Answer No)", name="No")
        self.__enableWhenRecording = [yes, no]

        self.__BindNotifier(start,  EVENT_START)
        self.__BindNotifier(yes,  EVENT_STOP_YES)
        self.__BindNotifier(no,  EVENT_STOP_NO)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1 = wx.BoxSizer(wx.VERTICAL)

        hbox1.Add(start, 1, wx.ALL|wx.EXPAND, 5)
        vbox1.Add(yes, 1, wx.ALL|wx.EXPAND, 5)
        vbox1.Add(no, 1, wx.ALL|wx.EXPAND, 5)
        hbox1.Add(vbox1, 1, wx.EXPAND, 0)

        controls.SetSizer(hbox1)
        controls.Layout()

        #self.Bind(wx.EVT_KEY_DOWN, self.__yesnoKeyBinding)

    def __yesnoKeyBinding(self, event):
        """Key binding handler for the yes/no layout"""
        ### TODO: Not working
        key = event.GetKeyCode()
        if key == wx.WXK_SPACE:
            # Control (CMD on Mac) space is No, plain space is Yes
            if event.CmdDown():
                self.NotifyObservers(EVENT_STOP_NO)
            else:
                self.NotifyObservers(EVENT_STOP_YES)
        elif key == wx.WXK_LEFT:
            self.NotifyObservers(EVENT_PREVIOUS)
        elif key == wx.WXK_RIGHT:
            self.NotifyObservers(EVENT_NEXT)

    def __getMapTaskMap(self):
        """Return the selection in the map chooser.
        Only makes sense in the map task, returns None
        if there is no selection or no control."""

        cb = self.FindWindowByName("Map")
        if cb:
            return cb.GetStringSelection()
        else:
            return None

    def __getMapTaskRole(self):
        """Return the selection in the role chooser.
        Only makes sense in the map task, returns None
        if there is no selection or no control."""

        cb = self.FindWindowByName("Role")
        if cb:
            return cb.GetStringSelection()
        else:
            return None

    def __maptaskLayout(self):
        """Generate the screen layout for the map task component"""

        # depends on mainlayout
        controls = self.__mainLayout()

        headerfont = wx.Font(18, wx.SWISS, wx.NORMAL, wx.NORMAL, False, u'Trebuchet MS')


        # we need to replace the prompt frame with our stuff
        promptw = self.__setPromptPanelState("Controls")

        instruction_text = """Please enter the details below of the new speaker who
will sit at the Second Table.

Remember to calibrate video and audio for the new speaker.

        """

        instructions = wx.StaticText(promptw, -1, label=instruction_text, style=wx.ALIGN_CENTER )
        instructions.SetFont(headerfont)

        participant = ParticipantChooser(promptw, name="Speaker B", label="Enter identity of the Speaker at the Second Table")

        # main participant role chooser with a label
        roles = ['Information Giver', 'Information Follower']
        lbl_prole = wx.StaticText(promptw, -1, "Role of the speaker at the Main Table (%s): " % self.__participant )
        prole = wx.ComboBox(promptw, -1, choices=roles, name="Role", style=wx.CB_READONLY)
        prole_ctl = wx.BoxSizer(wx.HORIZONTAL)
        prole_ctl.Add(lbl_prole, 1, wx.EXPAND, 0)
        prole_ctl.Add(prole, 0, wx.RIGHT, 0)

        # A label that gets updated with the role of speaker B
        lbl_brole = wx.StaticText(promptw, -1, "Role of the speaker at the Second Table: ", name="speakerBrole", style=wx.ALIGN_CENTER)

        # we update the label when the combobox is changed
        def update_role_label (evt):
            (colour, animal) = participant.get_selection()
            if colour != None and animal != None:
                part = Participant(colour, animal)
                label = "Role of the speaker at the Second Table (%s): %s" % (str(part), self.__OtherMapRole(prole.GetValue()))
                lbl_brole.SetLabel(label)

        self.Bind(wx.EVT_COMBOBOX, update_role_label)

        # role chooser with a label
        maps = ['Map A - architecture', 'Map A - colour', 'Map B - architecture', 'Map B - colour']
        lbl_map = wx.StaticText(promptw, -1, "Map: ")
        map = wx.ComboBox(promptw, -1, choices=maps, name="Map", style=wx.CB_READONLY)
        map_ctl = wx.BoxSizer(wx.HORIZONTAL)
        map_ctl.Add(lbl_map, 1, wx.EXPAND, 0)
        map_ctl.Add(map, 1, wx.RIGHT, 0)

        grid = wx.GridBagSizer(25, 5)
        grid.Add(instructions, (0,0))
        grid.Add(participant, (1,0))
        grid.Add(prole_ctl, (2,0))
        grid.Add(lbl_brole, (3,0))
        grid.Add(map_ctl, (4,0))


        promptw.SetSizer(grid)
        promptw.Layout()

        # set up controls
        start = wx.Button(controls, -1, "Start", name="StartPause")
        stop = wx.Button(controls, -1, "Done", name="Stop")

        self.__BindNotifier(start, EVENT_START)
        self.__BindNotifier(stop,  EVENT_STOP)

        self.__enableWhenRecording = [stop]

        controlsizer = wx.BoxSizer(wx.HORIZONTAL)
        controlsizer.Add(start, 1, wx.ALL|wx.EXPAND, 5)
        controlsizer.Add(stop, 1, wx.ALL|wx.EXPAND, 5)

        controls.SetSizer(controlsizer)
        controls.Layout()



    def __OtherMapRole(self, role):
        roles = ['Information Giver', 'Information Follower']
        if role == roles[0]:
            return roles[1]
        elif role == roles[1]:
            return roles[0]
        else:
            return ""




    def __defaultLayout(self):
        """Generate the screen layout for the component needing prompts"""

        # depends on mainlayout
        controls = self.__mainLayout()
        self.__setPromptPanelState("Image")

        start = wx.Button(controls, -1, "Start", name="StartPause")
        stop = wx.Button(controls, -1, "Done", name="Stop")

        self.__BindNotifier(start,  EVENT_START)
        self.__BindNotifier(stop,  EVENT_STOP)

        self.__enableWhenRecording = [stop]\

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        hbox1.Add(start, 1, wx.ALL|wx.EXPAND, 5)
        hbox1.Add(stop, 1, wx.ALL|wx.EXPAND, 5)

        controls.SetSizer(hbox1)
        controls.Layout()

    ################################## Log ########################################

    def LogMessage(self, message,  type=None):
        """Add a log message, type is a message type
        as defined in Const, message is a string"""

        textbox = self.FindWindowByName("Messages")
        if textbox:
            textbox.AppendText(message+'\n')


    ################################## Observers ##################################

    def NotifyObservers(self, eventName, values = {}, eventObj = None):
        """ Listeners should register callbacks and are notified of events
        with an event name, values as a dictionnary and the event object if any """
        for listener in self._listeners:
            listener(eventName, values, eventObj)

    def AddObserver(self, callback):
        """ Register a callback function, mainly used by
        protocol to listen to GUI events
        callback takes args
          eventname - event name that was triggered
          values - dictionary of event parameters, default {}
          eventObj - the wx Event object, default None
        """
        self._listeners.append(callback)

    def ClearObservers(self):
        """Remove any existing observers registered"""

        self._listeners = []

    ################################## Event Listners ##################################

    def __OnSessionStart(self, event):
        """Event triggered when the user selects a session button
        initialise the session and move to the first component screen"""

        (colour, animal) = self.FindWindowByName("Speaker A").get_selection()

        session = event.GetEventObject().GetName()

        if animal==None or colour==None: # Display Error
            wx.MessageDialog(
                parent=self,
                message='You must select the participant colour and animal.',
                caption='Error',
                style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
            ).ShowModal()
        else: # Notify
            values = {
                'session': session,
                'colour': colour,
                'animal': animal
            }
            self.NotifyObservers(EVENT_SESSION_START, values)

    def OnMapTaskStart(self):
        """Called when the Start button is pressed
        during the MapTask. Ensures that the relevant data
        has been entered before recoding starts.

        Return a dictionary of metadata values if all's well, False otherwise"""

        (colour, animal) = self.FindWindowByName("Speaker B").get_selection()
        map = self.__getMapTaskMap()
        role = self.__getMapTaskRole()


        if (animal == None and colour == None) or not map or not role:
            wx.MessageDialog(
                parent=self,
                message='You must enter all the required data for the Map Task.',
                caption='Error',
                style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
            ).ShowModal()
            return False
        else: # Notify
            values = {
                'colour': colour,
                'animal': animal,
                'role': role,
                'map': map,
            }
            return values


    def __OnNextComponent(self, event):
        """Move to the next component if the RA agrees"""

        result = wx.MessageDialog(
                        parent=self,
                        message='Are you sure you want to skip the rest of this component',
                        caption='Confirm',
                        style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
                    ).ShowModal()

        if result == wx.ID_OK:
            self.NotifyObservers(EVENT_NEXT_COMPONENT)


    def __OnExit(self, event):
        """Exit the application"""
        self.NotifyObservers(EVENT_EXIT)

    def __OnTreeSelectionChange(self, event):
        tree = event.GetEventObject()
        root = tree.GetRootItem()
        if tree.GetItemParent(event.GetItem()) == root:
            itempos = 0
            comppos = self.__findItemPosition(tree, root, event.GetItem())
        else:
            itempos = self.__findItemPosition(tree, tree.GetItemParent(event.GetItem()), event.GetItem())
            comppos = self.__findItemPosition(tree, root, tree.GetItemParent(event.GetItem()))

        # this would enable mouse based update of the current item
        # but it's also being triggered on a redraw of the tree
        # because we call SelectItem
        #self.NotifyObservers(EVENT_GOTO, {'pos': (comppos, itempos)})

    def __OnTimerUpdate(self, event):
        """ Set the time on the RA screen (called every second) """
        comptime = self.FindWindowByName("Time")
        if comptime:
            comptime.SetLabel("%s: %s/%s" %
                (
                 self.__currentComponentName,
                 time.strftime("%M:%S", time.gmtime(int(self.__componentTime))),
                 time.strftime("%M:%S", time.gmtime(int(self.GetPlannedTime())))
                )
            )
            comptime.GetParent().Layout()

        sesstime = self.FindWindowByName("Session")
        if sesstime:
            sesstime.SetLabel("%s: %s" %
                (
                 self.__currentSessionName,
                 time.strftime("%H:%M:%S", time.gmtime(int(self.__elapsedTime))),
                )
            )
            sesstime.GetParent().Layout()

        self.__elapsedTime += 1
        self.__componentTime += 1

    def __BindNotifier(self, button,  eventname):
        """Set up a binding for the given button so that
        the notifier will issue the given eventname when
        the button is pressed."""

        button.Bind(wx.EVT_BUTTON,  lambda(event): self.NotifyObservers(eventname))

    def OnFinalise(self, isSessionCompleted, isRecording):
        """Prompt the user to confirm finalisation of the GUI session
        warn if the session is not completed or if we are still recording"""



        if isRecording:
            message = "Please stop recording before exiting."
            result = wx.MessageDialog(
                    parent=self,
                    message=message,
                    caption='Confirm Finalisation',
                    style=wx.OK|wx.ICON_QUESTION|wx.STAY_ON_TOP
                ).ShowModal()
            # no option to do nothing, always return to allow them to stop recording
            return False


        message = "Are you sure you want to finalise the session?"
        if not isSessionCompleted:
            message = "The session is incomplete. " + message

        result = wx.MessageDialog(
            parent=self,
            message=message,
            caption='Confirm Finalisation',
            style=wx.OK|wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
        ).ShowModal()
        if result == wx.ID_OK:
            return True
        return False


    ################################## Getters/Setters ##################################

    def StartHeartbeat(self):
        self.__heartbeat = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, lambda event: self.NotifyObservers(EVENT_HEARTBEAT), self.__heartbeat)
        self.Start(5000)

    def StopHeartbeat(self):
        if hasattr(self, '__heartbeat') and self.__heartbeat:
            self.__heartbeat.Stop()
            self.Unbind(wx.EVT_TIMER, self.__heartbeat)
            del self.__heartbeat

    def StartTimer(self):
        self.__elapsedTime = 0
        self.__componentTime = 0
        self.__timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.__OnTimerUpdate, self.__timer)
        self.__timer.Start(1000)
        self.__timer.Notify()

    def StopTimer(self):
        if hasattr(self, '__timer') and self.__timer:
            self.__timer.Stop()
            self.Unbind(wx.EVT_TIMER, self.__timer)
            del self.__timer

    def SetParticipant(self, participant):
        """ Set the participant name on the RA screen """
        self.__participant = participant
        window = self.FindWindowByName("Participant")
        if window:
            window.SetLabel(str(participant))
            window.GetParent().Layout()

    def SetSessionName(self, name):
        """ Set the session name on the RA screen """
        self.__currentSessionName = name

    def SetComponentName(self, name):
        """ Set the component name on the RA screen """
        self.__currentComponentName = name

    def SetComponentTime(self, t):
        """Set the planned time for a new component and
        reset the component clock"""

        self.__componentTime = 0
        self.__plannedTime = t

    def GetPlannedTime(self):
        return self.__plannedTime

    def SetItemCounter(self, current, total):
        window = self.FindWindowByName("Item")
        if window:
            window.SetLabel("Item %d of %d" % (current, total))
            window.GetParent().Layout()

    def __setPromptPanelState(self, state="Image"):
        """The Prompt Panel is either an image (default) or
        a regular panel for displaying other controls. This
        sets the state of the panel. If state is 'Image' then
        it ensures that a StaticBitmap is installed. If state
        is 'Controls' then the panel is emptied ready for
        controls to be added to the panel.

        As a side effect, any contents in the panel will
        be destroyed.

        Returns the panel"""

        window = self.FindWindowByName("PromptPanel")
        if not window:
            return None

        if state == "Image":

            # make sure we have an image as a child
            bitmap_w = window.FindWindowByName("PromptImage")

            if not bitmap_w:
            # need to clean out any other stuff
                window.DestroyChildren()
                bitmap_w = wx.StaticBitmap(window, name="PromptImage")

            self.__promptWindowState = state

        elif state == "Controls":

            window.DestroyChildren()
            self.__promptWindowState = state

        return window



    def SetPromptImage(self, imagefile):
        """ Updates the prompt with an image read from imagefile
        Scales the image to the available area."""

        if not os.path.exists(imagefile):
            # substitute a default image
            imagefile = os.path.join(PATH_PROMPTS, PROMPT_BLANK)

        window = self.__getPromptPanel()

        if window and self.__promptWindowState == "Image":
            bitmap_w = self.FindWindowByName("PromptImage")

            # Now read the image data and scale to the right size

            # Get StaticImage container dimensions
            dimensions = window.GetSize()
            # Load image
            image = wx.Image(imagefile, wx.BITMAP_TYPE_ANY)
            # Get image ratio
            ratio = float(image.GetWidth()) / float(image.GetHeight())

            # Compute width, height, top and left
            if dimensions[1] * ratio <  dimensions[0]:
                # If display height is smaller than width
                height = dimensions[1]
                width = height * ratio
            else:
                # else display width is smaller than or equal to height
                width = dimensions[0]
                height = width / ratio
            # position of the image when resizing to display dimensions
            left = (dimensions[0] - width) / 2
            top = (dimensions[1] - height) / 2

            # Rescale to full height or width, resize to display dimension and convert to bitmap
            bitmap = image.Rescale(width, height).Resize(dimensions,(left, top)).ConvertToBitmap()

            bitmap_w.SetBitmap(bitmap)
            bitmap_w.Refresh()


    def SetStopped(self):
        recording_state = self.FindWindowByName("RecordingState")
        if recording_state:
            recording_state.SetBackgroundColour("green")
            recording_state.SetLabel("STOPPED")
            recording_state.GetParent().Layout()

        self.__UpdateButtonState(self.__disableWhenRecording, self.__enableWhenRecording)

        # toggle the
        startbutton = self.FindWindowByName("StartPause")
        if startbutton:
            startbutton.SetLabel(label="Start")
            self.__BindNotifier(startbutton, EVENT_START)

    def SetRecording(self):
        recording_state = self.FindWindowByName("RecordingState")
        if recording_state:
            recording_state.SetBackgroundColour("red")
            recording_state.SetLabel("RECORDING")
            recording_state.GetParent().Layout()

        self.__UpdateButtonState(self.__enableWhenRecording, self.__disableWhenRecording)

        startbutton = self.FindWindowByName("StartPause")
        if startbutton:
            startbutton.SetLabel(label="Pause")
            self.__BindNotifier(startbutton, EVENT_PAUSE)

    def __UpdateButtonState(self, enable = [], disable = []):
        for el in enable:
            if el:
                el.Enable()
        for el in disable:
            if el:
                el.Disable()


    def UpdateVideoStatus(self, status, message = None):
        self.__UpdateDeviceStatus("VideoStatus", status, message)

    def UpdateAudioStatus(self, status, message = None):
        self.__UpdateDeviceStatus("AudioStatus", status, message)

    def UpdateDiskStatus(self, status, message = None):
        self.__UpdateDeviceStatus("DiskStatus", status, message)

    def __UpdateDeviceStatus(self, device, status, message = None):
        window = self.FindWindowByName(device)
        if window:
            if status:
                image = self.__IMG_CHECK
            else:
                image = self.__IMG_ERROR

            window.SetBitmap(image)
            window.Refresh()
            window.GetParent().Layout()

            if message:
                self.LogMessage(message)

    ########################### Tree Control #########################################

    def TreeView(self,  tree):
        """Populate the Tree View with the components and their different items
        tree is a nested list of component names and their items
        """

        protocol = self.FindWindowByName('Protocol')
        if protocol:
            root = protocol.AddRoot('Protocol')
            # add the root level components
            for comp in tree:
                thiscomp = protocol.AppendItem(root,  self.__NormaliseName(str(comp[0])))
                # add the children
                for item in comp[1]:
                    # is it a tuple or just a string?
                    if len(item) == 2:
                        (name, state) = item
                    else:
                        name = item
                        state = False
                    protocol.AppendItem(thiscomp,  self.__NormaliseName(name))

    def __findItemPosition(self, tree, root, item):
        pos = 0
        i, cookie = tree.GetFirstChild(root)
        while i:
            if i == item:
                return pos
            i, cookie = tree.GetNextChild(root, cookie)
            pos += 1
        return pos


    def __findItemInChildren(self, tree, root, text):
        """Find the item with this text label in the
        children of the root item in this tree control.
        Return the item if found.
        Return None if no item is found."""

        item, cookie = tree.GetFirstChild(root)
        while item:
            if self.__NormaliseName(text) == tree.GetItemText(item):
                return item
            item, cookie = tree.GetNextChild(root, cookie)
        return None

    def __CheckAllChildrenComplete(self, tree, root):
        """Remove any bold styling from all children of this root"""

        item, cookie = tree.GetFirstChild(root)
        while item:
            if not tree.IsBold(item):
                return False
            item, cookie = tree.GetNextChild(root, cookie)
        return True


    def TreeShowComponent(self,  component):
        """Expand the named component and fold all others
        Return the item corresponding to this component or None if not found"""

        protocol = self.FindWindowByName('Protocol')
        if component and protocol:
            #can't do this on some versions of wx - can't collapse hidden root
            protocol.CollapseAll()
            # need to find the item we want
            item = self.__findItemInChildren(protocol, protocol.GetRootItem(), component.GetName())
            if item:
                protocol.Expand(item)
                protocol.EnsureVisible(item)
                protocol.SelectItem(item, True)
                return item
        return None


    def TreeShowItem(self,  component, item):
        """Highlight the given item within the component in the tree view"""

        if component and item:
            protocol = self.FindWindowByName('Protocol')
            if protocol:
                comp_item = self.__findItemInChildren(protocol, protocol.GetRootItem(), component.GetName())
                item_item = self.__findItemInChildren(protocol, comp_item,  str(item))
                protocol.SelectItem(item_item, True)
                protocol.EnsureVisible(item_item)
                protocol.Refresh()


    def TreeTickItem(self,  component,  item,  state=True):
        """Set the 'tick' on an item within a component to the given state"""
        protocol = self.FindWindowByName('Protocol')
        if protocol:
            comp_item = self.__findItemInChildren(protocol, protocol.GetRootItem(), component.GetName())
            item_item = self.__findItemInChildren(protocol, comp_item,  item)
            protocol.SetItemBold(item_item, state)
            protocol.Refresh()
            if self.__CheckAllChildrenComplete(protocol, comp_item):
                protocol.SetItemBold(comp_item, True)

    def __NormaliseName(self, text, maxlength = 30):
        """ Normalises the text to strip characters causing problems to the tree view """
        text = text[0:maxlength]
        if len(text) == maxlength:
            pos = text.rfind(" ")
            if pos > -1:
                return text[:pos] + '...'
        return text

if __name__=='__main__':
    import time


    class TestSSCPApp(wx.App):
        """Class for the SSCP application"""

        def OnInit(self):
            self.frame = wx.Frame(None)
            self.part = ParticipantChooser(self.frame)

            self.frame.Show()
            return True


        def testEventHandler(self, event, values={}, eventObj=None):
            """"test event handler"""

            pass

    # testing
    app = TestSSCPApp(0)
    app.MainLoop()
