from .task import Task

class Updater:

    def __init__(self):
        self._check_for_updates_task = Task()
        self._update_summary_task = Task()
        self._list_files_task = Task()
        self._file_tasks = [] # (task, path, socket)

    def _should_update(self):
        return False

    def _should_check_for_updates(self):
        # TODO: Should be based on time
        return True

    def _next_file_task(self):
        for el in self._file_tasks:
            if not el.task.done:
                return el

        return None

    def _update(self):
        if not self._list_files_task.started:
            # Start listing files
            pass
        elif self._list_files_task.in_progress():
            # Wait for response
            pass

        next_file_task = self._next_file_task()
        if next_file_task is None:
            # Download complete
            # Cleanup
            pass
        elif not next_file_task.started:
            # Start next task
            pass
        elif next_file_task.in_progress():
            # Check progress and download
            pass

    def _check_for_updates(self):
        if self._update_summary_task.in_progress():

        elif self._check_for_updates_task.in_progress():
            # TODO: poll for respose until done
            # then, begin download task
            pass
        elif self._should_update:

        elif self._should_check_for_updates:
            # TODO: start task
            self._check_for_updates_task.started = True


    # if is checking version
    # - keep checking version
    # if

    def poll(self):
        if self._check_for_updates_task is None:
            self._check_for_updates_task = Task(None) # TODO: not none
        if self._check_for_updates_task.started is False:

