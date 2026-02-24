from beanstalkc import Connection, Job


class Pusher():
    def __init__(self, tubename, host='127.0.0.1', port=11300) -> None:
        self.beans = Connection(host=host, port=port)
        self.beans.use(tubename)
        self.tubename = tubename

    def setJob(self, message, priority=2**31, delay=0, ttr=3600):
        self.beans.put(message, priority, delay, ttr)

    def close(self):
        self.beans.close()


class Worker():
    def __init__(self, tubename, host='127.0.0.1', port=11300) -> None:
        self.beans = Connection(host=host, port=port)
        self.beans.watch(tubename)
        self.tubename = tubename

    def getJob(self, timeout=10) -> Job:
        return self.beans.reserve(timeout)

    def deleteJob(self, job: Job):
        job.delete()

    def releaseJob(self, job: Job, priority=None, delay=0):
        if priority:
            job.release(priority=priority, delay=delay)
        elif delay:
            job.release(delay=delay)
        else:
            job.release()

    def buryJob(self, job: Job):
        job.bury()

    def close(self):
        self.beans.close()
