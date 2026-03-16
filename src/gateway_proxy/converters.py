def anthropic_to_openai_messages(messages):

    out = []

    for m in messages:

        if isinstance(m["content"], str):
            out.append({
                "role": m["role"],
                "content": m["content"]
            })
            continue

        text = []

        for block in m["content"]:

            if block.get("type") == "text":
                text.append(block.get("text"))

        out.append({
            "role": m["role"],
            "content": "\n".join(text)
        })

    return out


def _map_stop_reason(finish_reason):
    mapping = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
    }
    return mapping.get(finish_reason, "end_turn")


def openai_to_anthropic(resp, model="unknown"):

    from uuid import uuid4

    choice = resp["choices"][0]
    msg = choice["message"]
    finish_reason = choice.get("finish_reason")

    if "tool_calls" in msg:

        content = []
        for call in msg["tool_calls"]:
            content.append({
                "type": "tool_use",
                "id": call.get("id", "call_" + uuid4().hex[:8]),
                "name": call["function"]["name"],
                "input": call["function"]["arguments"],
            })

    else:
        content = [{
            "type": "text",
            "text": msg.get("content", "")
        }]

    usage = resp.get("usage", {})

    return {
        "id": "msg_" + uuid4().hex[:8],
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": _map_stop_reason(finish_reason),
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }
