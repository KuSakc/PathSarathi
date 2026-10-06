"""Provider abstraction: local stub, Ollama, OpenAI-compatible BYOK."""
import httpx
from app.config import settings


def ollama_chat(prompt: str, model: str | None = None) -> str | None:
    try:
        r = httpx.post(f"{settings.OLLAMA_BASE_URL}/api/generate",
                       json={"model": model or settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                       timeout=60)
        if r.status_code == 200:
            return r.json().get("response", "")
        return None
    except Exception:
        return None


def openai_compat_chat(prompt: str, api_key: str, base_url: str = "https://api.openai.com/v1",
                       model: str = "gpt-4o-mini") -> str:
    r = httpx.post(f"{base_url}/chat/completions",
                   headers={"Authorization": f"Bearer {api_key}"},
                   json={"model": model, "messages": [{"role": "user", "content": prompt}]}, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def stub_chat(topic: str, depth: str, n_ctx: int) -> str:
    return (f"# {topic}\n\n**Depth:** {depth} (scored from syllabus weight + paper frequency)\n\n"
            f"## Reference definition\nStandardized definition of {topic} (stub — connect Ollama/BYOK for full text).\n\n"
            f"## Classroom explanation\nSimple explanation of {topic} with example. Grounded in {n_ctx} retrieved chunk(s).\n\n"
            f"## Key points\n- point 1\n- point 2\n\n## Practice\n- Past-paper style Q1 on {topic}\n")
