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

class CCC_TUI(App):
    """A Textual app to manage Claude Code Companion prompts."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Container(
            DataTable(),
            Input(placeholder="Enter new prompt..."),
            Input(placeholder="Enter schedule (e.g., 'every_minute')"),
            Button("Add Prompt", id="add_prompt"),
        )

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Prompt", "Schedule")
        self.update_table()

    def update_table(self):
        """Update the table with the latest prompts."""
        table = self.query_one(DataTable)
        table.clear()
        prompts = list_prompts()
        for prompt in prompts:
            table.add_row(prompt["prompt"], prompt["schedule"])

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
