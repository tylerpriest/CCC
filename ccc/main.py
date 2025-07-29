import schedule
import time
import subprocess
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(filename='responses.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

PROMPTS_FILE = Path("prompts.jsonl")

def dispatch_prompt(prompt_text):
    """
    Dispatches a prompt to the Claude Code CLI.
    """
    logging.info(f"Dispatching prompt: {prompt_text}")
    try:
        # Assuming 'claude' is in the system's PATH
        result = subprocess.run(['claude', 'code', '-p', prompt_text],
                                capture_output=True, text=True, check=True)
        response = result.stdout
        logging.info(f"Received response: {response}")
    except FileNotFoundError:
        logging.error("The 'claude' command was not found.")
        logging.error("Please ensure the Claude Code CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling Claude Code CLI: {e}")
        logging.error(f"Stderr: {e.stderr}")


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

def add_prompt(prompt_text, schedule_text):
    """
    Adds a new prompt to the prompts file.
    """
    prompts = load_prompts()
    prompts.append({"prompt": prompt_text, "schedule": schedule_text})
    save_prompts(prompts)

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

def edit_prompt(prompt_index, new_prompt_text, new_schedule_text):
    """
    Edits a prompt by its index.
    """
    prompts = load_prompts()
    if 0 <= prompt_index < len(prompts):
        prompts[prompt_index]["prompt"] = new_prompt_text
        prompts[prompt_index]["schedule"] = new_schedule_text
        save_prompts(prompts)

def schedule_prompts():
    """
    Schedules all prompts from the prompts file.
    """
    prompts = load_prompts()
    for prompt in prompts:
        # Simple scheduling for now, will be expanded
        if prompt.get("schedule") == "every_minute":
            schedule.every().minute.do(dispatch_prompt, prompt_text=prompt["prompt"])

def main():
    """
    Main function to run the scheduler.
    """
    schedule_prompts()

    while True:
        schedule.run_pending()
        time.sleep(1)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Button, Input
from textual.containers import Container
from textual.screen import ModalScreen

class EditScreen(ModalScreen):
    """Screen with a dialog to edit a prompt."""

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
        yield Footer()
from textual.containers import VerticalScroll

        yield Container(
            DataTable(),
            VerticalScroll(
                Input(placeholder="Enter new prompt..."),
                Input(placeholder="Enter schedule (e.g., 'every_minute')"),
                Button("Add Prompt", id="add_prompt"),
            ),
        )

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Prompt", "Schedule", "Actions")
        self.update_table()

    def update_table(self):
        """Update the table with the latest prompts."""
        table = self.query_one(DataTable)
        table.clear()
        prompts = list_prompts()
        for i, prompt in enumerate(prompts):
            table.add_row(
                prompt["prompt"],
                prompt["schedule"],
                f"[link=edit:{i}]Edit[/link] | [link=delete:{i}]Delete[/link]",
            )

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Event handler for cell selection."""
        if event.cell_key.column_key == "Actions":
            action, index_str = event.value.split(":")
            index = int(index_str)
            if action == "delete":
                delete_prompt(index)
                self.update_table()
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
            self.update_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "add_prompt":
            prompt_input = self.query(Input)[0]
            schedule_input = self.query(Input)[1]
            prompt_text = prompt_input.value
            schedule_text = schedule_input.value
            if prompt_text and schedule_text:
                add_prompt(prompt_text, schedule_text)
                self.update_table()
                prompt_input.value = ""
                schedule_input.value = ""

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
