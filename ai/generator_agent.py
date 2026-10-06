"""Generator AI: Ollama primary, stub fallback; BYOK external for private User-mode."""
from ai.providers.backends import ollama_chat, openai_compat_chat, stub_chat


def generate_doc(topic: str, depth: str, context_chunks: list[str], template: str,
                 api_key: str | None = None, api_provider: str | None = None) -> str:
    ctx = "\n---\n".join(context_chunks[:5]) or "(no retrieved context)"
    prompt = template.replace("{topic}", topic).replace("{depth}", depth).replace("{context}", ctx)
    # External private path (student BYOK)
    if api_key:
        try:
            return openai_compat_chat(prompt, api_key)
        except Exception as e:
            return stub_chat(topic, depth, len(context_chunks)) + f"\n> external provider failed: {e}\n"
    # Local default: Ollama
    out = ollama_chat(prompt)
    if out:
        return out
    return stub_chat(topic, depth, len(context_chunks))
