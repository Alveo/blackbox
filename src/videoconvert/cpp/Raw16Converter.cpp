#include "Raw16Converter.h"

Raw16Converter::Raw16Converter(std::string calFile, const float fps, const int stippledFormat, const int colorPros)
{
	m_raw16ImageSize = COLS*ROWS*2;  //BB2 camera has two eyes
	rectImg2AVI = new Rectification(calFile, fps, stippledFormat, colorPros);
}

Raw16Converter::~Raw16Converter()
{
	delete rectImg2AVI;
}
 
int Raw16Converter::SetFilesPath( const std::string fileName, const std::string dirName )
{
	m_raw16FilePath = fileName;
	m_aviFilePath   = dirName;

	return 0;
}

int Raw16Converter::SaveToAvi()
{
	
	rectImg2AVI->SetAviFilePath(m_aviFilePath);

	unsigned char* pRaw16Data = new unsigned char[m_raw16ImageSize];

    ////open the raw16 file 
	ifstream hRaw16File( m_raw16FilePath.c_str(), ios::in | ios::binary );

	if (!hRaw16File.is_open())
	{
		cout << "Open raw video file failed\n";
		return -1;
	}
	
	while(hRaw16File.read((char *)pRaw16Data, m_raw16ImageSize) && !hRaw16File.eof())
	{
		rectImg2AVI->RetifyImage2AVI(pRaw16Data);
	}

	hRaw16File.close();
	delete [] pRaw16Data;

	return 0;
}
