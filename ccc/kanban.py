from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal
from textual.events import MouseDown, MouseUp, MouseMove

class KanbanBoard(Static):
    """A Kanban board widget."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dragging = None
        self.drag_offset = (0, 0)

    def compose(self) -> ComposeResult:
        yield Horizontal()

    def on_mouse_down(self, event: MouseDown) -> None:
        if isinstance(event.widget, KanbanCard):
            self.dragging = event.widget
            self.drag_offset = event.x - self.dragging.region.x, event.y - self.dragging.region.y

    def on_mouse_move(self, event: MouseMove) -> None:
        if self.dragging:
            self.dragging.styles.offset = (event.x - self.drag_offset[0], event.y - self.drag_offset[1])

    def on_mouse_up(self, event: MouseUp) -> None:
        if self.dragging:
            # This is where the logic to update the data would go
            self.dragging.styles.offset = (0, 0)
            self.dragging = None

class KanbanColumn(Static):
    """A column on the Kanban board."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def compose(self) -> ComposeResult:
        yield Static(self.title, classes="column_title")
        yield Static(classes="column_content")

class KanbanCard(Static):
    """A card on the Kanban board."""

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def compose(self) -> ComposeResult:
        yield Static(self.text)
