# -*- coding: utf-8 -*-

import json
import cgruconfig
import afnetwork


class Block:
    '''
    Block class for block manipulation
    '''
    p_percentage = None
    capacity = None
    name = None
    service = None
    frames_per_task = None
    time_done = None
    job_id = None
    tasks_num = None
    block_num = None
    p_progressbar = None
    p_tasks_run_time = None
    state = None
    flags = None
    p_tasks_skipped = None
    frame_first = None
    frame_last = None
    st = None
    frames_inc = None
    p_tasks_done = None
    time_started = None
    data = None
    tasks = []
    full = False

    class State:
        restart = 'restart'
        skip = 'skip'

    def __init__(self, data, full=False):
        '''
        Constructor
        '''
        self.p_percentage = data.get('p_percentage', 0)
        self.capacity = data.get('capacity', 0)
        self.name = data.get('name')
        self.service = data.get('service')
        self.frames_per_task = data.get('frames_per_task')
        self.time_done = data.get('time_done')
        self.job_id = data.get('job_id')
        self.tasks_num = data.get('tasks_num')
        self.block_num = data.get('block_num')
        self.p_progressbar = data.get('p_progressbar')
        self.p_tasks_run_time = data.get('p_tasks_run_time')
        self.state = data.get('state', '')
        self.flags = data.get('flags')
        self.p_tasks_skipped = data.get('p_tasks_skipped')
        self.frame_first = data.get('frame_first')
        self.frame_last = data.get('frame_last')
        self.st = data.get('st')
        self.frames_inc = data.get('frames_inc')
        self.p_tasks_done = data.get('p_tasks_done')
        self.time_started = data.get('time_started')
        self.data = data
        self.full = full
        if self.full is True and self.isNumeric() is False:
            self.tasks = data.get('tasks', [])

    def fillTasks(self):
        if self.full is not True:
            job = getJob(self.job_id, full=True)
            block = job.blocks[self.block_num]
            self.data = block.data
            self.tasks = block.tasks

    def setState(self, state, taskIds=[], verbose=False):
        action = 'action'
        data = {'ids': [self.job_id],
                'type': 'jobs',
                'block_ids': [self.block_num],
                'operation': {'type': state,
                              'task_ids': taskIds}}
        output = _sendRequest(action, data, verbose)
        return output

    def restart(self, taskIds=[]):
        self.setState(self.State.restart, taskIds=taskIds)

    def skip(self, taskIds=[]):
        self.setState(self.State.skip, taskIds=taskIds)

    def isNumeric(self):
        return bool(self.flags >> 0)

    def appendTasks(self, tasks, verbose=False):
        """Append new tasks to an existing block

        :param tasks: list of new Task() objects
        :param bool verbose: verbosity toggle
        :return: server response
        """
        output = "The block is numeric and cannot have tasks appended"
        if self.isNumeric() is False:
            tasks_data = []
            for t in tasks:
                tasks_data.append(t.data)
            action = 'action'
            data = {'ids': [self.job_id],
                    'type': 'jobs',
                    'block_ids': [self.block_num],
                    'operation': {
                        'type': 'append_tasks',
                        'tasks': tasks_data}}
            output = _sendRequest(action, data, verbose)
        return output


class Job:
    '''
    Job class for job manipulation
    '''
    id = None
    project = None
    blocks = []
    name = None
    st = None
    state = None
    priority = None
    host_name = None
    branch = None
    time_creation = None
    time_done = None
    time_started = None
    serial = None
    user_name = None
    max_running_tasks = None
    max_running_tasks_per_host = None
    depend_mask = ''
    p_percentage = 0
    data = None
    full = False

    class State:
        restart = 'restart'
        start = 'start'
        pause = 'pause'
        stop = 'stop'
        skip = 'skip'
        delete = 'delete'

    def __init__(self, jobId, data=None, full=False):
        '''
        Constructor
        '''
        self.id = jobId
        self.blocks = []
        self.full = full
        if data is not None:
            self.data = data
            self.fillInfo(data)

    def fillInfo(self, data):
        self.project = data.get('project')
        self.name = data.get('name')
        self.st = data.get('st')
        self.state = data.get('state')
        self.priority = data.get('priority')
        self.host_name = data.get('host_name')
        self.branch = data.get('branch')
        self.time_creation = data.get('time_creation')
        self.time_done = data.get('time_done')
        self.time_started = data.get('time_started')
        self.serial = data.get('serial')
        self.user_name = data.get('user_name')
        self.max_running_tasks = data.get('max_running_tasks', -1)
        self.max_running_tasks_per_host = data.get('max_running_tasks_per_host', -1)
        self.depend_mask = data.get('depend_mask', '')
        self.fillBlocks(data['blocks'], self.full)

    def fillBlocks(self, blocksData, full):
        blocksProgress = 0
        for blockData in blocksData:
            block = Block(blockData, full)
            if block.p_percentage is not None:
                blocksProgress += block.p_percentage
            self.blocks.append(block)
        self.p_percentage = blocksProgress / len(blocksData)

    def setState(self, jobState, verbose=False):
        action = 'action'
        data = {'ids': [self.id],
                'type': 'jobs',
                'operation': {'type': jobState}}
        output = _sendRequest(action, data, verbose)
        return output

    def pause(self):
        self.setState(self.State.pause)

    def start(self):
        self.setState(self.State.start)

    def stop(self):
        self.setState(self.State.stop)

    def delete(self):
        self.setState(self.State.delete)

    def getProgress(self, verbose=False,):
        action = 'get'
        data = {'type': 'jobs',
                'ids': [self.id],
                'mode': 'progress'}
        output = _sendRequest(action, data, verbose)
        if output is not None:
            if 'job_progress' in output:
                return output['job_progress']
        return None

    def appendBlocks(self, blocks, verbose=False):
        """Append new blocks to an existing job

        :param bool verbose: verbosity toggle
        :return: server response
        """
        action = 'action'
        blocks_data = []
        for block in blocks:
            block.fillTasks()
            blocks_data.append(block.data)
        data = {'type': 'jobs',
                'ids': [self.id],
                "operation": {
                    'type': 'append_blocks',
                    'blocks': blocks_data}}
        output = _sendRequest(action, data, verbose)
        return output


