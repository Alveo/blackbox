#include "VideoCapture2.h"

VideoCapture::VideoCapture()
{ 
	m_bVideoFileWriting = false;
	m_isRecPreviewing = false;
	m_bPreviewing = false;
	m_numOfCameras = 0;

	m_bStrobeSending = false;

	m_numOfFramesCaptured = 0;

	//create writing event
	m_hWritingEvent = ::CreateEvent( NULL, TRUE, FALSE, NULL);

	//create close the file handle event
	m_hCloseFileEvent = ::CreateEvent( NULL, TRUE, FALSE, NULL);

	if( m_hWritingEvent == NULL )
	{
		throw std::runtime_error( "failed to create file writing event" );
	}

	//create file writing thread
	m_hWritingThread = ::CreateThread( NULL, 0, WritingThreadProc, this, 0, NULL );
	if( m_hWritingThread == NULL )
	{
		::CloseHandle( m_hWritingEvent );
		throw std::runtime_error( "failed to create file writing thread" );
	}

	//wait for the file writing thread really run . 
	::WaitForSingleObject( m_hWritingEvent, 5000 );
};

VideoCapture::~VideoCapture()
{
	//wait for all data writing finished
	//::WaitForSingleObject( m_hWritingThread, INFINITE );
	::CloseHandle( m_hWritingThread );

	if( m_bRunning )
	{
		StopThread();
		Sleep( 20 ); // let the last capture loop has time to exit.
	}
	if( m_numOfCameras == 0 )
	{
		return;
	}
	for(int i=0;i<m_numOfCameras;i++)
	{
		if( m_ppFlyCamera[i]->IsConnected() )
		{
			StopCapture();
			StopCameras();
		}
	}

	for(int i=0;i<m_numOfCameras;i++)
	{
		delete m_ppFlyCamera[i];
		m_ppFlyCamera[i] = NULL;
	}
	delete [] m_ppFlyCamera;
	m_ppFlyCamera = NULL;
};

void VideoCapture::SetNumOfRecordingCameras(const unsigned int num)
{
	m_numOfRecordingCameras = num;
}

/** 
 * return the serial number of the given camera
 */
unsigned int VideoCapture::GetCameraSN(int index) 
{
    // only do this for index 0 or 1
    if (index < 0 || index > 1) {
        return 0;
    }
    
    unsigned int result;
    m_busMgr.GetCameraSerialNumberFromIndex( index, &result ); 
    return result;
}

