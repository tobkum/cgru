#include "monitor.h"

#include "address.h"
#include "environment.h"
#include "msg.h"

#define AFOUTPUT
#undef AFOUTPUT
#include "../include/macrooutput.h"

using namespace af;

const int Monitor::EventsShift = af::Msg::TMonitorEvents_BEGIN + 1;
const int Monitor::EventsCount = af::Msg::TMonitorEvents_END - Monitor::EventsShift;

Monitor::Monitor():
   Client( Client::GetEnvironment, 0)
{
   construct();
   m_name = af::Environment::getUserName() + "@" + af::Environment::getHostName() + ":" + m_address.generatePortString().c_str();
}

Monitor::Monitor( Msg * msg):
   Client( Client::DoNotGetAnyValues, 0)
{
   if( construct() == false) return;
   read( msg);
}

bool Monitor::construct()
{
   events = new bool[EventsCount];
   if( events == NULL)
   {
      AFERROR("Monitor::construct(): Can't allocate memory for events table.")
      return false;
   }
   for( int e = 0; e < EventsCount; e++) events[e] = false;
   return true;
}

Monitor::~Monitor()
{
   if( events ) delete [] events;
}

void Monitor::readwrite( Msg * msg)
{
   rw_int32_t( m_id,            msg);
   rw_int64_t( m_time_launch,   msg);
   rw_int64_t( m_time_register, msg);
   rw_int64_t( time_activity, msg);
   rw_String ( m_name,          msg);
   rw_String ( m_user_name,      msg);
   rw_String ( m_version,       msg);

   for( int e = 0; e < EventsCount; e++) rw_bool( events[e], msg);

   rw_Int32_List( jobsUsersIds, msg);
   rw_Int32_List( jobsIds,      msg);

   m_address.readwrite( msg);
}

bool Monitor::hasEvent( int type) const
{
   int eventNum = type - EventsShift;
   if((eventNum >= 0) && (eventNum < EventsCount))
   {
      return events[eventNum];
   }
   else
   {
      AFERRAR("MonitorAf::hasEvent: Invalid event: [%s]", af::Msg::TNAMES[type])
      return false;
   }
}

void Monitor::generateInfoStream( std::ostringstream & stream, bool full) const
{
   if( full )
   {
      stream << "Monitor name = \"" << m_name << "\" (id=" << getId() << ")";
      stream << "\n Version: " << m_version;
      stream << "\n Launch Time: " + af::time2str( m_time_launch);
      stream << "\n Register Time: " + af::time2str( m_time_register);
      stream << "\n Time Activity: " + af::time2str( time_activity);

      stream << "\n UIds[" << jobsUsersIds.size() << "]:";
      for( std::list<int32_t>::const_iterator it = jobsUsersIds.begin(); it != jobsUsersIds.end(); it++)
         stream << " " << *it;
      stream << "\n JIds[" << jobsIds.size() << "]:";
      for( std::list<int32_t>::const_iterator it = jobsIds.begin(); it != jobsIds.end(); it++)
         stream << " " << *it;

      stream << "\n System Events:";
      for( int e = 0; e < af::Monitor::EventsCount; e++)
      {
         int etype = e + af::Monitor::EventsShift;
         stream << "\n    " << af::Msg::TNAMES[etype] << " : ";
         if( hasEvent(etype)) stream << " SUBMITTED";
         else stream << "   ---";
      }
   }
   else
   {
      stream << m_name << "[" << m_id << "]";
      stream << " v'" << m_version << "' ";
      m_address.generateInfoStream( stream, full);
   }
}