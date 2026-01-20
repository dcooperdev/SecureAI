import re

def sanitize(text: str) -> str:
    r"""
    Replaces C:\Users\<user>\ with C:\Users\[USER]\ in the given text.
    Non-greedy matching for the username part.
    """
    # Regex explanation:
    # C:\\Users\\  -> Match C:\Users\
    # [^\\]+       -> Match any character except backslash (username)
    # \\           -> Match the trailing backslash
    return re.sub(r'(C:\\Users\\[^\\]+)', r'C:\\Users\\[USER]', text)