int VideoCapture::StartCameras()
{
	 // Display the camera selection dialog
	/*FlyCapture2::CameraSelectionDlg camSlnDlg;
    FlyCapture2::PGRGuid arGuid[MAX_NUM_CAMERA];
    unsigned int size = MAX_NUM_CAMERA;
    bool ok;
    camSlnDlg.ShowModal( &ok, arGuid, &size );
	m_numOfCameras = size;*/
////////////////////Set the small serial number camera as the main camera
	HandleFlyError( m_busMgr.GetNumOfCameras(&m_numOfCameras) );
	unsigned int sn[MAX_NUM_CAMERA];
	for(int i=0;i<m_numOfCameras;i++)
	{
		m_busMgr.GetCameraSerialNumberFromIndex( i, &sn[i] ); 
	}

	FlyCapture2::PGRGuid arGuid[MAX_NUM_CAMERA];
	if( m_numOfCameras == 2 )
	{
		unsigned int smallSN = (sn[0]<sn[1])?sn[0]:sn[1];
		unsigned int largeSN = (sn[0]>sn[1])?sn[0]:sn[1];

		HandleFlyError( m_busMgr.GetCameraFromSerialNumber( smallSN, &arGuid[0] ) );
		HandleFlyError( m_busMgr.GetCameraFromSerialNumber( largeSN, &arGuid[1] ) );
	}
	else
	{
		HandleFlyError( m_busMgr.GetCameraFromSerialNumber( sn[0], &arGuid[0] ) );
		std::cout<<"Cameras number error"<<std::endl;
		//return -1;
	}
//////////////////////////////////////////////////////////////

	m_ppFlyCamera = new FlyCapture2::Camera*[m_numOfCameras];
	for(int i=0;i<m_numOfCameras;i++)
	{
		m_ppFlyCamera[i] = new FlyCapture2::Camera();
	}

	for(int i=0;i<m_numOfCameras;i++)
	{
		//connect to a camera
		HandleFlyError( m_ppFlyCamera[i]->Connect(&arGuid[i]) );

		FlyCapture2::CameraInfo camInfo;
		HandleFlyError( m_ppFlyCamera[i]->GetCameraInfo(&camInfo) );
		PrintCameraInfo( &camInfo );

		//get the format7 mode3 info of the camera
		FlyCapture2::Format7Info fmt7Info;
		bool fmt7Supported;
		fmt7Info.mode = IMAGE_MODE3; //format 7, mode 3 for raw16 data capture
		HandleFlyError( m_ppFlyCamera[i]->GetFormat7Info(&fmt7Info, &fmt7Supported) );
		PrintFormat7Capabilities( fmt7Info );
		
		//set the format7, raw16 pixel format
		FlyCapture2::Format7ImageSettings fmt7ImageSettings;
		fmt7ImageSettings.mode = IMAGE_MODE3;
		fmt7ImageSettings.offsetX = 0;
		fmt7ImageSettings.offsetY = 0;
		fmt7ImageSettings.width = fmt7Info.maxWidth;
		fmt7ImageSettings.height = fmt7Info.maxHeight;
		fmt7ImageSettings.pixelFormat = FlyCapture2::PIXEL_FORMAT_RAW16;
		
		bool fmt7SettingValid;
		FlyCapture2::Format7PacketInfo fmt7PacketInfo;

		// Validate the settings to make sure that they are valid
		HandleFlyError( m_ppFlyCamera[i]->ValidateFormat7Settings( &fmt7ImageSettings, &fmt7SettingValid, &fmt7PacketInfo ) );
		
		if ( !fmt7SettingValid )
		{
			// Settings are not valid
			printf("Format7 settings are not valid\n");
			return -1;
		}

		// Set the settings to the camera
		HandleFlyError( m_ppFlyCamera[i]->SetFormat7Configuration( &fmt7ImageSettings, fmt7PacketInfo.recommendedBytesPerPacket ) );

		FlyCapture2::StrobeControl sc0;
		m_ppFlyCamera[i]->GetStrobe(&sc0);

		//set the strobe control struct
		m_strobeCtrl.source   = 0;
		m_strobeCtrl.duration = 0;
		m_strobeCtrl.onOff = false;
		m_strobeCtrl.polarity = 0;
		FlyCapture2::Error e = m_ppFlyCamera[i]->SetStrobe( &m_strobeCtrl );
		m_bStrobeSending = false;

		/*//set the internal buffer
		FlyCapture2::FC2Config config;
		config.grabMode = FlyCapture2::GrabMode::BUFFER_FRAMES;
		//config.grabMode = FlyCapture2::GrabMode::DROP_FRAMES;
		config.numBuffers = 256;
		m_ppFlyCamera[i]->SetConfiguration( &config );
		//m_ppFlyCamera[i]->GetConfiguration( &config );*/
	}

	return 0;
}

int VideoCapture::StopCameras()
{
	for(int i=0;i<m_numOfCameras;i++)
	{
		HandleFlyError( m_ppFlyCamera[i]->Disconnect() );
	}
	return 0;
};

int VideoCapture::CreateFiles( const std::string folderPath, const std::string fileName )
{
	for( unsigned i = 0; i < m_numOfRecordingCameras; i++ )
    {
		char tempFilename[256];
	    //sprintf_s( tempFilename, "%sCamera-%d-%s.raw16", folderPath.c_str(),i,fileName.c_str() );
		sprintf_s( tempFilename, "%s%s-camera-%d.raw16", folderPath.c_str(),fileName.c_str(),i );

	 	// Create files to write. Later use the handles in m_hFile[] to write 
		m_hFile[i] = CreateFile( 
		(LPCTSTR)tempFilename,          
		GENERIC_WRITE,          
		0,                      
		NULL,                   
		CREATE_ALWAYS,          
		FILE_ATTRIBUTE_NORMAL | 
		FILE_FLAG_WRITE_THROUGH,
		NULL);
	
		if ( m_hFile[i] == INVALID_HANDLE_VALUE ) 
		{
			throw std::runtime_error("create raw video file failed");	 
			return -1;
		}
	}

   return 0;
}

