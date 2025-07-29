# Claude Code Companion (CCC)

A minimal, extensible system for scheduling and automatically sending prompts to Claude Code.

## Features

- **Schedule Prompts:** Schedule prompts to be sent to Claude Code at specific times (e.g., daily at 1:00 AM).
- **TUI:** A Text-based User Interface to manage prompts.
- **Logging:** Responses from Claude are logged for later review.
- **Extensible:** The system is designed to be easily expandable.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install schedule textual
    ```

2.  **Install Claude Code CLI:**
    Ensure you have the Claude Code CLI installed and authenticated.

## Usage

1.  **Run the application:**
    ```bash
    python ccc/main.py
    ```

2.  **Use the TUI:**
    - The TUI will open in your terminal.
    - You can view existing prompts in the table.
    - To add a new prompt, fill in the "Enter new prompt..." and "Enter schedule..." fields, then click "Add Prompt".

## Scheduling

The schedule format is based on the `schedule` library. Here are some examples:

- `every_minute`
- `every_hour`
- `daily at 13:15`
- `every monday`
- `every wednesday at 13:15`