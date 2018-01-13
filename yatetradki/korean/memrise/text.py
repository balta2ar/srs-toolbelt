import re


def cleanup(text):
    return re.sub(r'\s+', ' ', text.strip())