int VideoCapture::StartCapture()
{
	//HandleFlyError( FlyCapture2::Camera::StartSyncCapture( m_numOfCameras, 
	//								(const FlyCapture2::Camera**)m_ppFlyCamera ) );
	for(int i=0;i<m_numOfCameras;i++)
	{
		HandleFlyError( m_ppFlyCamera[i]->StartCapture() );
	}
	
	std::ofstream exitCapLogFile("testExitCapLog.txt", std::ios::app);
	SYSTEMTIME cTime;
	GetLocalTime(&cTime);
	exitCapLogFile<<std::endl;
	exitCapLogFile<<"Beginning Hours:"<<cTime.wHour<<" minutes:"<<cTime.wMinute<<" seconds:"<<cTime.wSecond<<std::endl;

	FlyCapture2::Image img0;//used for release the images in the buffer
	FlyCapture2::Image img1;

	int fCounter = 0;
	static int FACTOR8 = 8;
	while(m_bRunning)
	{
		//file writing should be in a seperate thread
		if( m_bVideoFileWriting )
		{ 
			if(m_bPreviewing)//only stop full preview automatically when previewing. There is 20ms waiting.
			{
				m_bPreviewing = false;
			}
			//start to send camera strobe of the camera0
			if( !m_bStrobeSending )
			{
				m_strobeCtrl.source   = 0;
				m_strobeCtrl.duration = 0;
				m_strobeCtrl.onOff = true;
				m_strobeCtrl.polarity = 0;
				HandleFlyError( m_ppFlyCamera[0]->SetStrobe(&m_strobeCtrl) );
				HandleFlyError( m_ppFlyCamera[1]->SetStrobe(&m_strobeCtrl) );

				m_bStrobeSending = true;
			}

			boost::shared_ptr<FlyCapture2::Image> raw16Image0( new FlyCapture2::Image );
			HandleFlyError( m_ppFlyCamera[0]->RetrieveBuffer(raw16Image0.get()) );
			boost::shared_ptr<FlyCapture2::Image> raw16Image1;
			if( m_numOfRecordingCameras == 2 )
			{	
				raw16Image1.reset( new FlyCapture2::Image );
				HandleFlyError( m_ppFlyCamera[1]->RetrieveBuffer( raw16Image1.get()) );
			}else
			{//to empty the internal buffer
				HandleFlyError( m_ppFlyCamera[1]->RetrieveBuffer( &img1 ) );
				img1.ReleaseBuffer();
			}
			if(m_isRecPreviewing)
			{
				if(fCounter%FACTOR8 == 0) //show only one image in every 8 frames
				{
					Preview(raw16Image0.get());
				}
				fCounter++;
			}
			else
			{
				//cvDestroyWindow(m_recPreWinName.c_str());
			}

			//for one camera only. 
			Locker locker(this);
			m_rawQueueCamera0.push_back( raw16Image0 );
			// Write files for map task
			if( m_numOfRecordingCameras == 2 )
			{	
				m_rawQueueCamera1.push_back( raw16Image1 );
			}	
			::SetEvent( m_hWritingEvent );
		}
		else 
		{	
			HandleFlyError( m_ppFlyCamera[0]->RetrieveBuffer(&img0) );
			HandleFlyError( m_ppFlyCamera[1]->RetrieveBuffer(&img1) );
			img0.ReleaseBuffer();
			img1.ReleaseBuffer();

			//if set m_bPreviewing true from outside of the running thread, and not 
			//writing the files on hard disk, it starts preview video.
			if( m_bPreviewing )
			{
				Preview( m_videoWindowName, m_camSelector );
			}
			if(m_isRecPreviewing)
			{
				m_isRecPreviewing = false;
				cvDestroyWindow(m_videoWindowName.c_str());
			}
			if( m_bStrobeSending )// stop sending camera strobe signals.
			{
				m_strobeCtrl.source   = 0;
				m_strobeCtrl.duration = 0;
				m_strobeCtrl.onOff = false;
				m_strobeCtrl.polarity = 0;
				HandleFlyError( m_ppFlyCamera[0]->SetStrobe(&m_strobeCtrl) );
				HandleFlyError( m_ppFlyCamera[1]->SetStrobe(&m_strobeCtrl) );
				m_bStrobeSending = false;
			}
			//::ResetEvent( m_hWritingEvent );//cause dead-lock
		}
	}
	GetLocalTime(&cTime);
	exitCapLogFile<<std::endl;
	exitCapLogFile<<"Ending Hours:"<<cTime.wHour<<" minutes:"<<cTime.wMinute<<" seconds:"<<cTime.wSecond<<std::endl;

	return 0;
};

