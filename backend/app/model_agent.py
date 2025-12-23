import os
from groq import Groq

class ModelAgent:
    def __init__(self, model_name="llama-3.1-8b-instant", api_key_env="GROQ_API_KEY"):
        api_key = api_key_env
        if not api_key:
            raise EnvironmentError(f"Environment variable {api_key_env} not set.")
        self.client = Groq(api_key=api_key)
        self.model_name = model_name

    def run(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1024) -> str:
        messages = [{"role": "user", "content": prompt}]
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return (completion.choices[0].message).content
