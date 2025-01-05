/*****************************************************************************
*Organisation: MARCS of UWS
*Project: The Big ASC
*
*File name: ThreadLockBase
*Abstract:  It has a pure thread base class, a lock-able class and a tool locker class
*			Other worker class should derive from the base classes
*          
*
*Programmer: Lei Jing
*Version: 1.0.1
*Last update time: 18.4.2011
******************************************************************************/

#ifndef _Thread_Lock_Base_H_
#define _Thread_Lock_Base_H_

#define WIN32_LEAN_AND_MEAN             // Exclude rarely-used stuff from Windows headers

#include <list>
#include <vector>
#include <string>
#include <memory>
#include <iostream>
#include "windows.h"



//! A base class to make derived class multi-thread 
class ThreadBase 
{ 
public: 
	//! Constructor, set m_bRunning thread status true to be ready to start.
	ThreadBase(void)
	{
		m_bRunning = true;
	}; 

	//! Destructor.
	~ThreadBase(void) {};

	//! Start a thread.
	void StartThread(void); 

	//! Stop the started thread.
	void StopThread(void);

	//! Wait for the thread finish.
	void WaitForEnd(DWORD dwTimeOut = INFINITE); 

	//! Thread worker function. Pure virtual function, has to be overrided in the derived class.
	virtual DWORD WINAPI ThreadWorker(LPVOID lpParameter) = 0; 

protected:
	//! Thread running status.
	bool m_bRunning; 

private: 
	//! Thread function, entry.
	static DWORD WINAPI ThreadFunc(LPVOID lpParameter); 

	//! Thread handle.
	HANDLE m_hThread; 
	//DWORD m_dwThreadID; 
}; 

//!A base class to make derived class lock-able in multi-thread environment
class Lockable
{
public:
	//! constructor.
	Lockable() throw( std::runtime_error );

	//! Destructor.
	~Lockable();

	//! Enter the critical section to lock
	void lock();    

	//! Leave the critical section to unlock
	void unlock();  

private:
	//! The critical_section member
	CRITICAL_SECTION m_csec;
};

//! A tool class to lock and unlock a lockable object automatically in a function scope
class Locker
{
public:
//! Pass a lockable object to this class, the object is going to be locked in this constructor
	Locker( Lockable * lockable );

//! The passed lockable object is going to be unlocked in this destructor
	~Locker();
private:
	Lockable * m_lockable;
};

#endif //_Thread_Lock_Base_H_