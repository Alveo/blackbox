#pragma once
#include <iostream>
#include <string>

#include <triclops.h>
#include <pgrflycapture.h>
#include <pgrflycapturestereo.h>
 
#ifdef _MSC_VER
#include <FlyCapture2GUI.h>
#include <FlyCapture2.h>
#else
#include <flycapture/FlyCapture2GUI.h>
#include <flycapture/FlyCapture2.h>
#endif

class Rectification
{
private:
	TriclopsInput			  colorInput;
	TriclopsPackedColorImage  colorImageLeft;
	TriclopsPackedColorImage  colorImageRight;
	TriclopsContext           triclops;

	FlyCaptureContext	      flycapture;
	FlyCaptureImage	          flycaptureImage;
	FlyCaptureInfoEx	      pInfo;
	FlyCapturePixelFormat     pixelFormat;

	TriclopsError     te;
	FlyCaptureError   fe;
	FlyCapture2::Error f2e;

	static const unsigned int COLS = 640; 
	static const unsigned int ROWS = 480; 

	FlyCapture2::AVIOption aviOption;
	FlyCapture2::AVIRecorder rightAviRecorder;
	FlyCapture2::AVIRecorder leftAviRecorder;

	unsigned char* rowIntColor;
	unsigned char* rowIntMono;

	std::string leftAviFilePath;
	std::string rightAviFilePath;

	void SetCalFile(const std::string& calFile);
	
public:
	Rectification( std::string calFile, const float fps=48.0, const int stippledFormat=0, const int colorPros=5 );
	virtual ~Rectification(void);
	
	void SetAviFilePath( const std::string dirName );
	void RetifyImage2AVI(unsigned char* pRaw16Data);
	
	inline void HandleTriclopsError( TriclopsError triclopsError )
	{
		if( triclopsError != TriclopsErrorOk )
		{
			std::string err=triclopsErrorToString( triclopsError );
			std::cout<<"Error: "<<err<<std::endl;
			throw std::runtime_error( err );
		}
	};

	//! Handle the error returned from flycap sdk, throw run time error
	inline void HandleFlyError( FlyCaptureError flyError )
	{
		if( flyError != FLYCAPTURE_OK )
		{
			std::string err=flycaptureErrorToString( flyError );
			std::cout<<"Error: "<<err<<std::endl;
			throw std::runtime_error( err );
		}
	};
 

};
