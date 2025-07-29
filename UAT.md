# User Acceptance Test (UAT)

## User Story: Scheduling a Prompt

**As a user, I want to be able to write a prompt, choose a time to send the prompt, and at the assigned time, the prompt should be sent to the Claude Code CLI, and I should get a success notification.**

### Test Case 1: Scheduling a Prompt

**Objective:** To verify that a user can successfully schedule a prompt and receive a success notification.

**Prerequisites:**
*   The Claude Code Companion application is installed and running.
*   The Claude Code CLI is installed and authenticated.

**Test Steps:**
1.  Launch the Claude Code Companion application.
2.  Add a new prompt with the text "Write a python script to sort my downloads folder".
3.  Set the schedule for the prompt to be 1 minute from the current time.
4.  Wait for the scheduled time to pass.
5.  Check the `responses.log` file to verify that the prompt was dispatched and a response was received.
6.  Check the TUI for a notification indicating that the prompt was successfully dispatched.

**Expected Results:**
*   The prompt should be added to the schedule.
*   At the scheduled time, the prompt should be dispatched to the Claude Code CLI.
*   The `responses.log` file should contain the response from Claude.
*   The TUI should display a notification indicating that the prompt was successfully dispatched.
