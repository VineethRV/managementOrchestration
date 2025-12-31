class GlobalCoordinator:
    def __init__(self, model):
        self.model = model

    def integrate(self, role_outputs: dict) -> dict:
        prompt = f"""You are a global integrator. Given role outputs (separated by file markers), produce a JSON mapping of file paths to file contents, ensuring imports and paths are consistent.

Role outputs:
{role_outputs}

Return valid JSON only. and dont add any comments like Sure hers the json, only json nothing else. also see that frontend is calling backend with correct endpoitns else change.
        """
        out = self.model.run(prompt, temperature=0.0, max_tokens=8000, category='coding')
        try:
            import json
            parsed = json.loads(out)
            return parsed
        except Exception:
            return {'_raw': out}
