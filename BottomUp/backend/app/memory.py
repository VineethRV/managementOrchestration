class Memory:
    def __init__(self):
        self.own_history = []
        self.shared_suggestions = []

    def add_own(self, entry: str):
        self.own_history.append(entry)

    def add_shared(self, entry: str):
        self.shared_suggestions.append(entry)

    def get_context(self) -> str:
        parts = []
        if self.own_history:
            parts.append("Own History:")
            parts.extend(self.own_history[-2:])
        if self.shared_suggestions:
            parts.append("\nShared Suggestions:")
            parts.extend(self.shared_suggestions[-2:])
        return "\n".join(parts)