class Render:
    '''
    Render class for render manipulation
    '''
    id = None
    name = None
    user_name = None
    capacity_used = None
    idle_time = None
    time_launch = None
    state = None
    st = None
    priority = None
    time_update = None
    time_register = None
    netifs = []
    task_start_finish_time = None
    address = {}
    host = None
    busy_time = None

    max_tasks = None
    wol_idlesleep_time = None
    capacity = None
    power = None

    def __init__(self, renderId, data=None):
        '''
        Constructor
        '''
        self.id = renderId
        if data is not None:
            self.fillRenderInfo(data)

    def fillRenderInfo(self, data):
        self.name = data.get('name')
        self.user_name = data.get('user_name')
        self.capacity_used = data.get('capacity_used')
        self.idle_time = data.get('idle_time')
        self.time_launch = data.get('time_launch')
        self.state = data.get('state')
        self.st = data.get('st')
        self.priority = data.get('priority')
        self.time_update = data.get('time_update')
        self.time_register = data.get('time_register')
        # self.netifs = []
        self.task_start_finish_time = data.get('task_start_finish_time')
        # self.address = {}
        self.host = data.get('host')
        self.busy_time = data.get('busy_time')

    def setUserName(self, username, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['params'] = {'user_name': username}
        output = _sendRequest(action, data, verbose)
        return output

    def setNimby(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['params'] = {'nimby': True}
        output = _sendRequest(action, data, verbose)
        return output

    def setNIMBY(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['params'] = {'NIMBY': True}
        output = _sendRequest(action, data, verbose)
        return output

    def setFree(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['params'] = {'nimby': False}
        output = _sendRequest(action, data, verbose)
        return output

    def setFreeUnpause(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['params'] = {'nimby': False, 'paused': False}
        output = _sendRequest(action, data, verbose)
        return output

    def ejectNotMyTasks(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['operation'] = {'type': 'eject_tasks_keep_my'}
        output = _sendRequest(action, data, verbose)
        return output

    def exit(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['mask'] = self.name
        data['operation'] = {'type': 'exit'}
        output = _sendRequest(action, data, verbose)
        return output

    def addService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_add', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def removeService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_remove', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def disableService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_disable', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def enableService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_enable', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def clearServices(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'clear_services'}
        output = _sendRequest(action, data, verbose)
        return output

    def setPool(self, poolName, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'set_pool', 'name': poolName}
        output = _sendRequest(action, data, verbose)
        return output

    def reassignPool(self, verbose=False):
        action = 'action'
        data = {'type': 'renders'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'reassign_pool'}
        output = _sendRequest(action, data, verbose)
        return output


class Pool():
    '''
    Pool class for pool manipulation
    '''
    id = None
    name = None
    parent = None
    services = None
    priority = None
    time_creation = None
    pools_total = None
    max_capacity_per_host = None
    task_start_finish_time = None
    run_tasks = None
    max_tasks_per_host = None
    renders_total = None
    run_capacity = None
    renders_num = None

    def __init__(self, poolId, data=None):
        '''
        Constructor
        '''
        self.id = poolId

        if data is not None:
            self.fillPoolInfo(data)

    def fillPoolInfo(self, data):
        self.name = data.get('name')
        self.parent = data.get('parent')
        self.services = data.get('services')
        self.priority = data.get('priority')
        self.time_creation = data.get('time_creation')
        self.pools_total = data.get('pools_total')
        self.max_capacity_per_host = data.get('max_capacity_per_host')
        self.task_start_finish_time = data.get('task_start_finish_time')
        self.run_tasks = data.get('run_tasks')
        self.max_tasks_per_host = data.get('max_tasks_per_host')
        self.renders_total = data.get('renders_total')
        self.run_capacity = data.get('run_capacity')

    def addService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'pools'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_add', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def removeService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'pools'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_remove', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def disableService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'pools'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_disable', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def enableService(self, serviceName, verbose=False):
        action = 'action'
        data = {'type': 'pools'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'service_enable', 'name': serviceName, 'mask': serviceName}
        output = _sendRequest(action, data, verbose)
        return output

    def clearServices(self, verbose=False):
        action = 'action'
        data = {'type': 'pools'}
        data['ids'] = [self.id]
        data['operation'] = {'type': 'farm', 'mode': 'clear_services'}
        output = _sendRequest(action, data, verbose)
        return output

    def setMaxCapacity(self, capacity, verbose=False):
        action = 'action'
        data = {'type': 'pools'}
        data['ids'] = [self.id]
        data['params'] = {'max_capacity_per_host': capacity}
        output = _sendRequest(action, data, verbose)
        return output


class Monitor():
    '''
    Monitor class for monitor registration
    '''
    class WatchType:
        jobs = 'jobs'
        renders = 'renders'

    def __init__(self, verbose=False):
        action = 'monitor'
        data = {'engine': 'python'}
        output = _sendRequest(action, data, verbose)
        if output is not None:
            self.id = output['monitor']['id']
        else:
            return None

    def __del__(self, verbose=False):
        action = 'action'
        data = {'type': 'monitors',
                'ids': [self.id],
                'operation': {"type": "deregister"}}
        _sendRequest(action, data, verbose, without_answer=True)

    def changeUid(self, uid, verbose=False):
        action = 'action'
        data = {'type': 'monitors',
                'ids': [self.id],
                'operation': {"type": "watch",
                              "class": "perm",
                              "uid": uid}}
        return _sendRequest(action, data, verbose)

    def subscribe(self, classType, verbose=False):
        action = 'action'
        data = {'type': 'monitors',
                'ids': [self.id],
                'operation': {"type": "watch",
                              "class": classType,
                              "status": "subscribe"}}
        return _sendRequest(action, data, verbose)

    def events(self):
        action = 'get'
        data = {'type': 'monitors',
                'ids': [self.id],
                'mode': 'events'}
        return _sendRequest(action, data)


def _sendRequest(action, requestData, verbose=False, without_answer=False):
    """Missing DocString

    :param bool verbose:
    :return:
    """
    data = {'user_name': cgruconfig.VARS['USERNAME'],
            "host_name": cgruconfig.VARS['HOSTNAME']}
    data.update(requestData)
    obj = {action: data}
    # print(json.dumps(obj))
    output = afnetwork.sendServer(json.dumps(obj), verbose, i_without_answer=without_answer)
    if output[0] is True:
        return output[1]
    else:
        return None


def getJobList(ids=None, full=False, verbose=False):
    """Missing DocString

    :param bool verbose:
    :return:
    """
    action = 'get'
    data = {'type': 'jobs'}
    if ids is not None:
        data['ids'] = ids
    if full is True:
        data['mode'] = 'full'
    output = _sendRequest(action, data, verbose)
    jobs = []
    if output is not None:
        if 'jobs' in output:
            for jobData in output['jobs']:
                job = Job(jobData['id'], jobData, full=full)
                jobs.append(job)
    return jobs


def getJob(jobId, full=False, verbose=False):
    jobs = getJobList(ids=[jobId], full=full, verbose=verbose)
    if len(jobs) > 0:
        return jobs[0]
    else:
        return None


def getRenderList(mask=None, ids=None, verbose=False):
    action = 'get'
    data = {'type': 'renders'}
    if mask is not None:
        data['mask'] = mask
    if ids is not None:
        data['ids'] = ids
    output = _sendRequest(action, data, verbose)
    renders = []
    if output is not None:
        if 'renders' in output:
            for renderData in output['renders']:
                render = Render(renderData['id'], renderData)
                renders.append(render)
    return renders


def getRenderResources():
    action = 'get'
    data = {'type': 'renders',
            'mode': 'resources'}
    output = _sendRequest(action, data)
    if output is not None:
        if 'renders' in output:
            return output['renders']
    return None


def getPoolList(ids=None, verbose=False):
    action = 'get'
    data = {'type': 'pools'}
    if ids is not None:
        data['ids'] = ids
    output = _sendRequest(action, data, verbose)
    pools = []
    if output is not None:
        if 'pools' in output:
            for poolData in output['pools']:
                pool = Pool(poolData['id'], poolData)
                pools.append(pool)
    return pools
