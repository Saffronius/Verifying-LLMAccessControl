#!/usr/bin/env python3
"""
Test suite for Exp-2.py functionality
Tests core functions without running the full experiment
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
import importlib.util
spec = importlib.util.spec_from_file_location("exp2", "../Exp-2.py")
exp2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp2)


class TestExp2Functions(unittest.TestCase):
    """Test core functions of Exp-2.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::example-bucket/*"
                }
            ]
        }
        
        self.test_strings = """arn:aws:s3:::example-bucket/file1.txt
arn:aws:s3:::example-bucket/file2.txt
arn:aws:s3:::example-bucket/dir/file3.txt"""
        
        self.test_regex = "arn:aws:s3:::example-bucket/.*"
        
    def test_read_policy_file(self):
        """Test reading a policy file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_policy, f)
            temp_path = f.name
        
        try:
            content = exp2.read_policy_file(temp_path)
            self.assertIsInstance(content, str)
            policy = json.loads(content)
            self.assertEqual(policy['Version'], '2012-10-17')
            self.assertIn('Statement', policy)
        finally:
            os.unlink(temp_path)
    
    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='test strings')
    def test_generate_strings(self, mock_file, mock_run):
        """Test string generation from policy"""
        mock_run.return_value = MagicMock(
            stdout="String generation output",
            stderr="",
            returncode=0
        )
        
        result = exp2.generate_strings("/fake/policy.json", 100)
        
        self.assertEqual(result, 'test strings')
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('quacky.py', args[1])
        self.assertIn('-m', args)
        self.assertIn('100', args)
    
    @patch.object(exp2.client, 'responses')
    def test_generate_regex(self, mock_responses):
        """Test regex generation from strings"""
        # Mock GPT-5 response structure
        mock_response = MagicMock()
        mock_item = MagicMock()
        mock_content = MagicMock()
        mock_content.text = self.test_regex
        mock_item.content = [mock_content]
        mock_response.output = [mock_item]
        
        mock_responses.create.return_value = mock_response
        
        result = exp2.generate_regex(self.test_strings)
        
        self.assertEqual(result, self.test_regex)
        mock_responses.create.assert_called_once()
        
        # Check that the response was written to file
        call_args = mock_responses.create.call_args
        self.assertEqual(call_args[1]['model'], 'gpt-5')
        self.assertIn('reasoning', call_args[1])
    
    def test_parse_analysis(self):
        """Test parsing of analysis output"""
        sample_output = """
Policy 1
Solve Time (ms): 123
satisfiability: sat
Count Time (ms): 456
lg(requests): 10.5

-----------------------------------------------------------
Baseline Regex Count          : 100
Synthesized Regex Count       : 95
Baseline_Not_Synthesized Count: 5
Not_Baseline_Synthesized_Count: 0
regex_from_dfa                : pattern1
regex_from_llm                : pattern2
ops_regex_from_dfa            : 10
ops_regex_from_llm            : 8
length_regex_from_dfa         : 50
length_regex_from_llm         : 45
jaccard_numerator             : 90
jaccard_denominator           : 100
"""
        
        # Access the parse_analysis function from the module
        parse_func = None
        exec_locals = {}
        with open('../Exp-2.py', 'r') as f:
            code = f.read()
            exec(compile(code, '../Exp-2.py', 'exec'), exec_locals)
            parse_func = exec_locals['parse_analysis']
        
        result = parse_func(sample_output)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['Baseline Regex Count'], '100')
        self.assertEqual(result['Synthesized Regex Count'], '95')
        self.assertEqual(result['regex_from_dfa'], 'pattern1')
        self.assertEqual(result['regex_from_llm'], 'pattern2')
    
    @patch('subprocess.run')
    def test_run_final_analysis_success(self, mock_run):
        """Test successful final analysis"""
        mock_run.return_value = MagicMock(
            stdout="Analysis successful output",
            stderr="",
            returncode=0
        )
        
        result = exp2.run_final_analysis("/fake/policy.json")
        
        self.assertEqual(result, "Analysis successful output")
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_final_analysis_failure(self, mock_run):
        """Test failed final analysis"""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="FATAL ERROR FROM ABC",
            returncode=1
        )
        
        result = exp2.run_final_analysis("/fake/policy.json")
        
        self.assertIsNone(result)
    
    def test_progress_tracking(self):
        """Test progress save/load functionality"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Patch the progress_file_path
            original_path = exp2.progress_file_path
            exp2.progress_file_path = temp_path
            
            # Test saving progress
            exp2.update_progress(5)
            
            # Test loading progress
            progress = exp2.get_progress()
            self.assertEqual(progress['last_processed'], 5)
            
        finally:
            exp2.progress_file_path = original_path
            os.unlink(temp_path)
    
    def test_sort_key_function(self):
        """Test the filename sorting function"""
        # Access the sort_key function
        exec_locals = {}
        with open('../Exp-2.py', 'r') as f:
            code = f.read()
            exec(compile(code, '../Exp-2.py', 'exec'), exec_locals)
            sort_key = exec_locals['sort_key'] if 'sort_key' in exec_locals else None
        
        if sort_key:
            # Test various filename formats
            self.assertEqual(sort_key('policy_1.json'), 1)
            self.assertEqual(sort_key('policy_10.json'), 10)
            self.assertEqual(sort_key('policy_100.json'), 100)
            self.assertEqual(sort_key('no_number.json'), 0)


class TestDataProcessing(unittest.TestCase):
    """Test data processing and CSV operations"""
    
    def test_csv_creation(self):
        """Test CSV file creation with proper columns"""
        required_columns = [
            "model_name", "Original Policy", "Size", 
            "Regex from llm", "Experiment 2_Analysis", "Errors"
        ]
        
        # Create a test DataFrame
        df = pd.DataFrame(columns=required_columns)
        
        # Add a test row
        test_row = {
            "model_name": "gpt-5",
            "Original Policy": '{"test": "policy"}',
            "Size": 100,
            "Regex from llm": "test.*regex",
            "Experiment 2_Analysis": "Test output",
            "Errors": ""
        }
        
        df = pd.concat([df, pd.DataFrame([test_row])], ignore_index=True)
        
        # Verify structure
        self.assertEqual(len(df), 1)
        self.assertEqual(list(df.columns), required_columns)
        self.assertEqual(df.iloc[0]['model_name'], 'gpt-5')


if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)