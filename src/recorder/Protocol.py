
from Const import *
import config
from datahandling import Metadata, RecordedSession
import hardware
from Domain import Timer, Participant, Session
from exceptions import Exception
import time
import os, wx
import subprocess
import urllib, json

class Controller():
    """ Controller that manages the flow of the sessions """

    def __init__(self, raFrame = None, speakerFrame = None):
        """ Initialises the controller with the different screens """

        # quit if we couldn't load the backend
        if hardware.DUMMY_BACKEND:
            wx.MessageDialog(
                    parent=None,
                    message='There has been a problem loading the BlackBox software. You may need to re-install.',
                            caption='Software Problem',
                            style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
                        ).ShowModal()
            if config.config("DEBUG", "No") == "No":
                exit()


        try:
            self.__backend = hardware.Backend()
            self.__backend.Initialise()
        except:
            result = wx.MessageDialog(
                    parent=None,
                    message='Initialisation of recording hardware failed, you will not be able to record. Hit OK to continue in test mode, Cancel to quit.',
                            caption='Software Problem',
                            style=wx.OK | wx.CANCEL | wx.ICON_ERROR | wx.STAY_ON_TOP

                        ).ShowModal()
            if result == wx.ID_CANCEL and config.config("DEBUG", "No") == "No":
                exit()
            self.__backend = None


        if raFrame:
            self.SetRAFrame(raFrame)

        if speakerFrame:
            self.SetSpeakerFrame(speakerFrame)

        self.__Init()

    def __Reset(self):
        """ Reinitialises internal state """
        self.__session = None
        self.__participant = None

        self.__SetRecording(False)

        self.__StopTimer()

    def __DestroyBackend(self):
        if self.__backend:
            del self.__backend

    ########################## Protocol Events ##########################

    def EventDispatcher(self, eventName, values = {}, eventObj = None):
        """ Manages events from the GUI and dispatches them to actions in the controller """

        if eventName == EVENT_CONFIRMED_SETUP_1:
            self.__Reset()
            self.__stage = STAGE_SECOND
            self.__UpdateSpeakerPrompt()
            self.__SetLayout(LAYOUT_SECOND)
        elif eventName == EVENT_RECORD_SILENCE:
            self.__RecordSilence()
        elif eventName == EVENT_CONFIRMED_SETUP_2:
            self.__Reset()
            self.__stage = STAGE_THIRD
            self.__UpdateSpeakerPrompt()
            self.__SetLayout(LAYOUT_THIRD)
        elif eventName == EVENT_CONFIRMED_SETUP_3:
            self.__Reset()
            self.__stage = STAGE_FOURTH
            self.__UpdateSpeakerPrompt()
            self.__SetLayout(LAYOUT_FOURTH)
        elif eventName == EVENT_CONFIRMED_SETUP_4:
            self.__Reset()
            self.__stage = STAGE_INITIAL
            self.__UpdateSpeakerPrompt()
            self.__SetLayout(LAYOUT_INITIAL)
        elif eventName == EVENT_SESSION_START:
            self.__StartSession(values['session'], values['colour'], values['animal'])
        elif eventName == EVENT_RESET:
            self.__Init()
        elif eventName == EVENT_EXIT:
            self.__ApplicationClose()
        elif eventName == EVENT_MAUDIO:
            self.__CalibrateAudio()
        elif eventName == EVENT_CHECK_VIDEO:
            self.__CalibrateVideo()
        elif eventName == EVENT_SET_VIDEO1:
            self.__SetVideo1()
        elif eventName == EVENT_SET_VIDEO2:
            self.__SetVideo2()
        elif self.__stage == STAGE_RECORDING:
            if eventName == EVENT_NEXT:
                self.__Next()
            elif eventName == EVENT_PREVIOUS:
                self.__Previous()
            elif eventName == EVENT_NEXT_COMPONENT:
                self.__NextComponent()
            elif eventName == EVENT_PREVIOUS_COMPONENT:
                self.__PreviousComponent()
            elif eventName == EVENT_START:
                self.__Start()
            elif eventName == EVENT_PAUSE:
                self.__Pause()
            elif eventName == EVENT_STOP:
                self.__End()
            elif eventName == EVENT_STOP_YES:
                self.__EndYes()
            elif eventName == EVENT_STOP_NO:
                self.__EndNo()
            elif eventName == EVENT_CALIBRATE:
                self.__Calibrate()
            elif eventName == EVENT_FINALISE:
                self.__FinaliseSession()
            elif eventName == EVENT_GOTO:
                self.__GoTo(values['pos'])

    def __Init(self):
        """ Initial step in the process when RA's select the participant code and session number """
        self.__Reset()
        # to skip the first screens change this to 0
        if config.config("RECORDER_SKIP_INITIAL_SCREENS", "No") == "No":
            self.__stage = STAGE_FIRST
            self.__UpdateSpeakerPrompt()
            self.__SetLayout(LAYOUT_FIRST)
            self.__maptaskMeta = False
        else:
            self.__stage = STAGE_INITIAL
            self.__UpdateSpeakerPrompt()
            self.__SetLayout(LAYOUT_INITIAL)
            self.__maptaskMeta = False

    def __ValidateParticipant(self, session, colour, animal):
        """Check that this combination of session/colour/animal is ok,
         prompt the user to change or confirm, return True if we're good
         to go on, False otherwise."""

        # dummy participants are always valid

        if colour == 0: # Dummy for Testing
            result = wx.MessageDialog(
                            parent=self.__raFrame,
                            message='Using Dummy Identifier for Testing Purposes',
                            caption='Confirmation',
                            style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
                        ).ShowModal()
            return result == wx.ID_OK

        # here we will do a call to the web server to validate the triplet
        info = self.__ValidateParticpantWeb(session, colour, animal)

        # if we're all ok, pop up a confirmation dialogue
        if info['valid']:
            result = wx.MessageDialog(
                            parent=self.__raFrame,
                            message='Please confirm these participant details\nDate of Birth: %(DOB)s\nPlace of Birth: %(POB)s' % info,
                            caption='Confirmation',
                            style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
                        ).ShowModal()

            if result == wx.ID_OK:
                return True
        elif info['status'] == "No Connection":
            result = wx.MessageDialog(
                            parent=self.__raFrame,
                            message='Unable to connect to the web to validate that speaker identifier,\nare you sure you want to proceed?',
                            caption='Confirmation',
                            style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
                        ).ShowModal()

            if result == wx.ID_OK:
                return True
        else:
            result = wx.MessageDialog(
                            parent=self.__raFrame,
                            message='That speaker identifier can not be validated, please check and try again.\nIf you are sure that the identifier is correct, you may proceed with recording by pressing OK.',
                            caption='Confirmation',
                            style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
                        ).ShowModal()
            if result == wx.ID_OK:
                return True

        # return False if we didn't say yes to anything above
        return False

    def __ValidateParticpantWeb(self, session, colour, animal):
        """Check over the web that this colour/animal pair is ok.

    Return a status structure like:

        if which == 1:
            info = {'valid': True,
                     'DOB': "1999-12-12",
                     'POB': "Engadine",
                     'status': "Validated",
                    }
        elif which == 2:
            info = {'valid': False, 'status': "Validated" }
        elif which == 3:
            info = {'valid': False, 'status': "No Connection"}

        """

        from Domain import colourIdMap, animalIdMap


        urlTemplate = "https://austalk.edu.au/forms/participants/%s-%s"

        url = urlTemplate % (colourIdMap[colour], urllib.quote(animalIdMap[animal]))

        try:
            h = urllib.urlopen(url)
            response_code = h.getcode()
        except:
            return {'valid': False, 'status': "No Connection"}

        if response_code == 400:
            # 400 response means the participant isn't known
            return  {'valid': False, 'status': "Validated"}

        content = h.read()

        try:
            info = json.loads(content)
            info['status'] = 'Validated'
            return info
        except:
            return {'valid': False, 'status': "No Connection"}



    def __StartSession(self, session, colour, animal):
        """ Initialises the session once the participant and session number are known """

        # first validate the colour/animal selected, don't proceed if they're not good

        if not self.__ValidateParticipant(session, colour, animal):
            return

        self.__stage = STAGE_RECORDING

        #self.__backend = backend.Backend()
        #self.__backend.Initialise()

        # need to init the default layout so we have somewhere to write status info
        self.__SetLayout(LAYOUT_DEFAULT)
        self.__SetSession(Session.GetInstance(int(session)))
        self.__SetParticipant(Participant(colour, animal))
        self.__StartTimer()

        # set the planned time for this component
        self.__raFrame.SetComponentTime(self.__session.GetCurrentComponent().GetDuration())
        self.__raFrame.SetComponentName(self.__session.GetCurrentComponent().GetName())


        # self.__Calibrate()

        self.__UpdateLayout()
        self.__InitTreeView()

        if self.__IsRecovery():
            self.__Recover()
            return # Bypasses what is next as it will be called by Recover once the state is regenerated

        self.__UpdateItemCounter()
        self.__UpdateTreeView()
        self.__UpdateSpeakerPrompt()

        self.__SetRecording(False)

    def __GoTo(self, (comp, item)):
        if self.__IsRecording():
            return

        self.__session.SetIndex(comp)
        self.__session.GetCurrentComponent().SetIndex(item)

        # set the planned time for this component
        self.__raFrame.SetComponentTime(self.__session.GetCurrentComponent().GetDuration())
        self.__raFrame.SetComponentName(self.__session.GetCurrentComponent().GetName())

        self.__UpdateLayout()
        self.__UpdateItemCounter()
        self.__UpdateSpeakerPrompt()


    def CurrentComponent(self):
        """Return the component currently being displayed or None if we're not
        inside a component"""

        if self.__session:
            return self.__session.GetCurrentComponent()
        else:
            return None

    def CurrentItem(self):
        """Return the item currently being displayed or None if we're not
        inside a session or haven't started showing items yet"""

        cc = self.CurrentComponent()
        if cc:
            return cc.GetCurrentItem()
        else:
            return None


    def __Previous(self):
        """ Manages the backward flow of the protocol """
        # no action if we're already recording
        if self.__IsRecording():
            return

        if self.__session.GetCurrentComponent().HasPreviousItem():
            # Move component state to previous item
            self.__session.GetCurrentComponent().PreviousItem()
        elif self.__session.HasPreviousComponent():
            # Move session state to previous component
            self.__PreviousComponent()
        else:
            # No previous item
            pass

        self.__UpdateItemCounter()
        self.__UpdateTreeView()
        self.__UpdateSpeakerPrompt()

    def __Next(self):
        """ Manages the forward flow of the protocol """
        # no action if we're already recording
        if self.__IsRecording():
            return

        if self.__session.GetCurrentComponent().HasNextItem():
            # Move to component state to next item
            self.__session.GetCurrentComponent().NextItem()
        elif self.__session.HasNextComponent():
            # Move session state to next component
            self.__NextComponent()
        else:
            self.__FinaliseSession()
            return

        self.__UpdateItemCounter()
        self.__UpdateTreeView()
        self.__UpdateSpeakerPrompt()

    def __PreviousComponent(self):
        """ Component backward navigation """
        if self.__IsRecording():
            return

        if self.__session.HasPreviousComponent():
            # Move session state to previous component
            self.__session.PreviousComponent()

            # set the planned time for this component
            self.__raFrame.SetComponentTime(self.__session.GetCurrentComponent().GetDuration())
            self.__raFrame.SetComponentName(self.__session.GetCurrentComponent().GetName())

            self.__UpdateLayout()
            self.__UpdateItemCounter()
            self.__UpdateTreeView()
            self.__UpdateSpeakerPrompt()

    def __NextComponent(self):
        """ Component forward navigation """
        if self.__IsRecording():
            return

        if self.__session.HasNextComponent():
            # Move session state to next component
            self.__session.NextComponent()

            # set the planned time for this component
            self.__raFrame.SetComponentTime(self.__session.GetCurrentComponent().GetDuration())
            self.__raFrame.SetComponentName(self.__session.GetCurrentComponent().GetName())

            self.__UpdateLayout()
            self.__UpdateItemCounter()
            self.__UpdateTreeView()
            self.__UpdateSpeakerPrompt()
        else:
            self.__FinaliseSession()

    def __ApplicationClose(self, event=None):
        """Close the application - check first with the user that it's ok to do so """
        if not self.__session:
            # we're called before anything has been set up
            self.__DestroyBackend()
            self.__raFrame.Destroy()
            self.__speakerFrame.Destroy()
            return

        # confirm closing with th euser via a dialogue
        if not self.__raFrame.OnFinalise(self.__session.IsCompleted(), self.__IsRecording()):
            return
        else:
            self.__stage = STAGE_FINAL
            self.__StopTimer()
            self.__DestroyBackend()
            self.__raFrame.Destroy()
            self.__speakerFrame.Destroy()
            return


    def __FinaliseSession(self, event=None):
        """ Finalise a session by closing the backend and presenting final screen to the RA """

        #Remove when we have a finalisation screen
                # confirm closing with th euser via a dialogue
        if not self.__raFrame.OnFinalise(self.__session.IsCompleted(), self.__IsRecording()):
            return
        else:

            # generate the manifest file
            # need to get the session dir and basename which is somewhat difficult...
            path = os.path.dirname(os.path.dirname(self.__GetRecordingPath()))
            basename = os.path.basename(path)
            path = os.path.dirname(path)

            rs = RecordedSession(path, basename)
            rs.gen_manifest(isRawDir=True)

            # reinitialise
            self.__Init()



    def __Start(self):
        """ Recording is started """
        if not self.__IsRecording():


            ## if we're in the Maptask layout then we need to do a few things
            # differently, call a different start callback and record the
            # additional meta-data, then call the special start
            # method to start up both cameras
            comp = self.CurrentComponent()

            # are we recording two people, either for the maptask or if we're in the conversation component
            # TODO: should go in the configuration for the component
            twoUp = comp and (comp.GetLayout() == LAYOUT_MAPTASK or comp.GetName() == "Conversation")

                        # if we're in maptask, we can get the extra metadata
            if comp and comp.GetLayout() == LAYOUT_MAPTASK:
                result = self.__raFrame.OnMapTaskStart()
                if not result:
            # we aborted start
                    return
                else:
                    # result is written as metadata

                    # we have colour, animal (for second speaker) role and map
                    # need to save it for later
                    other_participant = Participant(result['colour'], result['animal'])
                    result['colourId'] = other_participant.GetColourId()
                    result['animalId'] = other_participant.GetAnimalId()
                    result['participant'] = str(other_participant)
                    self.__maptaskMeta = result
            else:
                # don't reset the metadata if we're in the conversation
                if not twoUp:
                    # I know nothing of any maptask
                    self.__maptaskMeta = False

            # if we're not on an item alreay (first item) we need to advance
            if not self.CurrentItem():
                self.__Next()

            # ensure any video preview window is closed
            self.__backend.StopVideoPreview()

            self.__SetRecording(True)

                        # start one or two cameras
            if twoUp:
                self.__backend.StartMapTaskRecording(self.__GetRecordingPath(), self.__GetRecordingBaseName())
            else:
                self.__backend.StartRecording(self.__GetRecordingPath(), self.__GetRecordingBaseName())
            self.__UpdateSpeakerPrompt()

    def __End(self):
        """ Recording is stopped, recording of next prompt is started"""
        self.__CommonEnd(self.__GetPrompt())

    def __EndYes(self):
        """ Recording is stopped with flag yes, recording of next prompt is started"""
        self.__CommonEnd('Yes')

    def __EndNo(self):
        """ Recording is stopped with flag no, recording of next prompt is started"""
        self.__CommonEnd('No')

    def __CommonEnd(self, prompt):
        """ Utility common to all End functions, stops current recording, saves result, starts next recording"""
        if self.__IsRecording():
            if prompt == 'Yes':
                self.__backend.StopRecordingYes()
            elif prompt == 'No':
                self.__backend.StopRecordingNo()
            else:
                self.__backend.StopRecording()

            self.__SetRecording(False)
            # self.__UpdateSpeakerPrompt()
            self.__WriteMetadata(prompt)
            self.__ItemCompleted()
            self.__Next()

            if self.__session and self.__session.GetCurrentComponent().Index() == -1:
                self.__Pause()
                return
            if self.__session and (
                    not self.__session.HasNextComponent() and
                    not self.__session.GetCurrentComponent().HasNextItem() and
                    self.__session.GetCurrentComponent().GetCurrentItem().IsCompleted()):
                self.__Pause()
                return
        if self.__session:
            # Even if we weren't recording before, start recording next prompt if not new component
            self.__Start()

    def __Pause(self):
        """Pause recording, aborts current recording and doesn't advance to the next item"""
        if self.__IsRecording():
            self.__backend.StopRecording()
            self.__SetRecording(False)
        #self.__UpdateSpeakerPrompt()

    ########################## Setters/Getters ##########################

    def SetRAFrame(self, frame):
        """ Sets the RA display instance """
        self.__raFrame = frame
        self.__raFrame.AddObserver(self.EventDispatcher)
        frame.Bind(wx.EVT_CLOSE, self.__ApplicationClose)

    def SetSpeakerFrame(self, frame):
        """ Sets the Speaker display instance """
        self.__speakerFrame = frame

    def GetSession(self):
        """ Returns the current session """
        return self.__session

    def GetParticipant(self):
        """ Returns the participant """
        return self.__participant

    def GetTimer(self):
        """ Returns timer """
        if hasattr(self, '__timer'):
            return self.__timer

    def __SetSession(self, session):
        """ Sets the session and Proxy to RA frame setSession """

        # make sure we 'rewind' the session
        session.Reset()

        self.__session = session
        if self.__raFrame:
            self.__raFrame.SetSessionName(session)

    def __SetParticipant(self, participant):
        """ Sets the participant and Proxy to RA frame setParticipant """

        self.__participant = participant
        if self.__raFrame:
            self.__raFrame.SetParticipant(participant)

    def __SetLayout(self, layout):
        """ Proxy to RA frame setLayout """
        if self.__raFrame:
            self.__raFrame.SetLayout(layout)

    def __GetRecordingPath(self):
        """ Get the fully qualified recording path for this session,
        make sure the path exists """

        participant = self.__participant
        session = self.__session
        component = session.GetCurrentComponent()
        item = component.GetCurrentItem()

        path = TPL_RECORDING_PATH % {
            'colourId': participant.GetColourId(),
            'animalId': participant.GetAnimalId(),
            'sessionId': session.GetId(),
            'componentId': component.GetId(),
            'itemId': item.GetId()
        }
        # make it a full path by adding on the configured prefix, make sure it ends in a slash
        path = os.path.join(PATH_RECORDINGS, path) + os.sep

        if not os.path.exists(path):
            os.makedirs(path)
        return path


    def __GetRecordingBaseName(self):
        """ Get the recording basename based on protocol state """
        participant = self.__participant
        session = self.__session
        component = session.GetCurrentComponent()
        item = component.GetCurrentItem()

        return TPL_RECORDING_FILE % {
            'colourId': participant.GetColourId(),
            'animalId': participant.GetAnimalId(),
            'sessionId': session.GetId(),
            'componentId': component.GetId(),
            'itemId': item.GetId()
        }

    def __GetPrompt(self):
        """ Return current item's prompt as string """
        try:
            # in some cases GetCurrentItem might be None
            return self.__session.GetCurrentComponent().GetCurrentItem().GetPrompt()
        except:
            return "No Item"

    ########################## Utilities ##########################

    def __IsRecording(self):
        return self.__isRecording

    def __SetRecording(self, flag = True):
        self.__isRecording = flag

        if self.__raFrame:
            if self.__isRecording:
                self.__raFrame.SetRecording()
            else:
                self.__raFrame.SetStopped()

    def __RecordSilence(self):
        """Records around 60s of silence for calibration purposes
        and stores it somewhere sensible"""

        # silence stored in the root recordings folder with a filename
        # based on the date

        outputdir = os.path.join(PATH_RECORDINGS, "silence"+os.sep)

        # ensure that the folder is present
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

        filename = time.strftime("silence-%d-%m-%Y")

        self.__raFrame.SetRecordingSilence(True)
        self.__SetRecording(True)
        self.__backend.StartRecording(outputdir, filename)
        # wait for  60s
        time.sleep(60)
        self.__backend.StopRecording()
        self.__raFrame.SetRecordingSilence(False)


    def __CalibrateVideo(self):
        print "Calibrating video"

        self.__backend.StartVideoPreview(1, "videoPreview")

    def __CalibrateAudio(self):
        subprocess.Popen([AUDIO_MONITOR])
        pass
        #self.__backend.OpenCamCtrlDlg0()

    def __SetVideo1(self):
        self.__backend.OpenCamCtrlDlg0()

    def __SetVideo2(self):
        self.__backend.OpenCamCtrlDlg1()

    def __WriteMetadata(self, prompt):
        """ Facade to Persistence Metadata """
        participant = self.__participant
        session = self.__session
        component = session.GetCurrentComponent()
        item = component.GetCurrentItem()
        path = self.__GetRecordingPath()
        filename = self.__GetRecordingBaseName()
        cameras = (self.__backend.GetCameraSN(0), self.__backend.GetCameraSN(1))

        if self.__raFrame:
            self.__raFrame.LogMessage("Recorded Component '%s', Item '%d': %s" % (component.GetName(),  item.GetId(),  prompt[:20]+"..."))


        Metadata(participant, session, component, item, path, filename, prompt, cameras, self.__maptaskMeta)

    def __InitTreeView(self):
        """ Populate the treeview on the RA screen """
        if self.__raFrame:
            self.__raFrame.TreeView(self.__session.ToTree())

    def __UpdateTreeView(self):
        """ Tasks to be performed to update the tree view when the protocol state changes """

        component = self.CurrentComponent()
        item = self.CurrentItem()

        self.__raFrame.TreeShowComponent(component)
        self.__raFrame.TreeShowItem(component, item)


    def __ItemCompleted(self):
        """ Tasks to be performed when an item is completed """
        if self.__raFrame:
            component = self.__session.GetCurrentComponent()
            item = component.GetCurrentItem()
            item.SetCompleted()
            self.__raFrame.TreeTickItem(component, str(item), True)

    def __UpdateLayout(self):
        """ Update RA screen layout based on current component """
        self.__SetLayout(self.__session.GetCurrentComponent().GetLayout())

    def __UpdateItemCounter(self):
        if self.__raFrame:
            component = self.__session.GetCurrentComponent()
            self.__raFrame.SetItemCounter(component.Index() + 1, len(component))


    def __UpdateSpeakerPrompt(self):
        """ Manages the prompt displayed to the speaker depending
        on the stage of the application and the protocol."""
        if self.__speakerFrame:
            if not self.__session:
                image = os.path.join(PATH_PROMPTS, PROMPT_DEFAULT)
            else:
                component = self.CurrentComponent()
                item = self.CurrentItem()
                if self.__stage == STAGE_RECORDING:
                    if item and item.GetPromptImage() != "":
                        image = os.path.join(component.GetPromptPath(), item.GetPromptImage())
                    else:
                        image = os.path.join(component.GetPromptPath(), PROMPT_DEFAULT)

            # now we do the update, only update the speaker frame if the component says
            # we should syncronise the prompts (set in the component properties in sql)
            # if we're not syncronising, display either welcome, goodbye or a blank screen

            if self.CurrentComponent() and self.CurrentComponent().SyncPrompts():
                self.__speakerFrame.SetPromptImage(image)
            elif self.__stage == STAGE_INITIAL:
                self.__speakerFrame.SetPromptImage(os.path.join(PATH_PROMPTS, PROMPT_DEFAULT))
            elif self.__stage == STAGE_FINAL:
                self.__speakerFrame.SetPromptImage(os.path.join(PATH_PROMPTS, PROMPT_GOODBYE))
            else:
                self.__speakerFrame.SetPromptImage(os.path.join(PATH_PROMPTS, PROMPT_BLANK))

            # always update the RA screen
            self.__raFrame.SetPromptImage(image)


    def __StartTimer(self):
        """ Ask RAFrame to start timer """
        if self.__raFrame:
            self.__raFrame.StartTimer()

    def __StopTimer(self):
        """ Ask RAFrame to stop timer """
        if self.__raFrame:
            self.__raFrame.StopTimer()

    def __Recover(self):
        """ Reload a participant's session and return to last valid state """
        pass

    def __IsRecovery(self):
        """ Determines from persistence whether the session crashed for the current session/participant """
        return False