int VideoCapture::StopCapture()
{
	for(int i=0;i<m_numOfCameras;i++)
	{
		//HandleFlyError( m_ppFlyCamera[i]->StopCapture() );
		 m_ppFlyCamera[i]->StopCapture();		
	}
	return 0;
};

//DWORD WINAPI VideoCapture::CamCtrlDlgThreadProc(LPVOID lpParameter)
//{
//	(( VideoCapture*)lpParameter)->OpenCamCtrlDlg();
//	return 0;
//}

bool VideoCapture::OpenCamCtrlDlg0()
{
//////////camera 1
	FlyCapture2::CameraControlDlg camCtrlDlg0;
	camCtrlDlg0.Connect(m_ppFlyCamera[0]);
	
	if(!camCtrlDlg0.IsVisible())
	{
		camCtrlDlg0.Show();
	}
	camCtrlDlg0.Disconnect();
	return true;
}

bool VideoCapture::OpenCamCtrlDlg1()
{
/////////camera 2
	FlyCapture2::CameraControlDlg camCtrlDlg1;
	camCtrlDlg1.Connect(m_ppFlyCamera[1]);
	
	if(!camCtrlDlg1.IsVisible())
	{
		camCtrlDlg1.Show();
	}
	camCtrlDlg1.Disconnect();
	return true;
}

