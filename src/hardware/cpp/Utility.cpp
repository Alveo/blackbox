#include "Utility.h"

Utility::Utility()
{
	std::string wav = ".wav";
	std::vector<std::string> ch;
	ch.push_back("-ch1-maptask");
	ch.push_back("-ch2-boundary");
	ch.push_back("-ch3-strobe");
	ch.push_back("-ch4-c2Left");
	ch.push_back("-ch5-c2Right");
	ch.push_back("-ch6-speaker");

	int numOfChannels = 6;
	for(int i=0;i<numOfChannels;i++)
	{
		auSuffixes.push_back(ch[i]+wav);
		auSuffixesYes.push_back(ch[i]+"-yes"+wav);
		auSuffixesNo.push_back(ch[i]+"-no"+wav);
	}
}
Utility::~Utility()
{
}

double Utility::GetSpecifiedDiskFreeSpace(const std::string dirName)
{
	DWORD dwSectPerClust;
	DWORD dwBytesPerSect;
	DWORD dwFreeClusters;
	DWORD dwTotalClusters;
   
	GetDiskFreeSpace (dirName.c_str(), 
		&dwSectPerClust,
		&dwBytesPerSect, 
		&dwFreeClusters,
		&dwTotalClusters);
   
	double dTotalSizeBytes = (double)dwTotalClusters * dwSectPerClust * dwBytesPerSect;
	double dTotalSizeGB = dTotalSizeBytes / ( 1024 * 1024 * 1024 );
	printf( "%.0lf bytes (%.2lfGB) total size\n", dTotalSizeBytes, dTotalSizeGB);
   
	double dFreeBytes = (double)dwFreeClusters * dwSectPerClust * dwBytesPerSect;
	double dFreeGB = dFreeBytes / ( 1024 * 1024 * 1024 );
	printf( "%.0lf bytes (%.2lfGB) free \n", dFreeBytes, dFreeGB);
	printf( "\n");
	return dFreeGB;
}

int Utility::GetFilesNumber( const std::string dirName )
{
	fs::path path( dirName, fs::native );
	if( !fs::exists(path) )
	{
		//std::cout<<"Folder is not existing."<<std::endl;
		return -1;
	}
    fs::directory_iterator end_itr;
	int numOfFiles = 0;
	for( fs::directory_iterator itr(path); itr != end_itr; ++itr )
	{
		//if it is sub directory, recurse the counting
		if( fs::is_directory( *itr) )
		{
			fs::path dir = *itr;
			numOfFiles += GetFilesNumber( dir.string() );
		}
		else
		{
			numOfFiles++;
		}
	}

	return numOfFiles;
}

int Utility::CheckFilesSize( const std::string dirName )
{
	int err = 0;
	
	fs::path path( dirName, fs::native );
	if( !fs::exists(path) )
	{
		//std::cout<<"Folder is not existing."<<std::endl;
		return -1;
	}
    fs::directory_iterator end_itr;

	for( fs::directory_iterator itr(path); itr != end_itr; ++itr )
	{
		if( fs::is_directory( *itr) )//recurse in sub directory
		{
			fs::path dir = *itr;
			CheckFilesSize( dir.string() );
		}
		else
		{
			fs::path filePath = *itr;
			if( ".wav" == filePath.extension() )
			{
				boost::uintmax_t fileSize = fs::file_size(filePath);
				//less than 50KB return minus error, 1024*50/44100/4 = 0.29 second
				if( fileSize<50*1024 ) 
				{
					//std::cout<<"This audio file "<<filePath.string()
					//	      <<" is not normal, too small."<<std::endl;
					if( err == -3 || err == -4 )
						err = -4;
					else
						err = -2;
				}
			}
			if( ".raw16" == filePath.extension() )
			{
				boost::uintmax_t fileSize = fs::file_size(filePath);
				//less than 8MB return minus error, 8*1024*1024/(1280*480*48) = 0.284 second
				if( fileSize<8*1024*1024 ) 
				{
					//std::cout<<"This video file "<<filePath.string()
					//	      <<" is not normal, too small."<<std::endl;
					if( err == -2 || err == -4 )
						err = -4;
					else
						err = -3;
				}
			}
		}
	}
	return err;
}

