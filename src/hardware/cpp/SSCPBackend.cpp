
#pragma once

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python.hpp>

#include <list>
#include <vector>
#include <string>
#include <memory>
#include <iostream>
#include <sstream>
#include <windows.h>

#include "AudioRecord.h"
#include "VideoCapture2.h"
#include "Utility.h"
#include "ThreadLockBase.h"

#include <portaudio/portaudio.h>
#include <sndfile/sndfile.hh>

#include <fstream>

using namespace boost::python;

//!The Backend class is the interface class for Python to achieve the audio/video recording.

class Backend
{
private:
	//! Audio recording object
	AudioRecord		m_audioR;

	//! video recording/preview object
	VideoCapture    m_videoR;

	//! File checking utility tool 
	Utility         m_utility;

	//! The directory name which a/v files will save in
	std::string m_dirName;

	//! The a/v files base name which will be added with suffix
	std::string m_baseName;

public:
	//!Activates the camera and audio devices and set the process to HIGH_PRIORITY_CLASS.
	int Initialise()
	{
		//set the process priority from NORMAL TO HIGH
		HANDLE hThisProcess = GetCurrentProcess();
		SetPriorityClass( hThisProcess, HIGH_PRIORITY_CLASS );

		m_videoR.m_bVideoFileWriting = false;
		m_videoR.StartCameras();
		m_videoR.StartThread();

		return 0;
	}

	//!Starts a recording with audio/video. It will only use one camera which has the smaller serial number.
	/*!
	\param dirName The directory name of files. Should be like 'd:/temp/"
	\param baseName The base name of all files. Back end would add the suffix.
	It will check if there is aleady a video file exists with the same name. If yes, add -n in the base name to avoid
		rewriting the existing audio/video files.
	*/
	int StartRecording( std::string dirName, std::string baseName )
	{
		//check if there already file recorded, if yes, add -n to the baseName
		std::string fileName = baseName + "-camera-0.raw16";
		fs::path filePath(dirName+fileName);
		while( fs::exists( filePath ) )
		{
			baseName += "-n";
			fs::path newFilePath( dirName + baseName + "-camera-0.raw16" );
			filePath = newFilePath;
		}
		m_videoR.SetNumOfRecordingCameras(1);
		m_videoR.CreateFiles( dirName, baseName );
		m_videoR.m_numOfFramesCaptured = 0;

		m_audioR.StartRecord( dirName, baseName );
		Sleep(150);
		m_videoR.m_bVideoFileWriting = true;

		m_dirName  = dirName;
		m_baseName = baseName;

		return 0;
	}

	//!Starts the map task recording. This will use both of cameras, the camera 0 is the main camera in front of the speaker.
	/*!
	\param dirName The directory name of files. Should be like 'd:/temp/"
	\param baseName The base name of all files. Back end would add the suffix.
		It will check if there is aleady a video file exists with the same name. If yes, add -n in the base name to avoid
		rewriting the existing audio/video files.
	*/
	int StartMapTaskRecording( std::string dirName, std::string baseName )
	{
		std::string fileName = baseName + "-camera-0.raw16";
		fs::path filePath(dirName+fileName);
		while( fs::exists( filePath ) )
		{
			baseName += "-n";
			fs::path newFilePath( dirName + baseName + "-camera-0.raw16" );
			filePath = newFilePath;
		}
		m_videoR.SetNumOfRecordingCameras(2);
		m_videoR.CreateFiles( dirName, baseName );
		m_videoR.m_numOfFramesCaptured = 0;

		m_audioR.StartRecord( dirName, baseName );
		Sleep(150);
		m_videoR.m_bVideoFileWriting = true;

		m_dirName  = dirName;
		m_baseName = baseName;

		return 0;
	}

