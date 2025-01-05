/*****************************************************************************
*Organisation: MARCS of UWS
*Project: The Big ASC
*
*File name: VideoCapture2
*Abstract:  Capture video from two cameras and save raw16 to files
*			It uses the FlyCap2 SDK
*          
*
*Programmer: Lei Jing
*Version: 1.0.1
*Last update time: 18.4.2011
******************************************************************************/

#ifndef _VIDEO_CAPTURE2_H_
#define _VIDEO_CAPTURE2_H_

#define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers

#include <list>
#include <vector>
#include <string>
#include <memory>
#include <iostream>
#include "windows.h"

#include <fstream>
#include <boost/shared_ptr.hpp>
#include <boost/thread/thread.hpp>  
#include "ThreadLockBase.h"

#ifdef _MSC_VER
#include <FlyCapture2GUI.h>
#include <FlyCapture2.h>
#else
#include <flycapture/FlyCapture2GUI.h>
#include <flycapture/FlyCapture2.h>
#endif

#include <opencv2.2/opencv.hpp>



//! Capture stream to memory buffer and preview video from two cameras.

class VideoCapture : public ThreadBase, public Lockable
{
private:
	//! StartSyncCapture and write to files
	int StartCapture();
	
	//! Handle the error returned from flycap sdk, throw run time error
	inline void HandleFlyError( FlyCapture2::Error flyError )
	{
		if( flyError != FlyCapture2::PGRERROR_OK )
		{
			char err[200];
			sprintf( err, "\nDescription: %s. \nHappened in the file: %s, \nline: %d.", 
								flyError.GetDescription(), flyError.GetFilename(), flyError.GetLine() );

			std::cout<<"Error: "<<err<<std::endl;
			std::ofstream fcErrLogFile("testFCerrLog.txt", std::ios::app);
			SYSTEMTIME cTime;
			GetLocalTime(&cTime);
			fcErrLogFile<<std::endl;
			fcErrLogFile<<"Flycap error happened. Hours:"<<cTime.wHour<<" minutes:"<<cTime.wMinute<<" seconds:"<<cTime.wSecond<<std::endl;
			throw std::runtime_error( err );
		}
	};

	
	//! Maximum number of cameras 2
	static const int MAX_NUM_CAMERA = 2;

	//! FlyCap image mode3, format7.
	static const FlyCapture2::Mode IMAGE_MODE3 = FlyCapture2::MODE_3;

	//! Pixel columns of the captured image 
	static const int COLS = 640;

	//! Pixel rows of the captured image 
	static const int ROWS = 480;

	//! Bytes of a raw16 image
	static const int RAW16_IMAGE_SIZE = COLS*ROWS*2; //bytes

	//! Bytes of a raw8 image
	static const int RAW8_IMAGE_SIZE  = COLS*ROWS;
	
	//! Pointers of FlyCap Camera class in array.
	FlyCapture2::Camera**  m_ppFlyCamera;

	//! Flycap bus manager to connect cameras.
	FlyCapture2::BusManager m_busMgr;

	//! The preview window name.
	std::string m_videoWindowName;

	//! ID number of the selected camera.
	int m_camSelector;

	//! The strobe control settings of the main camera.
	FlyCapture2::StrobeControl m_strobeCtrl;

public:
	//! Constructor.
	VideoCapture();

	//! Destructor.
	~VideoCapture();

    //! Get the serial number of the given camera (0 or 1)
    unsigned int VideoCapture::GetCameraSN(int index);
    
	//! Set the number of cameras will be used in the recording
	void SetNumOfRecordingCameras(const unsigned int num);

	//! Connect to cameras and set the format7 mode3 and raw16
	int StartCameras();

	//! Create video files with the fileName as base name in the specified folder path.
	/*!
	\param folderPath The directory which video files will locate. Must finish with '/'. e.g. d:/dir/.  
	\param fileName The base file name.
	
	* The format of the absolute video file path:\n
		- dirname + basename + "-camera-0.raw16";
	*/
	int CreateFiles( const std::string folderPath, const std::string fileName );

	//! Set the window name for the video preview.
	int SetVideoWindowName( const std::string name );

	//! Choose the first #0 camera.
	int SelectFirstCamera();

	//! Choose the second #1 camera.
	int SelectSecondCamera();

	//! Preview video of the selected camera
	/*!
	\param videoWindowName The name of the preview window.
	\param camSelector The sequence number of the camera. 0 is for the main camera. 1 is for map task only camera.
	*/
	int Preview( const std::string videoWindowName, const int camSelector );

	//! Preview video of the selected camera
	/*!
	\param videoWindowName The name of the preview window.
	
	*/
	int Preview( FlyCapture2::Image* raw16Image0);
				 //FlyCapture2::Image* raw16Image1);
	
	//! Start the video preview in a thread by setting m_bPreviewing true.
	int StartPreview();

	//! Stop the video preview in a thread by setting m_bPreviewing false.
	int StopPreview();

	//! change the video preveiw window position
	void VideoCapture::MoveVideoWindow(int x, int y);

////////////////////////////////////////////////////////////
	//!print the disk info
	void PrintDiskInfo();
	//!print the flycap driver and system info
	void PrintBuildInfo();
	//!print the camera info
	void PrintCameraInfo( FlyCapture2::CameraInfo* pCamInfo );
	//!print the video format7 capabilities
	void PrintFormat7Capabilities( FlyCapture2::Format7Info fmt7Info );
/////////////////////////////////////////////////////////////

	//!Implement the thread worker function, start capture video to memory buffer.
	DWORD WINAPI ThreadWorker(LPVOID lpParameter)
	{
		StartCapture();
		ExitThread(0);
		return 0;
	}

	//! StopCapture from cameras, stop capture first,then camera.
	int StopCapture();

	//! Disconnect cameras.
	int StopCameras();

	//! The number of cameras connected in the computer.
	unsigned int m_numOfCameras;

	//! The status of the video file writing.
	bool m_bVideoFileWriting;

	//! The status of video preview.
	bool m_bPreviewing;

	//! The status of low fps preview when recording
	bool m_isRecPreviewing;

	//! Video file handle, maximum is the same as the maximum number of cameras.
	HANDLE m_hFile[ MAX_NUM_CAMERA ];

	//! The number of cameras used for current recording
	int m_numOfRecordingCameras;

	int m_numOfFramesCaptured;

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
	//! Writing File thread entry.
	static DWORD WINAPI WritingThreadProc( LPVOID lpParameter );

	//! Close file handle event handle
	HANDLE m_hCloseFileEvent;

	//! Camera control setting dialog
	static DWORD WINAPI CamCtrlDlgThreadProc( LPVOID lpParameter );

	//! Open the camera 1 control dialog
	bool OpenCamCtrlDlg0();

	//! Open the camera 2 control dialog
	bool OpenCamCtrlDlg1();

private:
	//! File writing main function that handles the data in the queue and write into files.
	void WriteVideoFiles();

	//! Writing thread handle 
	HANDLE m_hWritingThread;

	//! Writing event handle
	HANDLE m_hWritingEvent;

	//! The raw16 data queue of camera0 (main camera) for share data between stream capture and file writing.
	std::list<boost::shared_ptr<FlyCapture2::Image>> m_rawQueueCamera0;

	//! The raw16 data queue of camera1 (second camera for map task only) for share data between stream capture and file writing.
	std::list<boost::shared_ptr<FlyCapture2::Image>> m_rawQueueCamera1;

	//! The strobe signal sending status
	bool m_bStrobeSending;

};

#endif //_VIDEO_CAPTURE2_H_