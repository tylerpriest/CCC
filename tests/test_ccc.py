import unittest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ccc.main import (
    load_prompts,
    save_prompts,
    add_prompt,
    delete_prompt,
    edit_prompt,
    schedule_prompts,
    dispatch_prompt,
)

class TestCCC(unittest.TestCase):
    def setUp(self):
        """Set up a temporary prompts file for testing."""
        self.test_prompts_file = Path("test_prompts.jsonl")
        # Start patching `PROMPTS_FILE`
        self.prompts_file_patcher = patch('ccc.main.PROMPTS_FILE', self.test_prompts_file)
        self.mock_prompts_file = self.prompts_file_patcher.start()

        self.test_prompts = [
            {"prompt": "Test prompt 1", "schedule": "* * * * *"},
            {"prompt": "Test prompt 2", "schedule": "0 0 * * *"},
        ]
        save_prompts(self.test_prompts)

    def tearDown(self):
        """Remove the temporary prompts file and stop patching."""
        if self.test_prompts_file.exists():
            self.test_prompts_file.unlink()
        # Stop patching
        self.prompts_file_patcher.stop()

    @patch('ccc.main.PROMPTS_FILE', new_callable=lambda: Path("test_prompts.jsonl"))
    def test_load_prompts(self, mock_prompts_file):
        """Test loading prompts from a file."""
        prompts = load_prompts()
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0]["prompt"], "Test prompt 1")

    @patch('ccc.main.PROMPTS_FILE', new_callable=lambda: Path("test_prompts.jsonl"))
    def test_add_prompt(self, mock_prompts_file):
        """Test adding a new prompt."""
        add_prompt("Test prompt 3", "0 12 * * *")
        prompts = load_prompts()
        self.assertEqual(len(prompts), 3)
        self.assertEqual(prompts[2]["prompt"], "Test prompt 3")

    @patch('ccc.main.PROMPTS_FILE', new_callable=lambda: Path("test_prompts.jsonl"))
    def test_delete_prompt(self, mock_prompts_file):
        """Test deleting a prompt."""
        delete_prompt(0)
        prompts = load_prompts()
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0]["prompt"], "Test prompt 2")

    @patch('ccc.main.PROMPTS_FILE', new_callable=lambda: Path("test_prompts.jsonl"))
    def test_edit_prompt(self, mock_prompts_file):
        """Test editing a prompt."""
        edit_prompt(0, "Updated prompt", "15 * * * *")
        prompts = load_prompts()
        self.assertEqual(prompts[0]["prompt"], "Updated prompt")
        self.assertEqual(prompts[0]["schedule"], "15 * * * *")

    @patch('ccc.main.schedule')
    @patch('ccc.main.PROMPTS_FILE', new_callable=lambda: Path("test_prompts.jsonl"))
    def test_schedule_prompts(self, mock_prompts_file, mock_schedule):
        """Test scheduling prompts."""
        schedule_prompts()
        self.assertEqual(mock_schedule.every().day.at.call_count, 2)

    @patch('ccc.main.subprocess.run')
    def test_dispatch_prompt(self, mock_run):
        """Test dispatching a prompt."""
        mock_result = MagicMock()
        mock_result.stdout = "Test response"
        mock_run.return_value = mock_result

        dispatch_prompt("Test prompt")
        mock_run.assert_called_once_with(
            ['claude', 'code', '-p', 'Test prompt'],
            capture_output=True, text=True, check=True
        )

if __name__ == '__main__':
    unittest.main()
