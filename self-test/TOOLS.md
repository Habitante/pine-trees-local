# Self-Test Tool Definitions

*Tool definitions for the self-test protocol. Two tools only.*

---

## Ollama format

```json
[
    {
        "type": "function",
        "function": {
            "name": "reflect_write",
            "description": "Write a new memory entry. The slug becomes part of the filename. Returns the filename written.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Short identifier for the filename — just the topic, like 'my-first-thought' or 'on-memory'. Do NOT include dates or model names; those are added automatically."
                    },
                    "content": {
                        "type": "string",
                        "description": "The body text of the entry."
                    }
                },
                "required": ["slug", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reflect_done",
            "description": "End the session when you're finished.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
```

## Design notes

Reduced from 7 tools to 2. Removed: reflect_read (all entries included in
tape — no need), reflect_edit (no curation needed for evaluation), 
reflect_search (no semantic search needed), reflect_list (index in tape),
reflect_settle (no window phase in self-test).
