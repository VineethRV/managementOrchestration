import os
import time
from groq import Groq
from typing import Dict, Any, List, Tuple


class ModelAgent:
    def __init__(self, model_name: str = "llama-3.1-8b-instant", api_key_env: str = "GROQ_API_KEY"):
        api_key =os.getenv(api_key_env) 
        if not api_key:
            raise EnvironmentError(f"Environment variable {api_key_env} not set.")
        self.client = Groq(api_key=api_key)
        self.model_name = model_name

        # Token metrics tracking
        self.metrics = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "call_count": 0,
            "conversations": [],
            "code_generation_tokens": 0,
        }

        # sliding window of (timestamp, tokens) for simple short-term accounting
        self._token_window: List[Tuple[float, int]] = []
        self.last_call_usage: Dict[str, Any] = None

    def run(self, prompt: str,category: str, temperature: float = 0.1, max_tokens: int = 1024) -> str:
        messages = [{"role": "user", "content": prompt}]
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract token usage and response
        response_content = completion.choices[0].message.content
        # Safely extract usage fields
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        try:
            if hasattr(completion, 'usage') and completion.usage is not None:
                usage = completion.usage
                prompt_tokens = int(getattr(usage, 'prompt_tokens', 0) or usage.get('prompt_tokens', 0))
                completion_tokens = int(getattr(usage, 'completion_tokens', 0) or usage.get('completion_tokens', 0))
                total_tokens = int(getattr(usage, 'total_tokens', 0) or usage.get('total_tokens', 0) or (prompt_tokens + completion_tokens))
            elif isinstance(completion, dict) and 'usage' in completion:
                usage = completion['usage']
                prompt_tokens = int(usage.get('prompt_tokens', 0))
                completion_tokens = int(usage.get('completion_tokens', 0))
                total_tokens = int(usage.get('total_tokens', prompt_tokens + completion_tokens))
        except Exception:
            # fallback: estimate from lengths
            total_tokens = max(1, int((len(prompt) + len(response_content)) / 4))

        # Update internal metrics
        try:
            self._update_metrics(prompt, response_content, prompt_tokens, completion_tokens, total_tokens,category=category)
        except Exception:
            pass

        # store last call usage for external collectors
        self.last_call_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "is_code_generation": ("===" in response_content or "def " in response_content or "class " in response_content),
        }

        # short-term accounting
        now = time.time()
        try:
            self._token_window.append((now, total_tokens))
            self._cleanup_token_window()
        except Exception:
            pass

        return response_content

    def _update_metrics(self, prompt: str, response: str, prompt_tokens: int, completion_tokens: int, total_tokens: int, category:str):
        """Update token metrics for each API call"""
        self.metrics["total_prompt_tokens"] += prompt_tokens
        self.metrics["total_completion_tokens"] += completion_tokens
        self.metrics["total_tokens"] += total_tokens
        self.metrics["call_count"] += 1

        # Heuristic: treat responses that contain code markers as code-generation
        is_code_gen = category == 'coding'
        if is_code_gen:
            self.metrics["code_generation_tokens"] += completion_tokens

        self.metrics["conversations"].append({
            "call_num": self.metrics["call_count"],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "is_code_generation": is_code_gen,
        })
        self.print_metrics()

    def get_metrics(self) -> Dict[str, Any]:
        """Return a shallow copy of current token metrics"""
        return dict(self.metrics)

    def get_last_call_usage(self) -> Dict[str, Any]:
        """Return usage info for the most recent API call, or None if unset."""
        return self.last_call_usage

    def _cleanup_token_window(self):
        """Remove entries older than 60 seconds from the token window."""
        try:
            now = time.time()
            cutoff = now - 60
            self._token_window = [(ts, t) for ts, t in self._token_window if ts >= cutoff]
        except Exception:
            # keep best-effort; nothing to do on failure
            pass

    def print_metrics(self):
        """Print formatted token metrics to stdout."""
        print("\n" + "=" * 60)
        print("TOKEN USAGE METRICS")
        print("=" * 60)
        print(f"Total API Calls: {self.metrics['call_count']}")
        print(f"Total Input Tokens: {self.metrics['total_prompt_tokens']}")
        print(f"Total Output Tokens: {self.metrics['total_completion_tokens']}")
        print(f"Total Tokens: {self.metrics['total_tokens']}")
        print(f"Code-generation Tokens: {self.metrics['code_generation_tokens']}")
        print("Recent conversation entries:")
        for c in self.metrics["conversations"][-5:]:
            print(f" - call {c['call_num']}: input={c['prompt_tokens']} output={c['completion_tokens']} total={c['total_tokens']} code={c['is_code_generation']}")
