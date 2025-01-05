try:
    from SSCPBackend import Backend

    DUMMY_BACKEND = False

except:
    import os
    from recorder.Const import *
    # TODO: replace with use of config module

    DUMMY_BACKEND = True

    class Backend:
        """Dummy implementation and documentation of the recording backend"""

        def Initialise(self):
            """ Activates the camera and audio devices """
            print "Initialising backend"
            return 0

        def StartRecording(self, dirname,  basename):
            """ Starts the recording of audio and video """
            self.path = dirname
            self.basename = basename
            print "Recording to ",  os.path.join(self.path, self.basename)
            return 0

        def StartMapTaskRecording(self, dirname,  basename):
            """ Starts the recording of audio and video with two cameras enabled"""
            self.path = dirname
            self.basename = basename
            print "Recording two cameras to ",  os.path.join(self.path, self.basename)
            return 0


        def StopRecording(self):
            """ Stops the recording of audio and video and checks that the files are correct (e.g. non empty),
                returns an error otherwise (<0). """
            print "Stopping recording"
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            # create some dummy files
            for suff in ['camera-1.raw16', 'left.wav', 'right.wav']:
                h = open(os.path.join(self.path, self.basename+suff), 'w')
                h.write("this is some recorded data in file "+ self.basename+suff)
                h.close()

            return 0

        def StopRecordingYes(self):
            """ Stops the recording of audio and video and checks that the files are correct (e.g. non empty),
                returns an error otherwise (<0).
                Adds a suffix 'yes' to the files."""
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            # create some dummy files
            for suff in ['camera-1-yes.raw16', 'left-yes.wav', 'right-yes.wav']:
                h = open(os.path.join(self.path, self.basename+suff), 'w')
                h.write("this is some recorded data in file "+ self.basename+suff)
                h.close()
            return 0

        def StopRecordingNo(self):
            """ Stops the recording of audio and video and checks that the files are correct (e.g. non empty),
                returns an error otherwise (<0).
                Adds a suffix 'no' to the files."""
            if not os.path.exists(self.path):
                os.makedirs(self.path)
            # create some dummy files
            for suff in ['camera-1-no.raw16', 'left-no.wav', 'right-no.wav']:
                h = open(os.path.join(self.path, self.basename+suff), 'w')
                h.write("this is some recorded data in file "+ self.basename+suff)
                h.close()
            return 0


        def CheckVideoDevice(self):
            """ Checks that the video cameras are ok (<0 otherwise). The check can be based on the values set during calibration. """
            return 0

        def CheckAudioDevice(self):
            """ Checks that the audio device is ok (<0 otherwise). The check can be based on the values set during calibration. """
            return 0

        def CheckDiskSpace(self, directory):
            """ Checks that the root drive of the given directory has enough free space (e.g. >50GB) """
            return 0

        def CheckDirectory(self, dirname):
            """ Checks all the files in the given directory according to the quality check criteria
                (e.g. non empty files) """
            return 0

        def StartVideoPreview(self, camera, windowname):
            """Open a window showing the video preview for the given camera (0 or 1)
            using a given window name"""
            return 0

        def StopVideoPreview(self):
            """Close the video preview window"""
            return 0

        def OpenCamCtrlDlg0(self):
            """Close the video preview window"""
            return 0

        def OpenCamCtrlDlg1(self):
            """Close the video preview window"""
            return 0

        def GetCameraSN(self, camId):
            """Return the serial number of the given camera (0 or 1)"""

            return 12341234
