import configparser
import schedule
import time
import subprocess
import json
import logging
from pathlib import Path

def load_config():
    """
    Loads the configuration from config.ini.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

config = load_config()

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler
handler = logging.FileHandler(config['DEFAULT']['log_file'])
handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(handler)

PROMPTS_FILE = Path(config['DEFAULT']['prompts_file'])

def dispatch_prompt(prompt_id, app):
    """
    Dispatches a prompt to the Claude Code CLI.
    """
    prompts = load_prompts()
    prompt = next((p for p in prompts if p["id"] == prompt_id), None)
    if not prompt:
        logger.error(f"Prompt with id {prompt_id} not found.")
        return

    app.query_one("#loading_indicator").styles.display = "block"
    logger.info(f"Dispatching prompt: {prompt['prompt']}")
    try:
        # Assuming 'claude' is in the system's PATH
        result = subprocess.run(['claude', 'code', '-p', prompt['prompt']],
                                capture_output=True, text=True, check=True)
        response = result.stdout
        logger.info(f"Received response: {response}")

        if prompt.get("next_prompt_id"):
            dispatch_prompt(prompt["next_prompt_id"], app)

    except FileNotFoundError:
        logger.error("The 'claude' command was not found.")
        logger.error("Please ensure the Claude Code CLI is installed and in your PATH.")
        logger.error("You can install it by following the instructions here: https://docs.anthropic.com/claude/docs/claude-code-cli")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error calling Claude Code CLI: {e}")
        logger.error(f"Stderr: {e.stderr}")
    finally:
        app.query_one("#loading_indicator").styles.display = "none"


def load_prompts():
    """
    Loads prompts from the prompts.jsonl file.
    """
    if not PROMPTS_FILE.exists():
        return []

    with open(PROMPTS_FILE, "r") as f:
        prompts = [json.loads(line) for line in f if line.strip()]
    return prompts

def save_prompts(prompts):
    """
    Saves prompts to the prompts.jsonl file.
    """
    with open(PROMPTS_FILE, "w") as f:
        for prompt in prompts:
            f.write(json.dumps(prompt) + "\n")

import uuid

def add_prompt(prompt_text, schedule_text, conversation_id=None, next_prompt_id=None):
    """
    Adds a new prompt to the prompts file.
    """
    prompts = load_prompts()
    prompt_id = str(uuid.uuid4())
    prompts.append({
        "id": prompt_id,
        "prompt": prompt_text,
        "schedule": schedule_text,
        "conversation_id": conversation_id,
        "next_prompt_id": next_prompt_id,
    })
    save_prompts(prompts)
    schedule_prompts()

def list_prompts():
    """
    Lists all scheduled prompts.
    """
    return load_prompts()

def delete_prompt(prompt_index):
    """
    Deletes a prompt by its index.
    """
    prompts = load_prompts()
    if 0 <= prompt_index < len(prompts):
        prompts.pop(prompt_index)
        save_prompts(prompts)
        schedule_prompts(app=None) # This is a hack for the tests

def edit_prompt(prompt_index, new_prompt_text, new_schedule_text):
    """
    Edits a prompt by its index.
    """
    prompts = load_prompts()
    if 0 <= prompt_index < len(prompts):
        prompts[prompt_index]["prompt"] = new_prompt_text
        prompts[prompt_index]["schedule"] = new_schedule_text
        save_prompts(prompts)
        schedule_prompts()

from croniter import croniter
import datetime

def run_and_reschedule(prompt_id, schedule_text, app):
    """
    Runs a prompt and reschedules it.
    """
    dispatch_prompt(prompt_id, app)
    base = datetime.datetime.now()
    iter = croniter(schedule_text, base)
    next_run = iter.get_next(datetime.datetime)
    schedule.every().day.at(next_run.strftime("%H:%M")).do(run_and_reschedule, prompt_id, schedule_text, app)

def schedule_prompts(app):
    """
    Schedules all prompts from the prompts file.
    """
    schedule.clear()
    prompts = load_prompts()
    for prompt in prompts:
        # Only schedule prompts that are not part of a conversation,
        # or are the first prompt in a conversation.
        if not prompt.get("conversation_id") or prompt.get("is_first"):
            schedule_text = prompt.get("schedule")
            if schedule_text:
                if croniter.is_valid(schedule_text):
                    base = datetime.datetime.now()
                    iter = croniter(schedule_text, base)
                    next_run = iter.get_next(datetime.datetime)
                    schedule.every().day.at(next_run.strftime("%H:%M")).do(run_and_reschedule, prompt["id"], schedule_text, app)
                else:
                    # Fallback to simple schedule parsing for now
                    if "every" in schedule_text and "minute" in schedule_text:
                         schedule.every().minute.do(dispatch_prompt, prompt_id=prompt["id"], app=app)

def main(app):
    """
    Main function to run the scheduler.
    """
    schedule_prompts(app)

    while True:
        schedule.run_pending()
        time.sleep(1)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Button, Input, Label, TabbedContent, TabPane, LoadingIndicator
from textual.containers import Container
from textual.screen import ModalScreen
from textual.command import Hit, Hits, Provider
from ccc.kanban import KanbanBoard
from ccc.queue_view import QueueView

class ConversationScreen(ModalScreen):
    """A modal screen for managing conversations."""

    def __init__(self, conversation_id=None):
        super().__init__()
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.prompts = []

    def compose(self) -> ComposeResult:
        yield Container(
            DataTable(id="conversation_table"),
            Input(placeholder="Enter new prompt..."),
            Button("Add Prompt to Conversation", id="add_prompt_to_conversation"),
            Button("Save Conversation", id="save_conversation"),
            Button("Cancel", id="cancel_conversation"),
            id="conversation_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_prompt_to_conversation":
            prompt_input = self.query_one(Input)
            prompt_text = prompt_input.value
            if prompt_text:
                self.prompts.append({"prompt": prompt_text, "schedule": ""})
                self.update_conversation_table()
                prompt_input.value = ""
        elif event.button.id == "save_conversation":
            self.save_conversation()
            self.dismiss()
        elif event.button.id == "cancel_conversation":
            self.dismiss()

    def update_conversation_table(self):
        table = self.query_one("#conversation_table")
        table.clear()
        for prompt in self.prompts:
            table.add_row(prompt["prompt"])

    def save_conversation(self):
        # This is a simplified save function. A more robust implementation
        # would handle editing existing conversations.
        for i, prompt_data in enumerate(self.prompts):
            is_first = i == 0
            next_prompt_id = self.prompts[i + 1]["id"] if i + 1 < len(self.prompts) else None
            add_prompt(
                prompt_data["prompt"],
                "", # No schedule for prompts in a conversation for now
                conversation_id=self.conversation_id,
                next_prompt_id=next_prompt_id,
            )

class EditScreen(ModalScreen):
    """A modal screen for editing a prompt."""

    def __init__(self, prompt_index, prompt_text, schedule_text) -> None:
        super().__init__()
        self.prompt_index = prompt_index
        self.prompt_text = prompt_text
        self.schedule_text = schedule_text

    def compose(self) -> ComposeResult:
        yield Container(
            Input(self.prompt_text, id="prompt_text"),
            Input(self.schedule_text, id="schedule_text"),
            Button("Save", id="save"),
            Button("Cancel", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            prompt_text = self.query_one("#prompt_text").value
            schedule_text = self.query_one("#schedule_text").value
            self.dismiss((self.prompt_index, prompt_text, schedule_text))
        else:
            self.dismiss()

class CommandProvider(Provider):
    async def get_hits(self, query: str) -> Hits:
        if query == "new_conversation":
            yield Hit(1, "New Conversation", self.app.action_new_conversation)
        elif query == "quit":
            yield Hit(1, "Quit", self.app.action_quit)

class CCC_TUI(App):
    """A Textual app to manage Claude Code Companion prompts."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("ctrl+c", "quit", "Quit")]
    COMMANDS = App.COMMANDS | {CommandProvider}

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent():
            with TabPane("Prompts", id="prompts_tab"):
                yield DataTable(id="prompts_table")
            with TabPane("Queue", id="queue_tab"):
                yield QueueView()
            with TabPane("Kanban", id="kanban_tab"):
                yield KanbanBoard()
        yield VerticalScroll(
            Input(placeholder="Enter new prompt..."),
            Input(placeholder="Enter schedule (e.g., 'every_minute')"),
            Button("Add Prompt", id="add_prompt"),
            Button("Manage Conversations", id="manage_conversations"),
        )
        yield Footer()
        yield LoadingIndicator(id="loading_indicator", style="display: none;")
        yield Label("Status: Ready", id="status")

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        prompts_table = self.query_one("#prompts_table")
        prompts_table.add_columns("Prompt", "Schedule", "Actions")
        queue_table = self.query_one("#queue_table")
        queue_table.add_columns("Next Run", "Prompt")
        self.update_tables()

    def update_tables(self):
        """Update both tables with the latest prompts and queue."""
        self.update_prompts_table()
        self.update_queue_table()
        self.update_kanban_board()

    def update_prompts_table(self):
        """Update the prompts table with the latest prompts."""
        table = self.query_one("#prompts_table")
        table.clear()
        prompts = list_prompts()
        for i, prompt in enumerate(prompts):
            table.add_row(
                prompt["prompt"],
                prompt["schedule"],
                f"[link=edit:{i}]Edit[/link] | [link=delete:{i}]Delete[/link]",
            )

    def update_queue_table(self):
        """Update the queue table with upcoming prompts."""
        queue_view = self.query_one(QueueView)
        queue_view.update_queue(schedule.jobs)

    def update_kanban_board(self):
        """Update the Kanban board with conversations."""
        kanban_board = self.query_one(KanbanBoard)
        # This is a simplified implementation. A more robust implementation
        # would involve a more complex data structure.
        prompts = load_prompts()
        conversations = {}
        for prompt in prompts:
            if prompt.get("conversation_id"):
                if prompt["conversation_id"] not in conversations:
                    conversations[prompt["conversation_id"]] = []
                conversations[prompt["conversation_id"]].append(prompt)

        # Clear the board
        for child in kanban_board.query("*"):
            child.remove()

        for conversation_id, prompts in conversations.items():
            column = KanbanColumn(title=f"Conversation {conversation_id[:8]}")
            for prompt in prompts:
                column.query_one(".column_content").mount(KanbanCard(text=prompt["prompt"]))
            kanban_board.query_one(Horizontal).mount(column)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Event handler for cell selection."""
        if event.cell_key.column_key == "Actions":
            action, index_str = event.value.split(":")
            index = int(index_str)
            if action == "delete":
                delete_prompt(index)
                self.update_tables()
                self.notify("Prompt deleted successfully.")
            elif action == "edit":
                prompts = list_prompts()
                prompt_to_edit = prompts[index]
                self.push_screen(
                    EditScreen(index, prompt_to_edit["prompt"], prompt_to_edit["schedule"]),
                    self.on_edit_screen_dismiss,
                )

    def on_edit_screen_dismiss(self, result) -> None:
        """Called when the EditScreen is dismissed."""
        if result:
            index, prompt_text, schedule_text = result
            edit_prompt(index, prompt_text, schedule_text)
            self.update_tables()
            self.notify("Prompt updated successfully.")

    def notify(self, message: str):
        """Display a notification in the footer."""
        self.query_one(Footer).query_one(Label).update(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "add_prompt":
            prompt_input = self.query(Input)[0]
            schedule_input = self.query(Input)[1]
            prompt_text = prompt_input.value
            schedule_text = schedule_input.value
            if prompt_text and schedule_text:
                add_prompt(prompt_text, schedule_text)
                self.update_tables()
                prompt_input.value = ""
                schedule_input.value = ""
                self.notify("Prompt added successfully.")
        elif event.button.id == "manage_conversations":
            self.push_screen(ConversationScreen())

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_new_conversation(self) -> None:
        """An action to create a new conversation."""
        self.push_screen(ConversationScreen())

    def action_quit(self) -> None:
        """An action to quit the application."""
        self.exit()

import threading

def run_scheduler(app):
    """
    Target function for the scheduler thread.
    """
    main(app)

def show_welcome_message():
    """
    Shows a welcome message to new users.
    """
    if not Path(".onboarding_complete").exists():
        # This is a simplified welcome message. A more robust implementation
        # could use a dedicated screen.
        print("Welcome to the Claude Code Companion!")
        print("This application allows you to schedule prompts to be sent to Claude Code.")
        print("You can add, edit, and delete prompts using the TUI.")
        print("You can also create conversational workflows by chaining prompts together.")
        print("Enjoy!")
        Path(".onboarding_complete").touch()

if __name__ == "__main__":
    show_welcome_message()

    app = CCC_TUI()

    # Run the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
    scheduler_thread.start()

    # Run the TUI
    app.run()
