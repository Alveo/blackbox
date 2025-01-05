/*****************************************************************************
*Organisation: MARCS of UWS
*Project: The Big ASC
*
*File name: AudioRecord
*Abstract:  Record audio and write to files
*          
*Programmer: Lei Jing
*Version: 1.0.1
*Last update time: 18.4.2011
******************************************************************************/

#ifndef _AUDIO_RECORD_H_
#define _AUDIO_RECORD_H_


#define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers

#include <list>
#include <vector>
#include <string>
#include <memory>
#include <iostream>
#include "windows.h"

#include <portaudio/portaudio.h>
#include <portaudio/pa_asio.h>
#include <sndfile/sndfile.hh>

#include "ThreadLockBase.h"
#include <boost/shared_ptr.hpp>

typedef int AUDIO_FORMAT;

//! This class encapsulates a worker thread and an audio stream with multiple channels
// But this class should be further abstracted into a base thread class and a derived worker thread to handle the stream. Next version
class AudioStream: public Lockable
{
private:
	//! The struct to hold the int24 pcm data.
	struct int24
	{
		unsigned char c[3];
	};

public:
	//! Define a vector type to hold files to be writen to
	typedef std::vector< SndfileHandle * > Files;   

	//! The constructor accecpts a device handle and a set of files, then opens a stream on that device
	/*!
	\param device The sequence number of the audio device.
	\param channelselectors The array of the selected channels. [0,...,5], 6 channels are used.
	\param files The holder of the audio file handles .
	*/
	AudioStream( const int device, int channelselectors[], const Files & files );

	//! The destructor will wait for the worker thread to quit and clean up opened resources
	virtual ~AudioStream();

	//! Thread entry
	static DWORD WINAPI ThreadProc( LPVOID lpParameter );

	//!set the number of channel
	int SetNumOfChannel(const int numOfChannel);  
	
	//!Maximum 6 channels. 
	static const int MAX_NUM_CHANNEL = 6; 

	//!The volume array of all channels
	//float *m_arrVolume;
	//int24* m_arrVolume;

private:
	//! Audio callback entry. Refer to the PortAudio document for more details.
	static int PaRecordCallback(const void *inputBuffer,                          
								void *outputBuffer,
								unsigned long framesPerBuffer,
								const PaStreamCallbackTimeInfo* timeInfo,
								PaStreamCallbackFlags statusFlags,
								void *userData )
	{
		return ((AudioStream*)userData)->RecordCallback(inputBuffer,outputBuffer,framesPerBuffer,timeInfo,statusFlags);
	}

	//! Thread's main function that handles the data in m_queue and writes into files
	void main();

	//! Audio callback handler that puts received audio data into the queue m_queue.
	int RecordCallback(const void *inputBuffer, 
					   void *outputBuffer,
					   unsigned long framesPerBuffer,
                       const PaStreamCallbackTimeInfo* timeInfo,
                       PaStreamCallbackFlags statusFlags );

	static const unsigned long FRAMES_PER_BUFFER = 1024;

	//! Thread handle returned by Windows
	HANDLE m_thread;

	//! Event handle returned by Windows
	HANDLE m_event;

	//! Opened files to write data into
	std::vector< SndfileHandle * > m_files;

	//! The current file used to handle multi-channel audio
	int m_currentFile;

	//! PaAudio stream
	PaStream * m_paStream;

	//! The queue shared between audio callback and file writing thread
	//std::list< std::vector<float> > m_queue;
	//std::list< std::vector<int24> > m_queue;
	std::list< std::vector<AUDIO_FORMAT> > m_queue;

	//! The number of channels are used in the recording.
	int m_numOfChannel;
};

//! The audio record class
class AudioRecord: public Lockable
{
public:
	//! The constructor
	AudioRecord();

	//! The deconstructor
	virtual ~AudioRecord();

	//! Start a recording.
	/*!
	\param folderPath The audio files would be put in this directory.
	\param fileName The base file name for the audio recording.
	*/
	void StartRecord(  const std::string &folderPath, const std::string &fileName );
	
	//! Stop recording
	void StopRecord();

	//! set the number of channels
	int SetNumOfChannel(const int numOfChannel);

	//! Accessor of the volume
	//float* GetArrVolume();
	//int24* GetArrVolume();

	//! Recording status
	bool m_bRecording;

private:
	//! Maximum number of channels
	static const int MAX_NUM_CHANNEL = AudioStream::MAX_NUM_CHANNEL;

	//! Combine Lockable class to clock 
	static Lockable m_lock;

	//! Lock class through this static counter
	static int m_initCounter;

	//! number of channels used
	int m_numOfChannel;

	//! the # ID of the ASIO device
	int m_iAsioDeviceId;

	//! audio file handles holder
	AudioStream::Files		m_files;

	//! AudioStream class for recording
	//std::auto_ptr< AudioStream > m_audioStream;
	boost::shared_ptr< AudioStream > m_audioStream;

	//! Get the ASIO device ID
	int GetAsioDeviceId();
};

#endif //_AUDIO_RECORD_H_ 
