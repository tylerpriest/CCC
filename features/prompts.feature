Feature: Prompt Management
  As a user, I want to be able to manage my prompts, so that I can keep my schedule organized.

  Scenario: Scheduling a prompt
    Given I have launched the application
    When I add a new prompt with the text "Test prompt" and the schedule "* * * * *"
    Then the prompt should be added to the schedule

  Scenario: Creating a conversation
    Given I have launched the application
    When I create a new conversation
    And I add a prompt with the text "Prompt 1" to the conversation
    And I add a prompt with the text "Prompt 2" to the conversation
    And I save the conversation
    Then a new conversation should be created with 2 prompts

  Scenario: Editing a prompt
    Given I have added a prompt with the text "Original prompt" and the schedule "* * * * *"
    When I edit the prompt to have the text "Updated prompt"
    Then the prompt should be updated

  Scenario: Deleting a prompt
    Given I have added a prompt with the text "Test prompt" and the schedule "* * * * *"
    When I delete the prompt
    Then the prompt should be removed from the schedule
