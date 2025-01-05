


#include "AudioRecord.h"

AudioStream::AudioStream(const int device, int inputChannelSelectors[],
								      const Files & files )
:m_files( files )
{
	//portaudio init
	PaAsioStreamInfo asioInputStreamInfo;
	asioInputStreamInfo.channelSelectors = inputChannelSelectors;
	asioInputStreamInfo.flags = paAsioUseChannelSelectors;
	asioInputStreamInfo.hostApiType = paASIO;
	asioInputStreamInfo.size = sizeof(PaAsioStreamInfo);
	asioInputStreamInfo.version = 1;

	PaStreamParameters inputParameters;
	inputParameters.channelCount = m_files.size();
	inputParameters.device = device; //ASIO USB DEVICE
	inputParameters.hostApiSpecificStreamInfo = &asioInputStreamInfo;
	//inputParameters.sampleFormat = paFloat32;
	//inputParameters.sampleFormat = paInt24;
	inputParameters.sampleFormat = paInt32;
	inputParameters.suggestedLatency = 
		Pa_GetDeviceInfo(inputParameters.device)
			->defaultLowInputLatency;
	
	PaError err = Pa_OpenStream( &m_paStream,
              &inputParameters,
              NULL,                  /* &outputParameters, */
              44100,
              FRAMES_PER_BUFFER,
              paClipOff,      /* won't output out of range samples so don't bother clipping them */
              PaRecordCallback,
              this );
    if( err != paNoError )
		throw std::runtime_error( "failed to open a stream" );

	// Create event
	m_event = ::CreateEvent( NULL, TRUE, FALSE, NULL );
	if( m_event == NULL )
	{
		Pa_CloseStream( m_paStream );
		throw std::runtime_error( "failed to create event" );
	}

	// Create thread
	m_thread = ::CreateThread( NULL, 0, ThreadProc, this, 0, NULL );
	if( m_thread == NULL )
	{
		::CloseHandle( m_event );
		Pa_CloseStream( m_paStream );
		throw std::runtime_error( "failed to create thread" );
	}

	//m_arrVolume = new float[6];
	//m_arrVolume = new int24[6];
	/*for( int i=0; i<6; i++ )
	{
		m_arrVolume[i] = 0.0;
	}*/

	// Wait for the thread to really run
	::WaitForSingleObject( m_event, INFINITE );
}

AudioStream::~AudioStream()
{
    // Closes the audio stream, that means no more callback will arrive
	Pa_CloseStream( m_paStream );
	m_paStream = NULL;

    // Waits for the thread to handle all data in the queue and quit, then closes the thread
	::WaitForSingleObject( m_thread, INFINITE );
	::CloseHandle( m_thread );
	//::CloseHandle();
	//delete [] m_arrVolume;
}

DWORD WINAPI AudioStream::ThreadProc( LPVOID lpParameter )
{
	((AudioStream*)lpParameter)->main();
	return 0;
}

void AudioStream:: main()
{
	// Notifies the constructor that the thread is already started
	::SetEvent( m_event );

	// Notifies the audio stream to start streaming
	Pa_StartStream( m_paStream );
	m_currentFile = 0;

	// Defines a queue to temporarily hold the audio data
	//std::vector<float> * buffers = new std::vector<float>[ m_files.size() ];
	//std::vector<int24> * buffers = new std::vector<int24>[ m_files.size() ];
	std::vector<AUDIO_FORMAT> * buffers = new std::vector<AUDIO_FORMAT>[ m_files.size() ];
	//int numOfBuffer = 0;
	while( true )
	{
		// Locks the class to access the shared m_queue
		{
			Locker locker(this);

			// Wait for the signal to start processing for 10ms, but start procesing anyway after that due time to avoid any deadlock issue
			::WaitForSingleObject( m_event, 10 );

			// Dequeues audio data and split the data to multiple files' queue ( temporary queues defined above)
			while( m_queue.size() )
			{
				//counter += m_queue.front().size();
				for( int i = 0; i < m_queue.front().size(); i++ )
				{
					buffers[m_currentFile].push_back( m_queue.front()[i] );
					m_currentFile++;
					m_currentFile %= m_files.size();
				}
				m_queue.pop_front();
			}

			// When the queue is empty, reset the event to allow 10ms waiting above to release CPU time
			::ResetEvent( m_event );
		}

		// Handles the splitted files queues and call writing functions on files
		//numOfBuffer++;
		for( int i=0; i<m_files.size();i++)
		{
			if( buffers[i].size() )
			{
				//m_files[i]->writeRaw( &buffers[i][0], sizeof( float )*buffers[i].size() );
				//m_files[i]->writeRaw( &buffers[i][0], sizeof( int24 )*buffers[i].size() );
				m_files[i]->writeRaw( &buffers[i][0], sizeof( AUDIO_FORMAT )*buffers[i].size() );
				//m_arrVolume[i] = buffers[i][0];
			}
			buffers[i].clear();
		}
		{
			Locker locker(this);
			if( m_paStream == NULL && m_queue.empty() )
				break;
		}
	}
	delete [] buffers;
}

int AudioStream::RecordCallback(const void *inputBuffer, 
				   void *outputBuffer,
				   unsigned long framesPerBuffer,
                   const PaStreamCallbackTimeInfo* timeInfo,
                   PaStreamCallbackFlags statusFlags )
{
	// Creates buffer to copy received data into it
	//std::vector< float > temp;
	//std::vector< int24 > temp;
	std::vector< AUDIO_FORMAT > temp;
	for( unsigned long i = 0; i < framesPerBuffer*m_numOfChannel; i++ )
	{
		//temp.push_back( *(((float *)inputBuffer)+i)  );
		temp.push_back( *(((AUDIO_FORMAT *)inputBuffer)+i)  );
	}
	 // Locks the shared queue and enqueue the buffer
	Locker locker(this);
	m_queue.push_back( temp );
	// Triggers the worker thread to handle the queue
	::SetEvent( m_event );
	return 0;
}

