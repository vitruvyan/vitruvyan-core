#!/usr/bin/env python3
"""
🛠️ BASE TOOL - DOMAIN-NEUTRAL CREWAI TOOL INTERFACE
===================================================
Abstract base class for all CrewAI tools in Vitruvyan Core

This module provides the foundational interface that all domain-specific
tools must implement. It ensures consistent tool behavior across domains.

Pattern:
1. Inherit from BaseTool
2. Define name and description
3. Implement _run() method with domain logic
4. Tool automatically gets run() and __call__() methods

Example:
    class DocumentAnalysisTool(BaseTool):
        name: str = "document_analyzer"
        description: str = "Analyzes legal documents for key clauses"
        
        def _run(self, input: Dict[str, Any]) -> Dict[str, Any]:
            doc_path = input.get("document_path")
            # Analysis logic here
            return {"clauses": [...], "risk_level": "low"}

Author: Vitruvian Development Team
Created: 2025-12-29 - Migrated from domains/trade/crewai/base_tool.py
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    Abstract base class for CrewAI tools
    
    All tools must define:
    - name: Tool identifier (snake_case)
    - description: Human-readable purpose
    - _run(): Core execution logic
    
    Provides:
    - run(): Public execution method
    - __call__(): Makes tool instance callable
    """
    
    name: str
    description: str

    @abstractmethod
    def _run(self, input: Dict[str, Any]) -> Any:
        """
        Core tool execution logic - must be implemented by subclasses
        
        Args:
            input: Dictionary containing tool parameters
            
        Returns:
            Tool execution result (typically dict or string)
        """
        pass

    def run(self, input: Dict[str, Any]) -> Any:
        """
        Public interface for tool execution
        
        Args:
            input: Dictionary containing tool parameters
            
        Returns:
            Result from _run() implementation
        """
        return self._run(input)

    def __call__(self, input: Dict[str, Any]) -> Any:
        """
        Makes tool instance callable
        
        Args:
            input: Dictionary containing tool parameters
            
        Returns:
            Result from _run() implementation
        """
        return self._run(input)
