from .task import Task, HttpTask

class Updater:

    def __init__(self, github_repo, app_dir='app', headers={}):
        self.github_repo = github_repo.rstrip('/').replace('https://github.com/', '')
        self.app_dir = app_dir
        self.headers = headers

        self._check_for_updates_task = HttpTask(
            'https://api.github.com/repos/{}/releases/latest'.format(self.github_repo),
            headers=headers,
        )
        self._update_summary_task = Task()
        self._list_files_task = HttpTask('')
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
        if self._update_summary_task.started:
            return
        elif self._check_for_updates_task.in_progress():
            # TODO: poll for respose until done
            # then, begin download task
            pass# url = 'https://api.github.com/repos/{}/contents{}{}?ref=refs/tags/{}'.format(self.github_repo, self.main_dir, sub_dir, version)
        # print(url)
        elif self._should_update:
            self._update_summary_task.started = True
            # start the update
            pass
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