int VideoCapture::Preview( const std::string videoWindowName, const int camSelector )
{
	unsigned char* pLeftRaw8Data0 = new unsigned char[RAW16_IMAGE_SIZE];
	unsigned char* pRightRaw8Data0 = new unsigned char[RAW16_IMAGE_SIZE];

	unsigned char* pLeftRaw8Data1 = new unsigned char[RAW16_IMAGE_SIZE];
	unsigned char* pRightRaw8Data1 = new unsigned char[RAW16_IMAGE_SIZE];

	cvNamedWindow( videoWindowName.c_str() );

	FlyCapture2::Image raw16Image0;
	FlyCapture2::Image raw16Image1;

	while( m_bPreviewing ) 
	{
		//only show 48/3=16 fps
		//because the decodin of the code need more time than 20ms 
		//so release more images in the buffer to do the real-time preview.
		m_ppFlyCamera[0]->RetrieveBuffer(&raw16Image0);
		m_ppFlyCamera[1]->RetrieveBuffer(&raw16Image1);
		raw16Image0.ReleaseBuffer();
		raw16Image1.ReleaseBuffer();

		m_ppFlyCamera[0]->RetrieveBuffer(&raw16Image0);
		m_ppFlyCamera[1]->RetrieveBuffer(&raw16Image1);

		//split raw16 to two raw8 rawImages
		for(int i=0; i<RAW16_IMAGE_SIZE; i++)
		{
			pLeftRaw8Data0[i/2] = raw16Image0.GetData()[i];
			i++;
			pRightRaw8Data0[i/2] = raw16Image0.GetData()[i];
		}
		for(int i=0; i<RAW16_IMAGE_SIZE; i++)
		{
			pLeftRaw8Data1[i/2] = raw16Image1.GetData()[i];
			i++;
			pRightRaw8Data1[i/2] = raw16Image1.GetData()[i];
		}

		//construct raw8 left and right images
		FlyCapture2::Image rawLeftImage0(ROWS,COLS,COLS,pLeftRaw8Data0, RAW8_IMAGE_SIZE,
			FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);
		FlyCapture2::Image rawRightImage0(ROWS,COLS,COLS,pRightRaw8Data0, RAW8_IMAGE_SIZE,
			FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);
		FlyCapture2::Image rawLeftImage1(ROWS,COLS,COLS,pLeftRaw8Data1, RAW8_IMAGE_SIZE,
			FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);
		FlyCapture2::Image rawRightImage1(ROWS,COLS,COLS,pRightRaw8Data1, RAW8_IMAGE_SIZE,
			FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);

		//convert raw8 to flycap2 rgb images
		FlyCapture2::Image convertedLeftImage;
		rawLeftImage0.Convert(FlyCapture2::PIXEL_FORMAT_BGR, &convertedLeftImage);

		FlyCapture2::Image convertedRightImage;
		rawRightImage1.Convert(FlyCapture2::PIXEL_FORMAT_BGR, &convertedRightImage);

		//convert flycap2 rgb to opencv cv::image
		cv::Mat opencvLeftImage(ROWS,COLS,CV_8UC3);
		memcpy(opencvLeftImage.data, convertedLeftImage.GetData(), convertedLeftImage.GetDataSize());
		
		cv::Mat opencvRightImage(ROWS,COLS,CV_8UC3);
		memcpy(opencvRightImage.data, convertedRightImage.GetData(), convertedRightImage.GetDataSize());

		//put rectangle and text on frames
		CvFont f;
		cvInitFont( &f, CV_FONT_VECTOR0, 0.8, 0.8, 0 , 1 );
		const char text[]="Face should be inside the rectangle";
		const char closeTxt[]="Please press 'q' to close";
		const char camTxt1[] = "Camera 1";
		const char camTxt2[] = "Camera 2";
		IplImage leftImg(opencvLeftImage);
		IplImage rightImg(opencvRightImage);
		cvPutText(&leftImg, text, cvPoint(10,30), &f, CV_RGB(255,100,100) );
		cvPutText(&leftImg, closeTxt, cvPoint(10,460), &f, CV_RGB(255,100,100) );
		cvPutText(&leftImg, camTxt1, cvPoint(90,100), &f, CV_RGB(255,100,100) );
		cvPutText(&rightImg, camTxt2, cvPoint(90,100), &f, CV_RGB(255,100,100) );
		cvRectangle(&leftImg,cvPoint(60,50), cvPoint(560,430), CV_RGB(255,100,100), 1,8,0);
		cvRectangle(&rightImg,cvPoint(60,50), cvPoint(560,430), CV_RGB(255,100,100), 1,8,0);
		
		//merge two opencv images to one single image
		cv::Mat doubleImage( opencvLeftImage.rows, opencvLeftImage.cols*2, opencvLeftImage.type() );
		opencvLeftImage.copyTo( doubleImage( cv::Rect(0,0, opencvLeftImage.cols, opencvLeftImage.rows )) );
		opencvRightImage.copyTo( doubleImage( cv::Rect(opencvLeftImage.cols,0, opencvLeftImage.cols, opencvLeftImage.rows )) );
		
		//cv::imshow(videoWindowName, doubleImage);
		IplImage img(doubleImage);
		cvShowImage(videoWindowName.c_str(), &img);
	
		raw16Image0.ReleaseBuffer();
		raw16Image1.ReleaseBuffer();

		if(cv::waitKey(1) == 'q')
		{
			m_bPreviewing = false;
			break;
		}
		
	}

	cvDestroyWindow( videoWindowName.c_str() );
	delete pLeftRaw8Data0;
	delete pRightRaw8Data0;

	return 0;
};

int VideoCapture::Preview( FlyCapture2::Image* raw16Image0)
						  //FlyCapture2::Image* raw16Image1)
{
	unsigned char* pLeftRaw8Data0 = new unsigned char[RAW16_IMAGE_SIZE];
	//unsigned char* pRightRaw8Data0 = new unsigned char[RAW16_IMAGE_SIZE];

	//unsigned char* pLeftRaw8Data1 = new unsigned char[RAW16_IMAGE_SIZE];
	//unsigned char* pRightRaw8Data1 = new unsigned char[RAW16_IMAGE_SIZE];

	cvNamedWindow( m_videoWindowName.c_str() );

	//split raw16 to two raw8 rawImages
	for(int i=0; i<RAW16_IMAGE_SIZE; i++)
	{
		pLeftRaw8Data0[i/2] = raw16Image0->GetData()[i];
		i++;
		//pRightRaw8Data0[i/2] = raw16Image0->GetData()[i];
	}
	//for(int i=0; i<RAW16_IMAGE_SIZE; i++)
	//{
		//pLeftRaw8Data1[i/2] = raw16Image1->GetData()[i];
		//i++;
		//pRightRaw8Data1[i/2] = raw16Image1->GetData()[i];
	//}

	//construct raw8 left and right images
	FlyCapture2::Image rawLeftImage0(ROWS,COLS,COLS,pLeftRaw8Data0, RAW8_IMAGE_SIZE,
		FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);
	//FlyCapture2::Image rawRightImage0(ROWS,COLS,COLS,pRightRaw8Data0, RAW8_IMAGE_SIZE,
		//FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);
	//FlyCapture2::Image rawLeftImage1(ROWS,COLS,COLS,pLeftRaw8Data1, RAW8_IMAGE_SIZE,
		//FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);
	//FlyCapture2::Image rawRightImage1(ROWS,COLS,COLS,pRightRaw8Data1, RAW8_IMAGE_SIZE,
		//FlyCapture2::PIXEL_FORMAT_RAW8,FlyCapture2::BGGR);

	//convert raw8 to flycap2 rgb images
	FlyCapture2::Image convertedLeftImage;
	rawLeftImage0.Convert(FlyCapture2::PIXEL_FORMAT_BGR, &convertedLeftImage);

	//FlyCapture2::Image convertedRightImage;
	//rawRightImage0.Convert(FlyCapture2::PIXEL_FORMAT_BGR, &convertedRightImage);

	//convert flycap2 rgb to opencv cv::image
	cv::Mat opencvLeftImage(ROWS,COLS,CV_8UC3);
	memcpy(opencvLeftImage.data, convertedLeftImage.GetData(), convertedLeftImage.GetDataSize());
	
	//cv::Mat opencvRightImage(ROWS,COLS,CV_8UC3);
	//memcpy(opencvRightImage.data, convertedRightImage.GetData(), convertedRightImage.GetDataSize());

	//put rectangle and text on frames
	CvFont f;
	cvInitFont( &f, CV_FONT_VECTOR0, 0.8, 0.8, 0 , 1 );
	const char text[]="Face should be inside the rectangle";
	//const char closeTxt[]="Please press 'q' to close";
	const char camTxt1[] = "Camera 1";
	const char camRec[]  = "Recording...";
	const char camTxt2[] = "Camera 1";
	IplImage leftImg(opencvLeftImage);
	//IplImage rightImg(opencvRightImage);
	cvPutText(&leftImg, text, cvPoint(10,30), &f, CV_RGB(255,100,100) );
	cvPutText(&leftImg, camRec, cvPoint(10,460), &f, CV_RGB(255,100,100) );
	//cvPutText(&leftImg, closeTxt, cvPoint(10,460), &f, CV_RGB(255,100,100) );
	cvPutText(&leftImg, camTxt1, cvPoint(90,100), &f, CV_RGB(255,100,100) );
	//cvPutText(&rightImg, camTxt2, cvPoint(90,100), &f, CV_RGB(255,100,100) );
	cvRectangle(&leftImg,cvPoint(60,50), cvPoint(560,430), CV_RGB(255,100,100), 1,8,0);
	//cvRectangle(&rightImg,cvPoint(60,50), cvPoint(560,430), CV_RGB(255,100,100), 1,8,0);
	
	//merge two opencv images to one single image
	//cv::Mat doubleImage( opencvLeftImage.rows, opencvLeftImage.cols*2, opencvLeftImage.type() );
	//opencvLeftImage.copyTo( doubleImage( cv::Rect(0,0, opencvLeftImage.cols, opencvLeftImage.rows )) );
	//opencvRightImage.copyTo( doubleImage( cv::Rect(opencvLeftImage.cols,0, opencvLeftImage.cols, opencvLeftImage.rows )) );
	
	//cv::imshow(videoWindowName, doubleImage);
	//IplImage img(doubleImage);
	IplImage img(opencvLeftImage);
	cvShowImage(m_videoWindowName.c_str(), &img);

	//raw16Image0->ReleaseBuffer();
	//raw16Image1->ReleaseBuffer();

	if(cv::waitKey(1) == 'q')
	{
		//m_bPreviewing = false;
	}

	delete pLeftRaw8Data0;
	//delete pRightRaw8Data0;
	//delete pRightRaw8Data1;
	//cvDestroyWindow( wName.c_str() );

	return 0;
};

int VideoCapture::StartPreview()
{
	if( m_bVideoFileWriting )
	{
		m_isRecPreviewing = true;
	}
	else
	{
		m_bPreviewing = true;
	}
	return 0;
}

int VideoCapture::StopPreview()
{
	if( m_bPreviewing )
	{
		m_bPreviewing = false;
		Sleep(20); //20ms to let the thread have enough time to exit the last round in the loop
	}
	if(m_isRecPreviewing)
	{
		m_isRecPreviewing = false;
		Sleep(20);
	}
	return 0;
}