	//!Stop recording and check if the audio/video files are empty. Can stop both kinds of recording.
	/*!
	\return If the recording files are not empty, returns 0. Empty and not existing return minus.\n
	 Not existing returns -1;\n
	 Audio files empty returns -2;\n
	 Video Files empty returns -3;
	*/
	int StopRecording()
	{
		std::ofstream logFile("testLog.txt",std::ios::app);
		logFile<<"  "<<std::endl;
		logFile<<"Stopped a recording."<<std::endl;
		m_videoR.m_bVideoFileWriting = false;
		for( int i=0; i<m_videoR.m_numOfRecordingCameras; i++)
		{
			logFile<<"Start to wait for the m_hCloseFileEvent."<<std::endl;
			//::WaitForSingleObject( m_videoR.m_hCloseFileEvent, INFINITE );
			if(::WaitForSingleObject( m_videoR.m_hCloseFileEvent, 2000 )==WAIT_TIMEOUT)
			{
				logFile<<"2s time out QUIT"<<std::endl;
			}else
			{
				if(::WaitForSingleObject( m_videoR.m_hCloseFileEvent, 2000 )==WAIT_OBJECT_0)
				{
					logFile<<"m_hCloseFileEvent SIGNALED"<<std::endl;
				}
			}
			logFile<<"Got the m_hCloseFileEvent."<<std::endl;
			CloseHandle( m_videoR.m_hFile[i] );

			logFile<<"Closed one video file handle."<<std::endl;
		}
		logFile<<"Closing audio files."<<std::endl;
		logFile.close();
		std::cout<<m_videoR.m_numOfFramesCaptured<<std::endl;
		Sleep(150);
		m_audioR.StopRecord();
		Sleep(100);

		return	m_utility.CheckItemFilesSize( m_dirName, m_baseName );
	}

	//!Stop yes answered recording in the opening/closing component and check if the audio/video files are empty.It will add Yes suffix to the end of each file.
	/*!
	\return If the recording files are not empty, returns 0. Empty and not existing return minus.\n
	 Not existing returns -1;\n
	 Audio files empty returns -2;\n
	 Video Files empty returns -3;
	*/
	int StopRecordingYes()
	{
		int error = StopRecording();
		m_utility.ChangeFileNamesYes( m_dirName, m_baseName );
		return error;
	}

	//!Stop no answered recording in the opening/closing component and check if the audio/video files are empty. It will add No suffix to the end of each file.
	/*!
	\return If the recording files are not empty, returns 0. Empty and not existing return minus.\n
	 Not existing returns -1;\n
	 Audio files empty returns -2;\n
	 Video Files empty returns -3;
	*/
	int StopRecordingNo()
	{
		int error = StopRecording();
		m_utility.ChangeFileNamesNo( m_dirName, m_baseName );
		return error;
	}

	//! Check the video devices by recording 1 second video data and check the size of data.
	int CheckVideoDevice()
	{
		m_utility.CreateTempFolder();
		std::string folder = m_utility.GetCurrentPath() + "/Temp/";
		m_videoR.CreateFiles( folder, "Test");
		m_videoR.m_bVideoFileWriting = true;
		Sleep( 1000 );
		m_videoR.m_bVideoFileWriting = false;
		for( int i=0; i<m_videoR.m_numOfCameras; i++)
		{
			CloseHandle( m_videoR.m_hFile[i] );
		}
		
		int error = CheckDirectory( folder );
		m_utility.RemoveTempFolder();
		return error;
	}

	//! Check the audio device by recording 1 second audio data and check the size of data.
	int CheckAudioDevice()
	{
		m_utility.CreateTempFolder();
		std::string folder = m_utility.GetCurrentPath() + "/Temp/";
		m_audioR.StartRecord( folder, "Test" );
		Sleep(1000);
		m_audioR.StopRecord();

		int error = CheckDirectory( folder );
		m_utility.RemoveTempFolder();
		return error;
	}

	//! Check the free space if it's larger than 200GB in the dirName locating hard disk.
	/*! If the free space is less than 200GB, returns -1, larger returns 0*/
	int CheckDiskSpace( std::string dirName )
	{
		if( m_utility.GetSpecifiedDiskFreeSpace(dirName) < 200.0 )
		{
			std::cout<<" Hard disk free space less than 200 GB, Please check it"<<std::endl;
			return -1;
		}
		else 
			return 0;
	}