int AudioStream::SetNumOfChannel(const int numOfChannel)
{
	m_numOfChannel = numOfChannel;
	return 0;
}

//////////////////////////////////////////////////////////////////////////

Lockable AudioRecord::m_lock;
int AudioRecord::m_initCounter = 0;

AudioRecord::AudioRecord()
{
	//Locker locker( this );
	// Locks the class to access static m_initCounter
	Locker locker( &m_lock );
	if( m_initCounter++ == 0 )
	{
		 // Only initialzes the paaudio lib once
		PaError err = Pa_Initialize();
		if( err != paNoError )
		{
			m_initCounter--;
			throw  std::runtime_error( "failed initialize PA lib" );
		}
	}
	m_bRecording = false;
	m_iAsioDeviceId = GetAsioDeviceId();
	if( m_iAsioDeviceId == -1 )
	{
		std::cout<< "The ASIO device has not been found." <<std::endl;
	}
}

AudioRecord::~AudioRecord()
{
	//StopRecord();

    // Locks the class to access static m_initCounter
	Locker locker( this );

	if( m_audioStream.get()!= NULL )
	{
		// Closes the stream
		m_audioStream.reset();
	}

	// Closes files of audio data
	for( AudioStream::Files::iterator i = m_files.begin(); i!= m_files.end(); i++ )
	{
		delete *i;
	}
	m_files.clear();
	m_bRecording = false;

    // Only uninitialzes the audio lib once
	if( --m_initCounter == 0 )
	{
		Pa_Terminate();
	}
}

int AudioRecord::GetAsioDeviceId()
{
	int asioDeviceId = -1;
	int numDevices = Pa_GetDeviceCount();
	const   PaDeviceInfo *deviceInfo;
	for( int i=0; i<numDevices; i++ )
	{
		deviceInfo = Pa_GetDeviceInfo( i );
		//compare two strings 
		if( strcmp( "ASIO", Pa_GetHostApiInfo( deviceInfo->hostApi )->name) == 0 )
		{
			std::cout<< "This is the ASIO device. ID: "<<i<<std::endl;
			asioDeviceId = i; 
		}
	}
	m_iAsioDeviceId = asioDeviceId;
	return asioDeviceId;
}

void AudioRecord::StartRecord( const std::string &folderPath, const std::string &fileName )
{
	std::cout<<" start audio recording......"<<std::endl;
	int numOfChannel = 6;
	if( numOfChannel != 6 )
	{
		throw std::runtime_error( "The number of channels must be 6! " );
		return;
	}

	//set the six channels audio file absolute path.
	std::vector< std::string > vFileNames;
	std::string ch1("-ch1-maptask.wav");
	std::string ch2("-ch2-boundary.wav");
	std::string ch3("-ch3-strobe.wav");
	std::string ch4("-ch4-c2Left.wav");
	std::string ch5("-ch5-c2Right.wav");
	std::string ch6("-ch6-speaker.wav");

	vFileNames.push_back( folderPath + fileName + ch1 );
	vFileNames.push_back( folderPath + fileName + ch2 );
	vFileNames.push_back( folderPath + fileName + ch3 );
	vFileNames.push_back( folderPath + fileName + ch4 );
	vFileNames.push_back( folderPath + fileName + ch5 );
	vFileNames.push_back( folderPath + fileName + ch6 );
	
	Locker locker( this );

    // Avoids to start recording twice
	if( m_audioStream.get() )
		throw  std::runtime_error( "record is running" );

	// Opens files for writing the audio data
	for( std::vector<std::string>::iterator i = vFileNames.begin(); i!= vFileNames.end(); i++ )
	{
		//m_files.push_back( new SndfileHandle( i->c_str() , SFM_WRITE, SF_FORMAT_WAV | SF_FORMAT_FLOAT, 1, 44100) );
		//m_files.push_back( new SndfileHandle( i->c_str() , SFM_WRITE, SF_FORMAT_WAV | SF_FORMAT_PCM_24, 1, 44100) );
		m_files.push_back( new SndfileHandle( i->c_str() , SFM_WRITE, SF_FORMAT_WAV | SF_FORMAT_PCM_32, 1, 44100) );
	}

	//set the channels selector, 6 channels
	int channelSelectors6[6] = {0,1,2,3,4,5};

	// Creates a stream
	//m_iAsioDeviceId is the ASIO device, usually it is #14;
	if( numOfChannel == 6)
	{
		m_audioStream.reset( new AudioStream( m_iAsioDeviceId,channelSelectors6, m_files ) );
	}

	SetNumOfChannel(numOfChannel); 
	m_bRecording = true;
}

void AudioRecord::StopRecord()
{
	// Locks this class
	Locker locker( this );

	if( m_audioStream.get() == NULL )
		return;

	// Closes the stream
	m_audioStream.reset();
	// Closes files of audio data
	for( AudioStream::Files::iterator i = m_files.begin(); i!= m_files.end(); i++ )
		delete *i;
	m_files.clear();
	m_bRecording = false;
}

int AudioRecord::SetNumOfChannel(const int numOfChannel)
{
	m_numOfChannel = numOfChannel;
	m_audioStream->SetNumOfChannel(numOfChannel);
	return 0;
}

//float* AudioRecord::GetArrVolume()
//int24* AudioRecord::GetArrVolume()
//{
//	return m_audioStream->m_arrVolume;
//}