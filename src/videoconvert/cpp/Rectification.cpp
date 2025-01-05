#include "Rectification.h"



Rectification::Rectification( std::string calFile, const float fps, const int stippledFormat, const int colorPros )
{	
	int iMaxCols = 0;
	int iMaxRows = 0;


	
	aviOption.frameRate = fps;

	FlyCaptureStippledFormat stMethod;
	switch(stippledFormat)//there are 17-3(raw format)=14 types
	{
	case 0:
		stMethod = FLYCAPTURE_STIPPLEDFORMAT_BGGR;
		break;
	case 1:
		stMethod = FLYCAPTURE_STIPPLEDFORMAT_GBRG;
		break;
	case 2:
		stMethod = FLYCAPTURE_STIPPLEDFORMAT_GRBG;
		break;
	case 3:
		stMethod = FLYCAPTURE_STIPPLEDFORMAT_RGGB;
		break;
	case 4:
		stMethod = FLYCAPTURE_STIPPLEDFORMAT_DEFAULT;
		break;
	default:
		std::cout<<"Chose wrong FlyCapture Stippled Format."<<std::endl;
		return;
		break;
	}
	
	FlyCaptureColorMethod cpMethod;
	switch(colorPros)
	{
	case 0:
		cpMethod = FLYCAPTURE_DISABLE;
		break;
	case 1:
		cpMethod = FLYCAPTURE_EDGE_SENSING;
		break;
	case 2:
		cpMethod = FLYCAPTURE_NEAREST_NEIGHBOR;
		break;
	case 3:
		cpMethod = FLYCAPTURE_NEAREST_NEIGHBOR_FAST;
		break;
	case 4:
		cpMethod = FLYCAPTURE_RIGOROUS;
		break;
	case 5:
		cpMethod = FLYCAPTURE_HQLINEAR;
		break;
	default:
		std::cout<<"Chose wrong color processing alogrithm."<<std::endl;
		return;
		break;
	}

	// flycapture initialisation
	fe = flycaptureCreateContext( &flycapture );
	pixelFormat = FLYCAPTURE_RAW16;

	fe = flycaptureSetColorTileFormat(flycapture, stMethod);
	fe = flycaptureSetColorProcessingMethod( flycapture, cpMethod);

	flycaptureImage.iCols = 640; 
	flycaptureImage.iRows = 480;
	flycaptureImage.bStippled = true;
	flycaptureImage.iNumImages = 2;
	flycaptureImage.pixelFormat = FLYCAPTURE_RAW16;
	flycaptureImage.iRowInc = 640*2;
	flycaptureImage.timeStamp.ulSeconds = 0;
	flycaptureImage.timeStamp.ulMicroSeconds = 0;
	flycaptureImage.videoMode = FLYCAPTURE_VIDEOMODE_640x480Y16;

	// Triclops initialisation
	// must set calibration file first to initalise the triclops context
	SetCalFile( calFile );
	// set rectified resolution to 640x480 
	te = triclopsSetResolution( triclops, 480, 640 );
	
	// Create buffers for holding the color and mono images
	rowIntColor = new unsigned char[ flycaptureImage.iCols * flycaptureImage.iRows * flycaptureImage.iNumImages * 4 ];
	rowIntMono  = new unsigned char[ flycaptureImage.iCols * flycaptureImage.iRows * flycaptureImage.iNumImages ];
}


Rectification::~Rectification(void)
{
	leftAviRecorder.AVIClose();
	rightAviRecorder.AVIClose();

	fe = flycaptureDestroyContext( flycapture );

	// Destroy the Triclops context
	te = triclopsDestroyContext( triclops ) ;

	// Delete the image buffer.
	delete [] rowIntColor;
	delete [] rowIntMono;
}

void Rectification::SetAviFilePath( const std::string dirName )
{
	leftAviFilePath  = dirName + "left";
	rightAviFilePath = dirName + "right";

	leftAviRecorder.AVIOpen(leftAviFilePath.c_str(),&aviOption);
	rightAviRecorder.AVIOpen(rightAviFilePath.c_str(),&aviOption);
}

void Rectification::SetCalFile(const std::string& calFile)
{
	char* szCalFile = new char[calFile.size()+1];
	strcpy( szCalFile, calFile.c_str() );
	HandleTriclopsError( triclopsGetDefaultContextFromFile( &triclops, szCalFile ) );
	delete[] szCalFile;
	szCalFile = NULL;	
}

void Rectification::RetifyImage2AVI(unsigned char* pRaw16Data)
{
	flycaptureImage.pData = pRaw16Data;

	// Extract information from the FlycaptureImage
	int imageCols = flycaptureImage.iCols;
	int imageRows = flycaptureImage.iRows;
	int imageRowInc = flycaptureImage.iRowInc;
	int iSideBySideImages = flycaptureImage.iNumImages;
	unsigned long timeStampSeconds = flycaptureImage.timeStamp.ulSeconds;
	unsigned long timeStampMicroSeconds = flycaptureImage.timeStamp.ulMicroSeconds;

	// Create a temporary FlyCaptureImage for preparing the stereo image
	FlyCaptureImage tempImage;
	tempImage.pData = rowIntColor;

	FlyCaptureImage tempMonoImage;
	tempMonoImage.pData = rowIntMono;

	// Convert the pixel interleaved raw data to row interleaved format
	fe = flycapturePrepareStereoImage( flycapture, flycaptureImage,  &tempMonoImage, &tempImage );
	
	// Pointers to positions in the color buffer that correspond to the beginning
	// of the red, green and blue sections
	unsigned char* redColor = NULL;
	unsigned char* greenColor = NULL;
	unsigned char* blueColor = NULL;

	redColor = rowIntColor;
	greenColor = redColor + ( 4 * imageCols );
	blueColor = redColor + ( 4 * imageCols );

    //// RIGHT
	te = triclopsBuildPackedTriclopsInput(
		imageCols,
		imageRows,
		imageRowInc * 4,
		timeStampSeconds,
		timeStampMicroSeconds,
		redColor,
		&colorInput );

	te = triclopsRectifyPackedColorImage( triclops, 
		TriCam_RIGHT, 
		&colorInput, 
		&colorImageRight );

	//triclopsSavePackedColorImage(&colorImageRight, "rectifiedfromrawright.ppm");
	
	FlyCapture2::Image rightImage((unsigned int)colorImageRight.nrows,(unsigned int)colorImageRight.ncols,(unsigned int)colorImageRight.rowinc,colorImageRight.data->value, (unsigned int)colorImageRight.nrows*colorImageRight.ncols*4,
		FlyCapture2::PIXEL_FORMAT_BGRU);

	f2e = rightAviRecorder.AVIAppend( &rightImage );
	if (f2e != FlyCapture2::PGRERROR_OK)
	{
		printf("error with right recorder:\n");
		printf(f2e.GetDescription());
		printf("\n");
		exit(1);
	}

	//// LEFT, note the use of greenColor
	te = triclopsBuildPackedTriclopsInput(
		imageCols,
		imageRows,
		imageRowInc * 4,
		timeStampSeconds,
		timeStampMicroSeconds,
		greenColor,
		&colorInput );
	
	// rectify the color image
	te = triclopsRectifyPackedColorImage( triclops, 
		TriCam_LEFT, 
		&colorInput, 
		&colorImageLeft );

	// Save the color rectified image to file
	//triclopsSavePackedColorImage(&colorImageLeft, "rectifiedfromrawleft.ppm");

	FlyCapture2::Image leftImage((unsigned int)colorImageLeft.nrows,(unsigned int)colorImageLeft.ncols,(unsigned int)colorImageLeft.rowinc,colorImageLeft.data->value, (unsigned int)colorImageLeft.nrows*colorImageLeft.ncols*4,
		FlyCapture2::PIXEL_FORMAT_BGRU);

	f2e = leftAviRecorder.AVIAppend( &leftImage );
	if (f2e != FlyCapture2::PGRERROR_OK)
	{
		printf("error with left recorder:\n");
		printf(f2e.GetDescription());
		printf("\n");
		exit(1);
	}  

	redColor = NULL;
	greenColor = NULL;
	blueColor = NULL; 
}