	//! Check all the files in the directory if any of them is empty.
	int CheckDirectory( std::string dirName )
	{
		return m_utility.CheckFilesSize( dirName );
	}


	//! Get the number of files in the specified directory.
	int GetFilesNumber( std::string dirName )
	{
		return m_utility.GetFilesNumber( dirName );
	}

	//! Get the specified channel volume.
	////float GetVolume( int channel )
	//int24 GetVolume( int channel )
	//{
	//	float* arrV = m_audioR.GetArrVolume();
	//	return arrV[channel];
	//}

	//! Launch a seperate window named by the videoWindowName and show the specified camera real-time video.
	/*!
	\param camera The camera sequence number. The main camera which is infront of the speaker is number 0.
	\param videoWindowName The preview window name.
	*/
	int StartVideoPreview( int camera, std::string videoWindowName )
	{
		m_videoR.SetVideoWindowName( videoWindowName );
		switch(camera)
		{
		case 0:
			m_videoR.SelectFirstCamera();
			break;
		case 1:
			m_videoR.SelectSecondCamera();
			break;
		default:
			std::cout<<"wrong camera number";
			break;
		}
		m_videoR.StartPreview();
		return 0;
	}

	//! Stop video preview.
	int StopVideoPreview( )
	{
		m_videoR.StopPreview();
		return 0;
	}

	//! Move the preview video window
	void MoveWindow(int x, int y)
	{
		m_videoR.MoveVideoWindow(x,y);
	}

	//!Get the number of cameras connected to the PC
	/*!
	\return The number of cameras linked to the computer.
	*/
	int GetNumOfCameras()
	{
		return m_videoR.m_numOfCameras;
	}

	//!Open the camera 1 dialog
	/*!
	\return true if the call is successful.
	*/
	bool OpenCamCtrlDlg0()
	{
		return m_videoR.OpenCamCtrlDlg0();
	}

	//!Open the camera 2 dialog
	/*!
	\return true if the call is successful.
	*/
	bool OpenCamCtrlDlg1()
	{
		return m_videoR.OpenCamCtrlDlg1();
	}
    
    
    /**
	 * Return the Serial Number of the camera camId (0 or 1)
	 */
	unsigned int GetCameraSN(const int camId)
	{
        return m_videoR.GetCameraSN(camId);
    }
    
    
}; 

BOOST_PYTHON_MODULE(SSCPBackend)
{
    class_<Backend, boost::noncopyable>("Backend")
		.def("Initialise", &Backend::Initialise )
        .def("StartRecording", &Backend::StartRecording)
		.def("StartMapTaskRecording", &Backend::StartMapTaskRecording)
        .def("StopRecording", &Backend::StopRecording)
		.def("StopRecordingYes",&Backend::StopRecordingYes)
		.def("StopRecordingNo",&Backend::StopRecordingNo)
		.def("CheckVideoDevice", &Backend::CheckVideoDevice)
		.def("CheckAudioDevice", &Backend::CheckAudioDevice)
		.def("CheckDiskSpace", &Backend::CheckDiskSpace)
		.def("CheckDirectory", &Backend::CheckDirectory)
		.def("OpenCamCtrlDlg0", &Backend::OpenCamCtrlDlg0)
		.def("OpenCamCtrlDlg1", &Backend::OpenCamCtrlDlg1)

		.def("GetFilesNumber", &Backend::GetFilesNumber)
		//.def("GetVolume", &Backend::GetVolume)
		.def("StartVideoPreview", &Backend::StartVideoPreview)
		.def("StopVideoPreview", &Backend::StopVideoPreview)	
		.def("MoveWindow", &Backend::MoveWindow)
		.def("GetNumOfCameras",&Backend::GetNumOfCameras)
        .def("GetCameraSN", &Backend::GetCameraSN)
    ;
}
