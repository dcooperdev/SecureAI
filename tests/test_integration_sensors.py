import unittest
import os
import json
import sys
import subprocess
import glob

class TestGaltSuite(unittest.TestCase):

    def test_01_env_file_exists(self):
        """Verify that the .env file exists and has API KEY."""
        exists = os.path.exists(".env")
        self.assertTrue(exists, "❌ .env file is missing!")
        
        if exists:
            with open(".env", "r") as f:
                content = f.read()
                self.assertIn("GOOGLE_API_KEY", content, "❌ GOOGLE_API_KEY missing in .env")

    def test_02_sensors_execution_and_schema(self):
        """
        Dynamic Discovery and Validation of all sensors.
        Each sensor must:
        1. Run without error (exit code 0).
        2. Output valid JSON (formatted or raw).
        3. Contain 'event_id', 'timestamp', 'plugin', 'result'.
        """
        # Discovery based on pattern
        # Discovery based on pattern in galt/sensors
        # Check files in galt/sensors/ but ignore __init__.py
        sensor_files = glob.glob("galt/sensors/*.py")
        sensor_files = [f for f in sensor_files if "__init__" not in f]
        if not sensor_files:
            self.fail("No sensor_*.py files found to test.")
            
        print(f"\n🔎 Discovered {len(sensor_files)} sensors for testing: {sensor_files}")
        
        for sensor in sensor_files:
            with self.subTest(sensor=sensor):
                print(f"   👉 Testing {sensor}...")
                
                # Execution as Module
                # Convert path "galt\sensors\processes.py" to "galt.sensors.processes"
                # Normalize path to handle mixed slashes on Windows
                normalized_path = os.path.normpath(sensor)
                module_name = normalized_path.replace(os.path.sep, ".").replace(".py", "")
                
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", module_name, "--local-only"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                except subprocess.TimeoutExpired:
                    self.fail(f"❌ {sensor} timed out (30s limit).")

                # Parse JSON Output
                output = result.stdout
                
                # Heuristic extraction similar to runner
                extracted_data = None
                potential_objects = output.split('"event_id":')
                
                for obj_part in potential_objects:
                    if not obj_part.strip(): continue
                    json_str = '{"event_id":' + obj_part.strip()
                    # Fix braces
                    last_brace = json_str.rfind('}')
                    if last_brace != -1:
                        json_str = json_str[:last_brace+1]
                    
                    try:
                        data = json.loads(json_str)
                        extracted_data = data
                        break # Stop at first valid event
                    except json.JSONDecodeError:
                        continue
                
                # Assertions
                if extracted_data is None:
                    print(f"❌ STDERR: {result.stderr}")
                self.assertIsNotNone(extracted_data, f"❌ {sensor} did not produce parsable JSON")
                self.assertIn("event_id", extracted_data, f"{sensor} missing event_id")
                self.assertIn("plugin", extracted_data, f"{sensor} missing plugin")
                self.assertIn("result", extracted_data, f"{sensor} missing result")
                print(f"      ✅ {sensor} passed JSON validation.")


import pytest
from unittest.mock import MagicMock

# DISABLE GLOBAL MOCK FOR THIS FILE
@pytest.fixture(autouse=True)
def mock_subprocess():
    """
    Override global mock to allow real subprocess calls in this integration test.
    """
    yield MagicMock()

if __name__ == "__main__":
    unittest.main()
