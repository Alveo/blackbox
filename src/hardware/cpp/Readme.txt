
Compile Prerequisites:
Below is the third party libraries used in the SSCP Backend C++ code. All the libraries have to be 64bit compatible. Newer version of these libraries might work as well.
•	FlyCapture2.1 (including libiomp5md.dll and FlyCapture2GUI_GTK.glade)
This is the BumbleBee2 SDK from Point Grey Research.

•	PortAudio v19
This is the audio recording open source library with ASIO driver. You may need to download the ASIO driver separately from http://www.steinberg.net/. 

•	OpenCV2.2
Open source library for converting FlyCap2 RGB images for displaying video.

•	Libsndfile v1.0.23
Raw audio .wav files writing.

•	Boost 1_46_1 (Python and filesystem).
To wrap C++ code into .pyd for Python and files checking. 
The source code use relative path for the header files and lib files. Please refer to the source code for the relative path, or changed them to the path you want.
Execute Prerequisites:
.dll requested for running executable program:
•	boost_filesystem-vc90-mt-1_46_1.dll
•	boost_filesystem-vc90-mt-gd-1_46_1.dll
•	boost_python-vc90-mt-1_46_1.dll
•	boost_python-vc90-mt-gd-1_46_1.dll
•	FlyCapture2.dll
•	FlyCapture2GUI.dll
•	FlyCapture2GUI_GTK.glade
•	libiomp5md.dll
•	libsndfile-1.dll
•	opencv_core220.dll
•	opencv_core220d.dll
•	opencv_highgui220.dll
•	opencv_highgui220d.dll
•	opencv_imgproc220.dll
•	portaudio_x64.dll