void VideoCapture::MoveVideoWindow(int x, int y)
{
	Sleep(100);
	HWND hWnd = (HWND) cvGetWindowHandle( m_videoWindowName.c_str() );
//	HWND hParent = ::GetParent(hWnd);
//	::SetWindowPos( hParent, HWND_TOPMOST, x, y, 0,0, SWP_NOSIZE);
}

int VideoCapture::SetVideoWindowName( const std::string name )
{
	m_videoWindowName = name;
	return 0;
}
int VideoCapture::SelectFirstCamera()
{
	return m_camSelector = 0;
}
int VideoCapture::SelectSecondCamera()
{
	if( m_numOfCameras>1 )
		return m_camSelector = 1;
	else
	{
		//std::cout<<"please select both cameras"<<std::endl;
		return -1;
	}
}

////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////

DWORD WINAPI VideoCapture::WritingThreadProc(LPVOID lpParameter)
{
	(( VideoCapture*)lpParameter)->WriteVideoFiles();
	return 0;
}

void VideoCapture::WriteVideoFiles()
{
	//notify the constrctor that the writing thread is already started
	::SetEvent( m_hWritingEvent );

	DWORD  ardwBytesWritten;
	unsigned int iImageSize = 614400; //ROWS*COLS*2

	//define a temp img to hold the raw 16 data from the grabbed queue. 
	//This can reduce the grabbed queue locked time dramatically.
	boost::shared_ptr<FlyCapture2::Image> tempImg0(new FlyCapture2::Image);
	boost::shared_ptr<FlyCapture2::Image> tempImg1(new FlyCapture2::Image);

	bool bGotRawImg0 = false;
	bool bGotRawImg1 = false;

	int numFrames = 0;
	int numFinQueue = 0;
	bool bFileWriting = true;

	std::ofstream exitLogFile("testExitWriteLog.txt", std::ios::app);
	SYSTEMTIME cTime;
	GetLocalTime(&cTime);
	exitLogFile<<std::endl;
	exitLogFile<<"Beginning Hours:"<<cTime.wHour<<" minutes:"<<cTime.wMinute<<" seconds:"<<cTime.wSecond<<std::endl;

	while( bFileWriting )
	{		
		if( numFinQueue < m_rawQueueCamera0.size() )
		{
			std::ofstream queueLogFile("testQLog.txt", std::ios::app);
			SYSTEMTIME curTime;
			GetLocalTime(&curTime);
			queueLogFile<<std::endl;
			queueLogFile<<"Hours:"<<curTime.wHour<<" minutes:"<<curTime.wMinute<<" seconds:"<<curTime.wSecond<<std::endl;
			numFinQueue = m_rawQueueCamera0.size();		
			queueLogFile<<"THe biggest number of frames in the queue is: "<< numFinQueue<<std::endl;
			queueLogFile.close();
		}
		::WaitForSingleObject( m_hWritingEvent, 3000 );
		{
			Locker locker(this);
			if( !m_rawQueueCamera0.empty() )
			{
				//wait for 10ms to make sure processing started to avoid dead lock.
				::WaitForSingleObject( m_hWritingEvent, 10 ); 
				
				//Dequeue the raw data queue
				tempImg0 = m_rawQueueCamera0.front();
				m_rawQueueCamera0.pop_front();
				bGotRawImg0 = true;

				::ResetEvent( m_hCloseFileEvent );
			}
			if( !m_rawQueueCamera1.empty() )
			{
				//wait for 10ms to make sure processing started to avoid dead lock.
				::WaitForSingleObject( m_hWritingEvent, 10 ); 
				
				//Dequeue the raw data queue
				tempImg1 = m_rawQueueCamera1.front();
				m_rawQueueCamera1.pop_front();
				bGotRawImg1 = true;

				::ResetEvent( m_hCloseFileEvent );
			}
		}

		if( bGotRawImg0  )
		{
			BOOL bWriteFileSuccess = WriteFile(
								m_hFile[0], 
								tempImg0.get()->GetData(),
								iImageSize,
								&ardwBytesWritten, 
								NULL ); 
	
			bGotRawImg0 = false;
		}

		if( bGotRawImg1  )
		{
			BOOL bWriteFileSuccess = WriteFile(
								m_hFile[1], 
								tempImg1.get()->GetData(),
								iImageSize,
								&ardwBytesWritten, 
								NULL ); 
	
			bGotRawImg1 = false;
		}

		//when queues are empty and capture thread exit then exit.
		{
			Locker lock(this);
			// when queue is empty, reset the event to allow some time to release CPU
			//avoid deadlock.
			if( m_rawQueueCamera0.empty() && m_rawQueueCamera1.empty() )
			{
				::ResetEvent( m_hWritingEvent );

				::SetEvent( m_hCloseFileEvent );

				if(!m_bRunning)
				{
					bFileWriting = false;
				}
			}
		}
	}
	//tempImg0.reset();
	//tempImg1.reset();
	GetLocalTime(&cTime);
	exitLogFile<<std::endl;
	exitLogFile<<"Ending Hours:"<<cTime.wHour<<" minutes:"<<cTime.wMinute<<" seconds:"<<cTime.wSecond<<std::endl;
}


