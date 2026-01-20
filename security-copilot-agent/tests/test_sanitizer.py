import pytest
from core import sanitizer

def test_sanitize_windows_path():
    raw_text = r"Error at C:\Users\Alice\Documents\secret.txt"
    expected = r"Error at C:\Users\[USER]\Documents\secret.txt"
    assert sanitizer.sanitize(raw_text) == expected

def test_sanitize_multiple_paths():
    raw_text = r"trace: C:\Users\Bob\App\Config vs C:\Users\Admin\System"
    expected = r"trace: C:\Users\[USER]\App\Config vs C:\Users\[USER]\System"
    assert sanitizer.sanitize(raw_text) == expected

def test_sanitize_no_sensitive_data():
    raw_text = "System32 call failed"
    assert sanitizer.sanitize(raw_text) == raw_text
