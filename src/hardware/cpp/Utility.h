/*****************************************************************************
*Organisation: MARCS of UWS
*Project: The Big ASC
*
*File name: Utility class
*Abstract:  a utility class to handle disk/file checking
*          
*
*Programmer: Lei Jing
*Version: 1.0.1
*Last update time: 18.4.2011
******************************************************************************/



#ifndef _UTILITY_H_
#define _UTILITY_H_
#include <boost/filesystem.hpp>
#include <string>

#define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers
#include "windows.h"


namespace fs = boost::filesystem;

//! A utility class to handle disk/file checking

class Utility
{
public:
	//! Constructor
	Utility();

	//! Destructor
	virtual ~Utility();

	//! Get the free space of the hard disk which the dirName locates.
	/*!
	\param dirName The folder path.
	\return The free space by GB.
	*/
	double GetSpecifiedDiskFreeSpace( const std::string dirName );

	//!Get the number of files in the specified directory including its subdirectories
	/*!
	\param dirName The folder path.
	\return The number of files in the directory including its subdirectories.
	*/
	int GetFilesNumber( const std::string dirName );

	//!Check the audio and video files, if any of they are too small return minus int. See the Detailed Description.
	/*! If the file is empty or too small, e.g:\n
	The audio file is less than 50KB, 1024*50/44100/4 = 0.29 second return -2;\n
	The video file is less than 8MB, 8*1024*1024/(1280*480*48) = 0.284 second, return -3.
	*/
	int CheckFilesSize( const std::string dirName );

	//!Check the size of the specified filePath file
	/*!
	\param filePath The absolute path and name of the file.
	\return If there is no such file existing, return -1.
			If the file is empty or too small not reasonalble, such as:\n
			The audio file is less than 50KB, 1024*50/44100/4 = 0.29 second return -2;\n
			The video file is less than 8MB, 8*1024*1024/(1280*480*48) = 0.284 second, return -3.
	*/
	int CheckSingleFileSize( const std::string& filePath );

	//! Check the audio/video files if empty or too small in one recording.
	int CheckItemFilesSize( const std::string& dirName, const std::string& baseName );

	//! Get the current folde path.
	std::string GetCurrentPath();

	//! Create a temp folder for testing the audio and video devices.
	int CreateTempFolder();

	//! Delete the folder and the files inside
	int RemoveTempFolder();

	//! Add Yes suffix in the files name. For the yes/no answers in the opening/closing components.
	int ChangeFileNamesYes( const std::string& dirName, const std::string& baseName );

	//! Add No suffix in the files name. For the yes/no answers in the opening/closing components.
	int ChangeFileNamesNo( const std::string& dirName, const std::string& baseName);

	//! The file names' suffix of the audio file. It should be the order of the mic
	std::vector<std::string> auSuffixes;

	//! The file names's suffix with -Yes of the audio file. It should be the order of the mic
	std::vector<std::string> auSuffixesYes;

	//! The file names's suffix with -No of the audio file. It should be the order of the mic
	std::vector<std::string> auSuffixesNo;

	//!copy the src file to the dst 
	int CopyFile( const std::string srcFile, const std::string dstFile );

};

#endif //_UTILITY_H_