void VideoCapture::PrintDiskInfo()
{
	DWORD dwSectPerClust;
	DWORD dwBytesPerSect;
	DWORD dwFreeClusters;
	DWORD dwTotalClusters;
   
	GetDiskFreeSpace (NULL, 
		&dwSectPerClust,
		&dwBytesPerSect, 
		&dwFreeClusters,
		&dwTotalClusters);
   
	printf( "This disk drive has:\n" );
	printf( "%d Total clusters\n", dwTotalClusters );
	printf( "%d Free clusters\n", dwFreeClusters );
	printf( "%d bytes/sector\n", dwBytesPerSect);
	printf( "%d sectors/cluster\n", dwSectPerClust );
   
	double dTotalSizeBytes = (double)dwTotalClusters * dwSectPerClust * dwBytesPerSect;
	double dTotalSizeGB = dTotalSizeBytes / ( 1024 * 1024 * 1024 );
	printf( "%.0lf bytes (%.2lfGB) total size\n", dTotalSizeBytes, dTotalSizeGB);
   
	double dFreeBytes = (double)dwFreeClusters * dwSectPerClust * dwBytesPerSect;
	double dFreeGB = dFreeBytes / ( 1024 * 1024 * 1024 );
	printf( "%.0lf bytes (%.2lfGB) free \n", dFreeBytes, dFreeGB);
	printf( "\n");
};

void VideoCapture::PrintBuildInfo()
{
    FlyCapture2::FC2Version fc2Version;
	FlyCapture2::Utilities::GetLibraryVersion( &fc2Version );
    char version[128];
    sprintf( 
        version, 
        "FlyCapture2 library version: %d.%d.%d.%d\n", 
        fc2Version.major, fc2Version.minor, fc2Version.type, fc2Version.build );

    printf( "%s", version );

    char timeStamp[512];
    sprintf( timeStamp, "Application build date: %s %s\n\n", __DATE__, __TIME__ );

    printf( "%s", timeStamp );
	printf( "\n");
}

void VideoCapture::PrintCameraInfo( FlyCapture2::CameraInfo* pCamInfo )
{
    printf(
        "\n*** CAMERA INFORMATION ***\n"
        "Serial number - %u\n"
        "Camera model - %s\n"
        "Camera vendor - %s\n"
        "Sensor - %s\n"
        "Resolution - %s\n"
        "Firmware version - %s\n"
        "Firmware build time - %s\n\n",
        pCamInfo->serialNumber,
        pCamInfo->modelName,
        pCamInfo->vendorName,
        pCamInfo->sensorInfo,
        pCamInfo->sensorResolution,
        pCamInfo->firmwareVersion,
        pCamInfo->firmwareBuildTime );
}

void VideoCapture::PrintFormat7Capabilities( FlyCapture2::Format7Info fmt7Info )
{
    printf(
        "Max image pixels: (%u, %u)\n"
        "Image Unit size: (%u, %u)\n"
        "Offset Unit size: (%u, %u)\n"
        "Pixel format bitfield: 0x%08x\n",
        fmt7Info.maxWidth,
        fmt7Info.maxHeight,
        fmt7Info.imageHStepSize,
        fmt7Info.imageVStepSize,
        fmt7Info.offsetHStepSize,
        fmt7Info.offsetVStepSize,
        fmt7Info.pixelFormatBitField );
}

