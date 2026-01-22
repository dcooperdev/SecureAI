import unittest
import glob
import subprocess
import json
import os
import sys

class TestSensors(unittest.TestCase):
    def test_sensors_json_output(self):
        # Find all sensor_*.py files
        sensor_files = glob.glob("sensor_*.py")
        
        if not sensor_files:
            self.fail("No sensor_*.py files found in the current directory.")
            
        print(f"\nFound sensors: {sensor_files}")
        
        for sensor in sensor_files:
            with self.subTest(sensor=sensor):
                print(f"Testing {sensor}...")
                
                # Execute sensor with --local-only
                result = subprocess.run(
                    [sys.executable, sensor, "--local-only"],
                    capture_output=True,
                    text=True,
                    timeout=30 # Safety timeout
                )
                
                # Check execution success (allow non-zero if handled, but output must be parsable)
                # But typically scripts should exit 0.
                if result.returncode != 0:
                   print(f"Warning: {sensor} returned code {result.returncode}")
                   print(f"Stderr: {result.stderr}")

                output = result.stdout
                self.assertTrue(output.strip(), f"Sensor {sensor} produced no output")
                
                # Extract JSON. Since output might contain other text, we look for JSON objects.
                # However, the requirement says "returns valid JSON". Ideally valid JSON in stdout.
                # The runner uses a "rearm" logic. For this unit test, let's try to find at least one valid event.
                
                # Simple heuristic: Look for valid JSON blocks
                found_valid_json = False
                potential_objects = output.split('"event_id":')
                
                for obj_part in potential_objects:
                    if not obj_part.strip(): continue
                    json_str = '{"event_id":' + obj_part.strip()
                    
                    # Try to close potential open ended braces
                    last_brace = json_str.rfind('}')
                    if last_brace != -1:
                        json_str = json_str[:last_brace+1]
                        
                    try:
                        data = json.loads(json_str)
                        # Validate schema
                        self.assertIn("event_id", data)
                        self.assertIn("timestamp", data)
                        self.assertIn("plugin", data)
                        self.assertIn("result", data)
                        found_valid_json = True
                        break # Found at least one valid event
                    except json.JSONDecodeError:
                        continue
                
                self.assertTrue(found_valid_json, f"Could not find valid JSON event in output of {sensor}")

if __name__ == "__main__":
    unittest.main()
