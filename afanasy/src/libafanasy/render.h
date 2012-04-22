#pragma once

#include "name_af.h"
#include "host.h"
#include "client.h"

namespace af
{
/// Afanasy render slave.
class Render : public Client
{
public:

/// Construct render, getting values from environment.
   Render( uint32_t State, uint8_t Priority);

/// Construct offline render with provided values from database.
   Render( int Id);

/// Read Render data from message.
   Render( Msg * msg);

   virtual ~Render();

   void generateInfoStream( std::ostringstream & stream, bool full = false) const; /// Generate information.

	inline bool isOnline()  const { return (m_state & SOnline ); }///< Whether Render is online.
	inline bool isBusy()    const { return (m_state & SBusy   ); }///< Whether Render is busy.
	inline bool isNIMBY()   const { return (m_state & SNIMBY  ); }///< Whether Render is NIMBY.
	inline bool isNimby()   const { return (m_state & Snimby  ); }///< Whether Render is nimby.
	inline bool isFree()    const { return (((~m_state) & SNIMBY) && ((~m_state) & Snimby));}///< Whether Render is free.
	inline bool isOffline() const { return !(m_state & SOnline );}///< Whether Render is offline.
	inline bool isDirty()   const { return !(m_state & SDirty);}  ///< Whether Render is dirty.

	inline bool isWOLFalling()   const { return m_state & SWOLFalling;  }
	inline bool isWOLSleeping()  const { return m_state & SWOLSleeping; }
	inline bool isWOLWaking()    const { return m_state & SWOLWaking;   }
	inline long long getWOLTime()const { return m_wol_operation_time;   }
	inline void setWOLFalling(   bool value) { if( value ) m_state = m_state | SWOLFalling;  else m_state = m_state & (~SWOLFalling); }
	inline void setWOLSleeping(  bool value) { if( value ) m_state = m_state | SWOLSleeping; else m_state = m_state & (~SWOLSleeping);}
	inline void setWOLWaking(    bool value) { if( value ) m_state = m_state | SWOLWaking;   else m_state = m_state & (~SWOLWaking);  }

	inline int getMaxTasks()     const { return (m_max_tasks == -1 ? m_host.m_max_tasks : m_max_tasks);}
	inline int getCapacity()     const { return (m_capacity == -1 ? m_host.m_capacity : m_capacity);}
	inline int getCapacityUsed() const { return m_capacity_used;}
	inline int getCapacityFree() const { return (m_capacity == -1 ? m_host.m_capacity : m_capacity) - m_capacity_used;}
	inline bool hasCapacity( int value) const { return m_capacity_used + value <= (m_capacity == -1 ? m_host.m_capacity : m_capacity );}

/// Whether Render is ready to render tasks.
   inline bool isReady() const { return (
			( m_state & SOnline ) &&
			( false == ( m_state & SNIMBY )) &&
			( m_priority > 0 ) &&
			( m_capacity_used < getCapacity() ) &&
			( (int)m_tasks.size() < getMaxTasks() ) &&
            ( false == isWOLFalling())
         );}

   inline const Host    & getHost()    const { return m_host;}
   inline const HostRes & getHostRes() const { return m_hres;}

   inline void setFree()   { m_state = m_state & (~Snimby); m_state = m_state & (~SNIMBY);}///< Set free (unset nimby and NIMBY).
   inline void setNIMBY()  { m_state = m_state |   SNIMBY;  m_state = m_state & (~Snimby);}///< Set NIMBY.
   inline void setNimby()  { m_state = m_state |   Snimby;  m_state = m_state & (~SNIMBY);}///< Set nimby.

   inline void setOnline()  { m_state = m_state |   SOnline ; m_wol_operation_time = time(NULL);}
   inline void setOffline() { m_state = m_state & (~SOnline); m_wol_operation_time = time(NULL);}

   inline void setPriority( int value) { m_priority = value; }///< Set priority.

   void setCapacity( int value) { m_capacity = value; checkDirty();}
   void setMaxTasks( int value) { m_max_tasks = value; checkDirty();}

   virtual int calcWeight() const; ///< Calculate and return memory size.

   inline long long getTasksStartFinishTime() const { return m_task_start_finish_time; }///< Get tasks start or finish time.
   inline const std::list<TaskExec*> & getTasks() { return m_tasks;}
   inline int getTasksNumber() const { return int(m_tasks.size());}

//   const std::string getResourcesString() const;

   inline const std::string & getAnnontation() const { return m_annotation;}

   virtual void v_jsonWrite( std::ostringstream & o_str, int type);

   void jsonRead( const JSON & i_object, std::string * io_changes);

public:

	enum State
	{
		SOnline      = 1<<0,
		Snimby       = 1<<1,
		SNIMBY       = 1<<2,
		SBusy        = 1<<3,
		SDirty       = 1<<4,
		SWOLFalling  = 1<<5,
		SWOLSleeping = 1<<6,
		SWOLWaking   = 1<<7
	};

protected:
   inline void setBusy(  bool Busy ) { if(Busy ) m_state = m_state | SBusy;  else m_state = m_state & (~SBusy );}
   void restoreDefaults();       ///< Restore host capacity and reset disabled services.
   void checkDirty();

protected:

	int32_t m_capacity;
	int32_t m_capacity_used;
	int32_t m_max_tasks;

	std::string m_services_disabled;
	std::string m_custom_data;
	std::string m_annotation;

	Host     m_host;
	HostRes  m_hres;

	std::list<TaskExec*> m_tasks;

	int64_t m_task_start_finish_time; ///< Task start or finish time.

	int64_t m_wol_operation_time;   ///< Last WOL operation time (to sleep or to wake).

private:
   void construct();

protected:
   void readwrite( Msg * msg); ///< Read or write Render in message.
};
}