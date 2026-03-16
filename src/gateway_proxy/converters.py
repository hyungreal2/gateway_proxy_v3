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


def anthropic_to_gemini(req):
    contents = []
    for msg in req.get("messages", []):
        role = "model" if msg["role"] == "assistant" else "user"
        content = msg["content"]
        if isinstance(content, str):
            parts = [{"text": content}]
        else:
            parts = [{"text": b["text"]} for b in content if b.get("type") == "text"]
        contents.append({"role": role, "parts": parts})

    payload = {"contents": contents}

    system = req.get("system")
    if system:
        if isinstance(system, str):
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        elif isinstance(system, list):
            parts = [{"text": b["text"]} for b in system if b.get("type") == "text"]
            payload["systemInstruction"] = {"parts": parts}

    gen_config = {}
    if req.get("max_tokens"):
        gen_config["maxOutputTokens"] = req["max_tokens"]
    if req.get("temperature") is not None:
        gen_config["temperature"] = req["temperature"]
    if gen_config:
        payload["generationConfig"] = gen_config

    return payload


def gemini_to_anthropic(resp, model="unknown"):
    candidate = resp["candidates"][0]
    text = "".join(p.get("text", "") for p in candidate["content"]["parts"])
    usage = resp.get("usageMetadata", {})
    return {
        "id": "msg_gemini",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": model,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": usage.get("promptTokenCount", 0),
            "output_tokens": usage.get("candidatesTokenCount", 0),
        },
    }
