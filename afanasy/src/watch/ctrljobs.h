#pragma once

#include "actionid.h"
#include "listjobs.h"

#include <QLabel>

class ListJobs;

class CtrlJobs : public QLabel
{
Q_OBJECT
public:
	CtrlJobs(QWidget * i_parent, ListJobs * i_listjobs, bool i_inworklist);
	~CtrlJobs();

protected:
	void contextMenuEvent( QContextMenuEvent * i_event);

private:
	ListJobs * m_listjobs;
	const bool m_inworklist;
};
