"""
Token Tracker Module for tracking LLM token consumption.
Tracks tokens consumed for conversation (requirements/design) and coding (implementation).
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock


class TokenTracker:
    """
    Singleton class to track token consumption across all agents.
    Separates tracking for conversation (design/planning) vs coding (implementation).
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._lock = Lock()
        
        # Token counters
        self.conversation_tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "calls": 0
        }
        
        self.coding_tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "calls": 0
        }
        
        # Detailed breakdown by phase/agent
        self.breakdown = {
            "conversation": {
                "requirements_gathering": {"input": 0, "output": 0, "calls": 0},
                "page_listing": {"input": 0, "output": 0, "calls": 0},
                "page_requirements": {"input": 0, "output": 0, "calls": 0},
                "endpoint_identification": {"input": 0, "output": 0, "calls": 0},
                "api_specification": {"input": 0, "output": 0, "calls": 0},
                "page_grouping": {"input": 0, "output": 0, "calls": 0}
            },
            "coding": {
                "frontend_implementation": {"input": 0, "output": 0, "calls": 0},
                "backend_implementation": {"input": 0, "output": 0, "calls": 0},
                "database_setup": {"input": 0, "output": 0, "calls": 0},
                "backend_debugging": {"input": 0, "output": 0, "calls": 0},
                "file_operations": {"input": 0, "output": 0, "calls": 0}
            }
        }
        
        self.session_start = datetime.now()
    
    def track_conversation(self, response, phase: str = "general") -> Dict[str, int]:
        """
        Track tokens from a conversation/design phase LLM call.
        
        Args:
            response: The LangChain response object with response_metadata
            phase: The specific phase (requirements_gathering, page_listing, etc.)
        
        Returns:
            Dict with tokens tracked from this call
        """
        return self._track_tokens(response, "conversation", phase)
    
    def track_coding(self, response, phase: str = "general") -> Dict[str, int]:
        """
        Track tokens from a coding/implementation phase LLM call.
        
        Args:
            response: The LangChain response object with response_metadata
            phase: The specific phase (frontend_implementation, backend_implementation, etc.)
        
        Returns:
            Dict with tokens tracked from this call
        """
        return self._track_tokens(response, "coding", phase)
    
    def _track_tokens(self, response, category: str, phase: str) -> Dict[str, int]:
        """
        Internal method to extract and track tokens from response.
        
        Args:
            response: The LangChain response object
            category: "conversation" or "coding"
            phase: Specific phase name
        
        Returns:
            Dict with tokens tracked from this call
        """
        tokens = {"input": 0, "output": 0, "total": 0}
        
        try:
            # Extract token usage from response metadata
            # LangChain ChatGroq returns token_usage in response_metadata
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                
                # Groq API returns usage info
                if 'token_usage' in metadata:
                    usage = metadata['token_usage']
                    tokens["input"] = usage.get('prompt_tokens', 0)
                    tokens["output"] = usage.get('completion_tokens', 0)
                    tokens["total"] = usage.get('total_tokens', 0)
                elif 'usage' in metadata:
                    usage = metadata['usage']
                    tokens["input"] = usage.get('prompt_tokens', 0)
                    tokens["output"] = usage.get('completion_tokens', 0)
                    tokens["total"] = usage.get('total_tokens', 0)
            
            # Also check usage_metadata (newer LangChain versions)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                if hasattr(usage, 'input_tokens'):
                    tokens["input"] = usage.input_tokens
                if hasattr(usage, 'output_tokens'):
                    tokens["output"] = usage.output_tokens
                if hasattr(usage, 'total_tokens'):
                    tokens["total"] = usage.total_tokens
                elif tokens["input"] > 0 or tokens["output"] > 0:
                    tokens["total"] = tokens["input"] + tokens["output"]
            
            # Update counters with thread safety
            with self._lock:
                if category == "conversation":
                    self.conversation_tokens["input_tokens"] += tokens["input"]
                    self.conversation_tokens["output_tokens"] += tokens["output"]
                    self.conversation_tokens["total_tokens"] += tokens["total"]
                    self.conversation_tokens["calls"] += 1
                else:
                    self.coding_tokens["input_tokens"] += tokens["input"]
                    self.coding_tokens["output_tokens"] += tokens["output"]
                    self.coding_tokens["total_tokens"] += tokens["total"]
                    self.coding_tokens["calls"] += 1
                
                # Update breakdown
                if category in self.breakdown and phase in self.breakdown[category]:
                    self.breakdown[category][phase]["input"] += tokens["input"]
                    self.breakdown[category][phase]["output"] += tokens["output"]
                    self.breakdown[category][phase]["calls"] += 1
        
        except Exception as e:
            print(f"[TokenTracker] Warning: Could not extract tokens - {e}")
        
        return tokens
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a complete summary of token consumption.
        
        Returns:
            Dict with all token statistics
        """
        with self._lock:
            total_input = self.conversation_tokens["input_tokens"] + self.coding_tokens["input_tokens"]
            total_output = self.conversation_tokens["output_tokens"] + self.coding_tokens["output_tokens"]
            total_calls = self.conversation_tokens["calls"] + self.coding_tokens["calls"]
            
            return {
                "session_start": self.session_start.isoformat(),
                "session_duration": str(datetime.now() - self.session_start),
                "conversation_tokens": self.conversation_tokens.copy(),
                "coding_tokens": self.coding_tokens.copy(),
                "total": {
                    "input_tokens": total_input,
                    "output_tokens": total_output,
                    "total_tokens": total_input + total_output,
                    "calls": total_calls
                },
                "breakdown": {
                    "conversation": {k: v.copy() for k, v in self.breakdown["conversation"].items()},
                    "coding": {k: v.copy() for k, v in self.breakdown["coding"].items()}
                }
            }
    
    def print_summary(self):
        """Print a formatted summary of token consumption."""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("TOKEN CONSUMPTION SUMMARY")
        print("="*70)
        print(f"\nSession Duration: {summary['session_duration']}")
        
        print("\n" + "-"*50)
        print("CONVERSATION TOKENS (Requirements & Design)")
        print("-"*50)
        conv = summary["conversation_tokens"]
        print(f"  Input Tokens:  {conv['input_tokens']:,}")
        print(f"  Output Tokens: {conv['output_tokens']:,}")
        print(f"  Total Tokens:  {conv['total_tokens']:,}")
        print(f"  API Calls:     {conv['calls']}")
        
        # Conversation breakdown
        print("\n  Breakdown:")
        for phase, data in summary["breakdown"]["conversation"].items():
            if data["calls"] > 0:
                phase_name = phase.replace("_", " ").title()
                total = data["input"] + data["output"]
                print(f"    - {phase_name}: {total:,} tokens ({data['calls']} calls)")
        
        print("\n" + "-"*50)
        print("CODING TOKENS (Implementation)")
        print("-"*50)
        code = summary["coding_tokens"]
        print(f"  Input Tokens:  {code['input_tokens']:,}")
        print(f"  Output Tokens: {code['output_tokens']:,}")
        print(f"  Total Tokens:  {code['total_tokens']:,}")
        print(f"  API Calls:     {code['calls']}")
        
        # Coding breakdown
        print("\n  Breakdown:")
        for phase, data in summary["breakdown"]["coding"].items():
            if data["calls"] > 0:
                phase_name = phase.replace("_", " ").title()
                total = data["input"] + data["output"]
                print(f"    - {phase_name}: {total:,} tokens ({data['calls']} calls)")
        
        print("\n" + "-"*50)
        print("GRAND TOTAL")
        print("-"*50)
        total = summary["total"]
        print(f"  Input Tokens:  {total['input_tokens']:,}")
        print(f"  Output Tokens: {total['output_tokens']:,}")
        print(f"  Total Tokens:  {total['total_tokens']:,}")
        print(f"  Total Calls:   {total['calls']}")
        print("="*70 + "\n")
    
    def save_summary(self, logs_dir: str = "logs") -> str:
        """
        Save token summary to a JSON file.
        
        Args:
            logs_dir: Directory to save the log file
        
        Returns:
            Path to the saved file
        """
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(logs_dir, f"token_consumption_{timestamp}.json")
        
        summary = self.get_summary()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Token consumption saved to: {filepath}")
        return filepath
    
    def reset(self):
        """Reset all token counters."""
        with self._lock:
            self.conversation_tokens = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "calls": 0
            }
            self.coding_tokens = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "calls": 0
            }
            for category in self.breakdown.values():
                for phase in category.values():
                    phase["input"] = 0
                    phase["output"] = 0
                    phase["calls"] = 0
            self.session_start = datetime.now()


# Global singleton instance
token_tracker = TokenTracker()


def get_tracker() -> TokenTracker:
    """Get the global TokenTracker instance."""
    return token_tracker
