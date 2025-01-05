

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python.hpp>

#include <string>
#include <iostream>
#include <sstream>
#include <fstream>

#include "Raw16Converter.h"

using namespace boost::python;

class RawConverter
{
private:


public:
	/**
	 * Save the calibration file for camera camId and return
	 * the name of the file
	 */
	std::string GetCalFile(const int camId)
	{
		FlyCaptureContext fcContext;
		flycaptureCreateContext( &fcContext );
		flycaptureInitialize( fcContext, camId );

		char* szCalFile;
		flycaptureGetCalibrationFileFromCamera( fcContext, &szCalFile );
		
		flycaptureDestroyContext( fcContext );
		
		return szCalFile;
	}
	
	/**
	 * Return the Serial Number of the camera camId (0 or 1)
	 */
	unsigned long GetCameraSN(const int camId)
	{
		FlyCaptureContext fcContext;
		flycaptureCreateContext( &fcContext );
		flycaptureInitialize( fcContext, camId );

		FlyCaptureInfoEx info;
		flycaptureGetCameraInfo( fcContext, &info );
		
		return info.SerialNumber;
	}
	
	
	inline bool RawToAvi( const float fps, const int stMethod, const int colorPros, 
		const std::string fileName, const std::string dirName, const std::string calFile )
	{
		Raw16Converter m_converter(calFile,  fps, stMethod, colorPros ); 
		m_converter.SetFilesPath( fileName.c_str(), dirName.c_str() );
		m_converter.SaveToAvi();
		return true;
	}

}; 

BOOST_PYTHON_MODULE(RawToAvi)
{
    class_<RawConverter, boost::noncopyable>("RawConverter")
		.def( "GetCalFile", &RawConverter::GetCalFile )
		.def( "GetCameraSN", &RawConverter::GetCameraSN ) 
		.def( "RawToAvi", &RawConverter::RawToAvi )
    ;
}