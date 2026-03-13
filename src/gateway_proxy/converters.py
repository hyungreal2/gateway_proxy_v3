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


def openai_to_anthropic(resp):

    msg = resp["choices"][0]["message"]

    if "tool_calls" in msg:

        call = msg["tool_calls"][0]

        return {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "name": call["function"]["name"],
                "input": call["function"]["arguments"]
            }]
        }

    return {
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": msg.get("content", "")
        }]
    }
