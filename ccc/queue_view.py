from textual.app import ComposeResult
from textual.widgets import Static, DataTable

class QueueView(Static):
    """A widget to display the prompt queue."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="queue_table")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Next Run", "Prompt")

    def update_queue(self, jobs):
        table = self.query_one(DataTable)
        table.clear()
        for job in jobs:
            table.add_row(str(job.next_run), str(job.job_func))
