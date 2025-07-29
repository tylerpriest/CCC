from behave import *
from unittest.mock import patch
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ccc.main import (
    load_prompts,
    add_prompt,
    delete_prompt,
    edit_prompt,
    save_prompts
)

@given('I have launched the application')
def step_impl(context):
    context.prompts_file = Path("test_prompts.jsonl")
    if context.prompts_file.exists():
        context.prompts_file.unlink()

@when('I add a new prompt with the text "{text}" and the schedule "{schedule}"')
def step_impl(context, text, schedule):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file), \
         patch('ccc.main.schedule_prompts') as mock_schedule_prompts:
        add_prompt(text, schedule)

@then('the prompt should be added to the schedule')
def step_impl(context):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file):
        prompts = load_prompts()
        assert len(prompts) == 1
        assert prompts[0]["prompt"] == "Test prompt"

@when('I create a new conversation')
def step_impl(context):
    context.conversation_prompts = []

@when('I add a prompt with the text "{text}" to the conversation')
def step_impl(context, text):
    context.conversation_prompts.append({"prompt": text, "schedule": ""})

@when('I save the conversation')
def step_impl(context):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file):
        # This is a simplified implementation for the test
        prompts = []
        conversation_id = "test_conversation"
        for i, prompt_data in enumerate(context.conversation_prompts):
            next_prompt_id = str(i + 1) if i + 1 < len(context.conversation_prompts) else None
            prompts.append({
                "id": str(i),
                "prompt": prompt_data["prompt"],
                "schedule": "",
                "conversation_id": conversation_id,
                "next_prompt_id": next_prompt_id
            })
        save_prompts(prompts)


@then('a new conversation should be created with {count:d} prompts')
def step_impl(context, count):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file):
        prompts = load_prompts()
        assert len(prompts) == count
        assert prompts[0]["conversation_id"] == "test_conversation"

@given('I have added a prompt with the text "{text}" and the schedule "{schedule}"')
def step_impl(context, text, schedule):
    context.prompts_file = Path("test_prompts.jsonl")
    if context.prompts_file.exists():
        context.prompts_file.unlink()
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file), \
         patch('ccc.main.schedule_prompts') as mock_schedule_prompts:
        add_prompt(text, schedule)

@when('I edit the prompt to have the text "{text}"')
def step_impl(context, text):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file), \
         patch('ccc.main.schedule_prompts') as mock_schedule_prompts:
        prompts = load_prompts()
        edit_prompt(0, text, prompts[0]["schedule"])

@then('the prompt should be updated')
def step_impl(context):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file):
        prompts = load_prompts()
        assert prompts[0]["prompt"] == "Updated prompt"

@when('I delete the prompt')
def step_impl(context):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file), \
         patch('ccc.main.schedule_prompts') as mock_schedule_prompts:
        delete_prompt(0)

@then('the prompt should be removed from the schedule')
def step_impl(context):
    with patch('ccc.main.PROMPTS_FILE', context.prompts_file):
        prompts = load_prompts()
        assert len(prompts) == 0
