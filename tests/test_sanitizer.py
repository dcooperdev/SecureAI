import pytest
from galt.core import sanitizer

def test_sanitize_windows_path():
    raw_text = r"Error at C:\Users\Alice\Documents\secret.txt"
    sanitized = sanitizer.sanitize(raw_text)
    assert r"C:\Users\[USER]" in sanitized
    assert "Alice" not in sanitized

def test_sanitize_linux_path():
    raw_text = "/home/bob/scripts/deploy.sh"
    sanitized = sanitizer.sanitize(raw_text)
    assert "/home/[USER]" in sanitized
    assert "bob" not in sanitized

def test_sanitize_mixed_paths():
    # Strict test: multiple users in one string
    raw_text = r"Compare C:\Users\Admin\Log.txt with /home/service/config"
    sanitized = sanitizer.sanitize(raw_text)
    assert r"C:\Users\[USER]" in sanitized
    assert "/home/[USER]" in sanitized
    assert "Admin" not in sanitized
    assert "service" not in sanitized

def test_sanitize_ip_address():
    raw_text = "Connection from 192.168.1.50 to 10.0.0.5"
    sanitized = sanitizer.sanitize(raw_text)
    assert "192.168.1.50" not in sanitized
    assert "10.0.0.5" not in sanitized
    assert "[IP]" in sanitized

def test_sanitize_hostname_unc():
    # Strict test: UNC path
    raw_text = r"Copying to \\SecretServer\Share"
    sanitized = sanitizer.sanitize(raw_text)
    assert r"\\[HOST]\Share" in sanitized
    assert "SecretServer" not in sanitized
