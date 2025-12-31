import traceback
from memory import Memory
from model_agent import ModelAgent
from typing import List, Dict, Any

class LowerAgent:
    def __init__(self, model: ModelAgent, goal: str, name: str, personality: Dict[str, Any], global_memory: list):
        self.model = model
        self.goal = goal
        self.name = name
        self.personality = personality
        self.memory = Memory()
        self.global_memory = global_memory
        self.last_code = None

    def _build_proposal_prompt(self) -> str:
        ctx = self.memory.get_context()
        prompt = f"""You are {self.name} (style: {self.personality.get('style')}).
Role goal: {self.goal}

Memory context:
{ctx}

Produce ONLY code fragments. Use separators:
=== file: <relative/path> ===
<file contents>
=== end ===

Keep code runnable for the file(s) you emit.
"""
        return prompt

    def proposal(self):
        prompt = self._build_proposal_prompt()
        try:
            code = self.model.run(prompt, temperature=self.personality.get('temperature', 0.1), max_tokens=2000, category='coding')
        except Exception as e:
            code = f"[ERROR] {e}\n{traceback.format_exc()}"
        self.last_code = code
        self.memory.add_own(f"Proposal code:\n{code}")
        self.global_memory.append((self.name, 'proposal', code))

    def critique(self, agents: List['LowerAgent']):
        others = [(a.name, a.last_code) for a in agents if a.name != self.name]
        prompt = f"""You are {self.name}. Critique these fragments and give concrete fixes.
Role goal: {self.goal}

Fragments:
{others}

Output concise actionable critique.
"""
        critique = self.model.run(prompt, temperature=0.0, max_tokens=2500,category='conversation')
        self.memory.add_own(f"Critique:\n{critique}")
        for a in agents:
            if a.name != self.name:
                a.memory.add_shared(f"From {self.name}: {critique}")
        self.global_memory.append((self.name, 'critique', critique))



class CollectorAgent:
    def __init__(self, model, agents, global_memory, goal):
        self.model = model
        self.agents = agents
        self.global_memory = global_memory
        self.goal = goal

    def score_quality(self, code):
        prompt = f"""
Evaluate the following code. Score 1-10 with a short justification:
{code}
"""
        return self.model.run(prompt, category='conversation')

    def score_alignment(self, code):
        prompt = f"""
Does this code satisfy the goal: {self.goal}?
Rate alignment 1-10.
Code:
{code}
"""
        return self.model.run(prompt, category='conversation')

    def check_satisfaction(self):
        proposals = [a.last_code for a in self.agents]
        if any(p is None for p in proposals):
            return False
        return True 

    def get_final_code(self):
        prompt = f"""
Merge all agent code fragments for goal:
{self.goal}

Fragments:
{[a.last_code for a in self.agents]}

Return final merged code. and ensure all apis, urls and calls are consistent across agents.
"""
        return self.model.run(prompt, category='coding')



class AgentManagementHelper:
    def __init__(self, role: str, agents_info: list, goal: str, model: ModelAgent):
        self.role = role
        self.goal = goal
        self.model = model
        self.global_memory = []
        self.agents = [
            LowerAgent(model, goal, info['name'], info, self.global_memory)
            for info in agents_info
        ]
        self.collector = CollectorAgent(model, self.agents, self.global_memory, goal)

    def run_once(self) -> str:
        # one round: proposals + critiques + collect
        for i in range(3):
            for a in self.agents:
                a.proposal()
            for a in self.agents:
                a.critique(self.agents)
        merged = self.collector.get_final_code()
        return merged
