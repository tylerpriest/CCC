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

def dispatch_prompt(prompt_id):
    """
    Dispatches a prompt to the Claude Code CLI.
    """
    prompts = load_prompts()
    prompt = next((p for p in prompts if p["id"] == prompt_id), None)
    if not prompt:
        logger.error(f"Prompt with id {prompt_id} not found.")
        return

    logger.info(f"Dispatching prompt: {prompt['prompt']}")
    try:
        # Assuming 'claude' is in the system's PATH
        result = subprocess.run(['claude', 'code', '-p', prompt['prompt']],
                                capture_output=True, text=True, check=True)
        response = result.stdout
        logger.info(f"Received response: {response}")

        if prompt.get("next_prompt_id"):
            dispatch_prompt(prompt["next_prompt_id"])

    except FileNotFoundError:
        logger.error("The 'claude' command was not found.")
        logger.error("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error calling Claude Code CLI: {e}")
        logger.error(f"Stderr: {e.stderr}")


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
        schedule_prompts()

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

def run_and_reschedule(prompt_id, schedule_text):
    """
    Runs a prompt and reschedules it.
    """
    dispatch_prompt(prompt_id)
    base = datetime.datetime.now()
    iter = croniter(schedule_text, base)
    next_run = iter.get_next(datetime.datetime)
    schedule.every().day.at(next_run.strftime("%H:%M")).do(run_and_reschedule, prompt_id, schedule_text)

def schedule_prompts():
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
                    schedule.every().day.at(next_run.strftime("%H:%M")).do(run_and_reschedule, prompt["id"], schedule_text)
                else:
                    # Fallback to simple schedule parsing for now
                    if "every" in schedule_text and "minute" in schedule_text:
                         schedule.every().minute.do(dispatch_prompt, prompt_id=prompt["id"])

def main():
    """
    Main function to run the scheduler.
    """
    schedule_prompts()

    while True:
        schedule.run_pending()
        time.sleep(1)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Button, Input, Label, TabbedContent, TabPane
from textual.containers import Container
from textual.screen import ModalScreen

class ConversationScreen(ModalScreen):
    """A modal screen for managing conversations."""

    def __init__(self, conversation_id=None):
        super().__init__()
        self.conversation_id = conversation_id

    def compose(self) -> ComposeResult:
        yield Container(
            DataTable(id="conversation_table"),
            Input(placeholder="Enter new prompt..."),
            Button("Add Prompt to Conversation", id="add_prompt_to_conversation"),
            Button("Save Conversation", id="save_conversation"),
            Button("Cancel", id="cancel_conversation"),
            id="conversation_dialog",
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

class CCC_TUI(App):
    """A Textual app to manage Claude Code Companion prompts."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent():
            with TabPane("Prompts", id="prompts_tab"):
                yield DataTable(id="prompts_table")
            with TabPane("Queue", id="queue_tab"):
                yield DataTable(id="queue_table")
        yield VerticalScroll(
            Input(placeholder="Enter new prompt..."),
            Input(placeholder="Enter schedule (e.g., 'every_minute')"),
            Button("Add Prompt", id="add_prompt"),
            Button("Manage Conversations", id="manage_conversations"),
        )
        yield Footer()
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
        table = self.query_one("#queue_table")
        table.clear()

        # This is a simplified queue view. A more robust implementation
        # would require inspecting the schedule more deeply.
        for job in schedule.jobs:
            table.add_row(str(job.next_run), str(job.job_func))

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

import threading

def run_scheduler():
    """
    Target function for the scheduler thread.
    """
    main()

if __name__ == "__main__":
    # Run the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Run the TUI
    app = CCC_TUI()
    app.run()
