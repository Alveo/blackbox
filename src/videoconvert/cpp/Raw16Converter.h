#pragma once

#include <string>
#include <iostream>
#include <fstream>

#ifdef _MSC_VER
#include <FlyCapture2GUI.h>
#include <FlyCapture2.h>
#else
#include <flycapture/FlyCapture2GUI.h>
#include <flycapture/FlyCapture2.h>
#endif


#include "Rectification.h"

using namespace std;

#define DWORD long int
#define LARGE_INTEGER long int
#define _int64 long int

class Raw16Converter
{
private:
	static const unsigned int COLS = 640;
	static const unsigned int ROWS = 480;

	string m_raw16FilePath;
	string m_aviFilePath;

	DWORD m_raw16ImageSize;

	Rectification *rectImg2AVI;

public:
	Raw16Converter(std::string calFile, const float fps=48, const int stippledFormat=0, const int colorPros=5);
	virtual ~Raw16Converter();
    
    //using flycap AVI function to convert the raw16 data to AVI
	int SaveToAvi();
	 
	int  SetFilesPath( const std::string fileName, const std::string dirName);

};
