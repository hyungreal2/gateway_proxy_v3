import json
import re


def parse_tool_from_text(text):

    if not text:
        return None

    m = re.search(r"<tool_call>(.*?)</tool_call>", text, re.S)

    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return None

    try:
        return json.loads(text)
    except Exception:
        return None
