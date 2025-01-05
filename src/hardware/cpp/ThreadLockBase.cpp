
#include "ThreadLockBase.h"
#include <process.h>


void ThreadBase::StartThread(void) 
{ 
	//m_hThread = reinterpret_cast<HANDLE>(_beginthreadex(NULL, NULL, (PTHREADFUN) ThreadFun, this, 0, (unsigned*) &m_dwThreadID)); 
	m_hThread = CreateThread(NULL, 0, ThreadFunc, this, 0, 0);
	if (m_hThread == NULL) 
	{ 
		throw("Start thread error!"); 
	} 
	CloseHandle(m_hThread);
	//m_bRunning = true; //if set this, can restart a new thread after stop
} 

void ThreadBase::StopThread()
{
	m_bRunning = false;
}

DWORD WINAPI ThreadBase::ThreadFunc(LPVOID lpParameter) 
{ 
	ThreadBase *pThreadBase = reinterpret_cast<ThreadBase*> (lpParameter); 
	pThreadBase->ThreadWorker(lpParameter); 
	return 0; 
} 

void ThreadBase::WaitForEnd(DWORD dwTimeOut /* = INFINITE */) 
{ 
	DWORD dwRet = WaitForSingleObject(m_hThread, dwTimeOut); 
	if (dwRet == WAIT_OBJECT_0) 
	{ 
		CloseHandle(m_hThread); 
		m_hThread = NULL; 
	} 
	else if (dwRet == WAIT_TIMEOUT) 
	{ 
		throw("Error: Time out!"); 
	} 
	return;
}

Lockable::Lockable()
{
	// Creates a critical section and specify a spin counter for multi-processor machine
	if ( !::InitializeCriticalSectionAndSpinCount( &m_csec, 0x80000400) )
		throw std::runtime_error( "failed to create a critical section" );
}

Lockable::~Lockable()
{
	::DeleteCriticalSection( &m_csec );
}

void Lockable::lock()
{
	::EnterCriticalSection( &m_csec ); 
}

void Lockable::unlock()
{
	::LeaveCriticalSection( &m_csec );
}
/////////////////////////////////////////////////////////////////////////////////////
Locker::Locker( Lockable * lockable )
:m_lockable( lockable )
{
    // Locks the lockable object if the pointer is valid
	if( !m_lockable )
		throw std::runtime_error( "invalid pointer" );
	m_lockable->lock();
}

Locker::~Locker()
{
	m_lockable->unlock();
}
