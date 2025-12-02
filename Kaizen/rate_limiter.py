"""
Rate Limiter: Prevents API key limit exhaustion by managing request rates.
Implements token bucket algorithm for rate limiting.
"""

import time
from datetime import datetime, timedelta
from typing import Optional
from collections import deque


class RateLimiter:
    """
    Token bucket rate limiter to prevent hitting API key limits.
    Tracks requests per minute and per hour.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 30,
        requests_per_hour: int = 1000,
        tokens_per_minute: int = 100000,  # Token budget per minute
        tokens_per_day: int = 100000  # Daily token limit (Groq on-demand tier)
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_hour: Maximum requests per hour
            tokens_per_minute: Token budget per minute (for Groq API)
            tokens_per_day: Daily token limit (default 100k for Groq on-demand)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.tokens_per_minute = tokens_per_minute
        self.tokens_per_day = tokens_per_day
        
        # Track request timestamps
        self.request_times: deque = deque()
        self.hourly_request_times: deque = deque()
        
        # Track token usage (minute, hour, day)
        self.token_usage: deque = deque()  # (timestamp, tokens)
        self.daily_token_usage: deque = deque()  # (timestamp, tokens) for daily tracking
        self.total_tokens_used = 0
        
        # Statistics
        self.total_requests = 0
        self.delayed_requests = 0
        self.rate_limit_errors = 0
    
    def _clean_old_requests(self):
        """Remove requests older than 1 hour and tokens older than 24 hours."""
        now = time.time()
        one_hour_ago = now - 3600
        one_minute_ago = now - 60
        one_day_ago = now - 86400  # 24 hours
        
        # Clean minute window
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()
        
        # Clean hour window
        while self.hourly_request_times and self.hourly_request_times[0] < one_hour_ago:
            self.hourly_request_times.popleft()
        
        # Clean token usage older than 1 minute
        while self.token_usage and self.token_usage[0][0] < one_minute_ago:
            self.token_usage.popleft()
        
        # Clean daily token usage older than 24 hours
        while self.daily_token_usage and self.daily_token_usage[0][0] < one_day_ago:
            self.daily_token_usage.popleft()
    
    def _calculate_wait_time(self) -> float:
        """
        Calculate how long to wait before next request.
        
        Returns:
            Wait time in seconds
        """
        self._clean_old_requests()
        
        now = time.time()
        wait_time = 0.0
        
        # Check per-minute limit
        if len(self.request_times) >= self.requests_per_minute:
            oldest_in_minute = self.request_times[0]
            wait_time = max(wait_time, 60 - (now - oldest_in_minute) + 0.1)
        
        # Check per-hour limit
        if len(self.hourly_request_times) >= self.requests_per_hour:
            oldest_in_hour = self.hourly_request_times[0]
            wait_time = max(wait_time, 3600 - (now - oldest_in_hour) + 0.1)
        
        # Check daily token limit (most important for Groq)
        current_daily_tokens = sum(tokens for _, tokens in self.daily_token_usage)
        if current_daily_tokens >= self.tokens_per_day * 0.95:  # Stop at 95% to be safe
            # Calculate wait until oldest daily token expires
            if self.daily_token_usage:
                oldest_daily_token_time = self.daily_token_usage[0][0]
                wait_until_reset = 86400 - (now - oldest_daily_token_time)
                wait_time = max(wait_time, wait_until_reset + 0.1)
        
        # Check per-minute token budget (secondary check)
        current_minute_tokens = sum(tokens for _, tokens in self.token_usage)
        if current_minute_tokens >= self.tokens_per_minute:
            # Wait until oldest token usage expires
            if self.token_usage:
                oldest_token_time = self.token_usage[0][0]
                wait_time = max(wait_time, 60 - (now - oldest_token_time) + 0.1)
        
        return wait_time
    
    def wait_if_needed(self) -> float:
        """
        Wait if rate limit would be exceeded.
        
        Returns:
            Actual wait time in seconds
        """
        wait_time = self._calculate_wait_time()
        
        if wait_time > 0:
            self.delayed_requests += 1
            time.sleep(wait_time)
            return wait_time
        
        return 0.0
    
    def record_request(self, tokens_used: int = 0):
        """
        Record a completed request.
        
        Args:
            tokens_used: Number of tokens used in this request
        """
        now = time.time()
        self.request_times.append(now)
        self.hourly_request_times.append(now)
        self.total_requests += 1
        
        if tokens_used > 0:
            self.token_usage.append((now, tokens_used))
            self.daily_token_usage.append((now, tokens_used))
            self.total_tokens_used += tokens_used
    
    def can_make_request(self, estimated_tokens: int = 0) -> bool:
        """
        Check if a request can be made without waiting.
        
        Args:
            estimated_tokens: Estimated tokens for this request
        
        Returns:
            True if request can be made immediately
        """
        self._clean_old_requests()
        
        if len(self.request_times) >= self.requests_per_minute:
            return False
        
        if len(self.hourly_request_times) >= self.requests_per_hour:
            return False
        
        # Check daily token limit (most critical)
        current_daily_tokens = sum(tokens for _, tokens in self.daily_token_usage)
        if current_daily_tokens + estimated_tokens >= self.tokens_per_day * 0.95:  # 95% safety margin
            return False
        
        # Check per-minute token budget
        current_minute_tokens = sum(tokens for _, tokens in self.token_usage)
        if current_minute_tokens + estimated_tokens >= self.tokens_per_minute:
            return False
        
        return True
    
    def get_daily_token_usage(self) -> int:
        """Get current daily token usage."""
        self._clean_old_requests()
        return sum(tokens for _, tokens in self.daily_token_usage)
    
    def get_remaining_daily_tokens(self) -> int:
        """Get remaining daily token budget."""
        return max(0, self.tokens_per_day - self.get_daily_token_usage())
    
    def get_statistics(self) -> dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        self._clean_old_requests()
        
        daily_tokens = self.get_daily_token_usage()
        remaining_daily = self.get_remaining_daily_tokens()
        
        return {
            'total_requests': self.total_requests,
            'delayed_requests': self.delayed_requests,
            'rate_limit_errors': self.rate_limit_errors,
            'requests_in_last_minute': len(self.request_times),
            'requests_in_last_hour': len(self.hourly_request_times),
            'total_tokens_used': self.total_tokens_used,
            'tokens_in_last_minute': sum(tokens for _, tokens in self.token_usage),
            'tokens_per_day_limit': self.tokens_per_day,
            'daily_tokens_used': daily_tokens,
            'remaining_daily_tokens': remaining_daily,
            'daily_token_percentage': (daily_tokens / self.tokens_per_day * 100) if self.tokens_per_day > 0 else 0,
            'can_make_request': self.can_make_request()
        }
    
    def record_rate_limit_error(self):
        """Record a rate limit error."""
        self.rate_limit_errors += 1
    
    def reset(self):
        """Reset all counters (use with caution)."""
        self.request_times.clear()
        self.hourly_request_times.clear()
        self.token_usage.clear()
        self.daily_token_usage.clear()
        self.total_requests = 0
        self.delayed_requests = 0
        self.rate_limit_errors = 0
        self.total_tokens_used = 0