int Utility::CheckSingleFileSize( const std::string& filePath )
{
	int err = 0;

	fs::path path( filePath, fs::native );
	if( !fs::exists(path) )
	{
		//std::cout<<"The file is not existing."<<std::endl;
		return -1;
	}

	if( ".wav" == path.extension() )
	{
		boost::uintmax_t fileSize = fs::file_size(filePath);
		//less than 50KB return minus error, 1024*50/44100/4 = 0.29 second
		if( fileSize<50*1024 ) 
		{
			//std::cout<<"This audio file "<<filePath
			//	      <<" is not normal, too small."<<std::endl;
			err = -2;
		}
	}
	if( ".raw16" == path.extension() )
	{
		boost::uintmax_t fileSize = fs::file_size(filePath);
		//less than 8MB return minus error, 8*1024*1024/(1280*480*48) = 0.284 second
		if( fileSize<8*1024*1024 ) 
		{
			//std::cout<<"This video file "<<filePath
			//	      <<" is not normal, too small."<<std::endl;
			err = -3;
		}
	}

	return err;
}

int Utility::CheckItemFilesSize( const std::string& dirName, const std::string& baseName )
{
	int err = 0;

	//"%s%s-camera-%d.raw16", The format of the file absolute path:
	//dirname + basename + "-camera-0.raw16";
	//Check first camera video file.
	err = CheckSingleFileSize( dirName + baseName +    "-Camera-0.raw16" );
	if( err<0 )
		return err;

	std::string camera2FilePath = dirName + baseName + "-Camera-1.raw16";
	fs::path path( camera2FilePath, fs::native );
	if( fs::exists(path) )
	{
		//err = CheckSingleFileSize( dirName + "Camera-1-" + baseName + ".raw16");
		err = CheckSingleFileSize( camera2FilePath );
		if( err<0 )
			return err;
	}

	//check audio file of one item
	for(int i=0;i<auSuffixes.size();i++)
	{
		err = CheckSingleFileSize( dirName + baseName + auSuffixes[i] );
		if( err<0 )
			return err;
	}
	
	return err;
}

std::string Utility::GetCurrentPath()
{
	fs::path path = fs::current_path();
	return path.string();
}

int Utility::CreateTempFolder()
{
	std::string strPath = GetCurrentPath() + "/Temp";
	fs::create_directory( strPath );

	return 0;
}

int Utility::RemoveTempFolder()
{
	std::string strPath = GetCurrentPath() + "/Temp";
	fs::remove_all( strPath );

	return 0;
}

int Utility::ChangeFileNamesYes( const std::string& dirName, const std::string& baseName )
{
	for(int i=0;i<auSuffixes.size();i++)
	{
		fs::path audioPath1( dirName + baseName + auSuffixes[i] );
		fs::rename( audioPath1, dirName + baseName + auSuffixesYes[i] );
	}
	fs::path audioPath1( dirName + baseName + "-camera-0.raw16" );
	fs::rename( audioPath1, dirName + baseName + "-camera-0-yes.raw16" );
	return 0;
}

int Utility::ChangeFileNamesNo( const std::string& dirName, const std::string& baseName  )
{
	for(int i=0;i<auSuffixes.size();i++)
	{
		fs::path audioPath1( dirName + baseName + auSuffixes[i] );
		fs::rename( audioPath1, dirName + baseName + auSuffixesNo[i] );
	}
	fs::path audioPath1( dirName + baseName + "-camera-0.raw16" );
	fs::rename( audioPath1, dirName + baseName + "-camera-0-no.raw16" );
	return 0;
}

int Utility::CopyFile( const std::string srcFile, const std::string dstFile )
{
	fs::path src(srcFile);
	fs::path dst(dstFile);
	if( fs::exists(dst) )
	{
		fs::rename( dst, "n-"+dstFile );
	}
	fs::copy_file(src, dst, fs::copy_option::overwrite_if_exists);  
	return 0;
}