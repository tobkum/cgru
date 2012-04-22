#pragma once

#include "../libafanasy/blockdata.h"
#include "../libafanasy/name_af.h"

#include "useraf.h"

class MonitorContainer;
class RenderAf;
class RenderContainer;
class Task;

class Block
{
public:
   Block( JobAf * blockJob, af::BlockData * blockData, af::JobProgress * progress);
   virtual ~Block();

   inline bool isInitialized() const { return m_initialized;}

   inline void setUser( UserAf * jobOwner) { m_user = jobOwner;}

   inline int getErrorsAvoidHost() const
	  { return ( m_data->getErrorsAvoidHost() > -1) ? m_data->getErrorsAvoidHost() : m_user->getErrorsAvoidHost();}
   inline int getErrorsRetries() const
	  { return ( m_data->getErrorsRetries() > -1) ? m_data->getErrorsRetries() : m_user->getErrorsRetries();}
   inline int getErrorsTaskSameHost() const
	  { return ( m_data->getErrorsTaskSameHost() > -1) ? m_data->getErrorsTaskSameHost() : m_user->getErrorsTaskSameHost();}
   inline int getErrorsForgiveTime() const
	  { return ( m_data->getErrorsForgiveTime() > -1) ? m_data->getErrorsForgiveTime() : m_user->getErrorsForgiveTime();}

   int calcWeight() const;
   int logsWeight() const;
   int blackListWeight() const;

   virtual void errorHostsAppend( int task, int hostId, RenderContainer * renders);
   bool avoidHostsCheck( const std::string & hostname) const;
   virtual void getErrorHostsListString( std::string & str) const;
   virtual void errorHostsReset();

   bool canRun( RenderAf * render);

   virtual void startTask( af::TaskExec * taskexec, RenderAf * render, MonitorContainer * monitoring);

   void taskFinished( af::TaskExec * taskexec, RenderAf * render, MonitorContainer * monitoring);

   /// Refresh block. Retrun true if block progress changed, needed for jobs monitoring (watch jobs list).
   virtual bool refresh( time_t currentTime, RenderContainer * renders, MonitorContainer * monitoring);

   uint32_t action( const af::MCGeneral & mcgeneral, int type, AfContainer * pointer, MonitorContainer * monitoring);

	/// Return \c true if some job block progess parameter needs to updated for monitoring
	bool action( const JSON & i_action, const std::string & i_author, std::string & io_changes,
					AfContainer * i_container, MonitorContainer * i_monitoring);

   bool tasksDependsOn( int block);

public:
   JobAf * m_job;
   af::BlockData * m_data;
   Task ** m_tasks;                 ///< Tasks.
   UserAf * m_user;

protected:
   void appendJobLog( const std::string & message);
   bool errorHostsAppend( const std::string & hostname);

private:
   af::JobProgress * m_jobprogress;

   std::list<std::string>  m_errorHosts;       ///< Avoid error hosts list.
   std::list<int>          m_errorHostsCounts; ///< Number of errors on error host.
   std::list<time_t>       m_errorHostsTime;   ///< Time of the last error

   std::list<RenderAf*> m_renders_ptrs;
   std::list<int> m_renders_counts;

   std::list<int> m_dependBlocks;
   std::list<int> m_dependTasksBlocks;
   bool m_initialized;             ///< Where the block was successfully  initialized.

private:
   void constructDependBlocks();

   void addRenderCounts( RenderAf * render);
   int  getRenderCounts( RenderAf * render) const;
   void remRenderCounts( RenderAf * render);
};