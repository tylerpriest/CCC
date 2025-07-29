# Claude Code Companion (CCC) - Documentation

This document provides a comprehensive overview of the Claude Code Companion (CCC) project, including its architecture, features, and user journey.

## How it Works

The Claude Code Companion is a Python application that consists of two main components that run concurrently:

1.  **Scheduler:** A background process that uses the `schedule` library to manage and dispatch prompts. It reads from a `prompts.jsonl` file to determine which prompts to run and when. When a prompt is due, it calls the Claude Code CLI using Python's `subprocess` module and logs the response to `responses.log`.

2.  **Text-based User Interface (TUI):** A user-facing interface built with the `textual` library. It allows users to manage their scheduled prompts. The TUI provides a simple and intuitive way to add, edit, and delete prompts, which are then saved to the `prompts.jsonl` file.

These two components run in separate threads, allowing the user to interact with the TUI while the scheduler runs seamlessly in the background.

## Current Features

- **Scheduling:** Schedule prompts using cron-style expressions for precise timing.
- **Conversational Workflows:** Chain prompts together to create complex, stateful conversations with Claude.
- **TUI Management:** A comprehensive TUI for managing prompts and conversations, including:
    - **Adding:** Add new prompts with a prompt text and schedule.
    - **Editing:** Modify existing prompts in a modal dialog.
    - **Deleting:** Remove prompts from the schedule.
    - **Conversation Management:** A dedicated screen for creating and managing conversations.
- **Logging:** All responses from the Claude Code CLI are logged to `responses.log` with a timestamp.
- **Configuration:** A configuration file for managing settings like API keys and file paths.
- **Extensibility:** The modular design allows for easy addition of new features.

## Planned Features

- **Advanced Scheduling:** Integration with a more powerful scheduling library or support for cron-style expressions.
- **API Integration:** Direct integration with the Claude API for more robust communication and error handling.
- **Configuration File:** A configuration file for managing settings like API keys and CLI paths.
- **Priority Levels:** The ability to assign priority levels to prompts.
- **Tagging:** The ability to tag prompts for better organization and filtering.

## User Acceptance Testing

For details on User Acceptance Testing (UAT), please see the [`UAT.md`](UAT.md) file.

## User Journey

A typical user journey for the Claude Code Companion is as follows:

1.  **Installation:** The user installs the necessary Python libraries (`schedule` and `textual`) and ensures the Claude Code CLI is installed and authenticated.

2.  **Launch:** The user launches the application by running `python ccc/main.py` from their terminal.

3.  **TUI Interaction:** The TUI opens in the terminal, displaying a table of scheduled prompts.
    - **Adding a Prompt:** The user enters a new prompt and a schedule in the input fields and clicks "Add Prompt". The new prompt appears in the table.
    - **Editing a Prompt:** The user clicks the "Edit" link next to a prompt. A dialog appears, allowing them to modify the prompt's text and schedule. They save the changes, and the table updates.
    - **Deleting a Prompt:** The user clicks the "Delete" link next to a prompt. The prompt is removed from the table and the underlying `prompts.jsonl` file.

4.  **Background Operation:** While the user interacts with the TUI, the scheduler runs in the background. When a scheduled prompt is due, it is dispatched to the Claude Code CLI.

5.  **Reviewing Responses:** The user can review the responses from Claude by checking the `responses.log` file.
