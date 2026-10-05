from multiprocessing import Process, Pipe

from gi.repository import GLib

from apostrophe.stats_counter_worker import count_worker


class StatsCounter:
    """Counts characters, words, sentences
    and read time using a worker process."""

    def __init__(self, callback):
        super().__init__()

        # Worker process to handle counting.
        self.counting = False
        self.count_pending_text = None
        self.parent_conn, child_conn = Pipe()
        worker = Process(target=count_worker, args=(child_conn,), daemon=True)
        worker.start()
        child_conn.close()
        GLib.io_add_watch(
            self.parent_conn.fileno(), GLib.PRIORITY_LOW, GLib.IO_IN,
            self.on_counted, callback)

    def count(self, text):
        """Count stats for text.

        In case counting is already running, it will re-count once it finishes.
        This ensure that the pipe doesn't fill (and block) if multiple requests
        are made in quick succession."""

        if not self.counting:
            self.counting = True
            self.count_pending_text = None
            self.parent_conn.send(text)
        else:
            self.count_pending_text = text

    def on_counted(self, _source, _condition, callback):
        """Reads the counting result from the pipe
        and triggers any pending count."""

        self.counting = False
        if self.count_pending_text is not None:
            # self.count clears the pending text.
            self.count(self.count_pending_text)

        try:
            if self.parent_conn.poll():
                callback(self.parent_conn.recv())
            return True
        except EOFError:
            return False

    def stop(self):
        """Stops the worker process.
        StatsCounter shouldn't be used after this."""

        self.parent_conn.close()
