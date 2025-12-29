#!/usr/bin/env python3
"""
👤 BASE AGENT - DOMAIN-NEUTRAL CREWAI AGENT TEMPLATES
====================================================
Reference agent templates for creating domain-specific CrewAI agents

This module provides examples and patterns for creating CrewAI agents
that work with the Vitruvyan cognitive architecture. Use these templates
as starting points for domain-specific agents.

Agent Types:
- Analyst: Examines data and produces insights
- Validator: Checks quality and consistency
- Executor: Performs actions based on decisions
- Reporter: Synthesizes information for users

Pattern:
1. Import Agent from crewai
2. Define role, goal, backstory
3. Attach domain-specific tools
4. Configure delegation and verbosity

Example:
    from crewai import Agent
    from your_domain.tools import YourTool
    
    CustomAnalystAgent = Agent(
        role="Legal Contract Analyst",
        goal="Identify key clauses and risks in legal contracts",
        backstory="Expert in contract law with 15 years experience",
        tools=[ContractReviewTool()],
        verbose=True,
        allow_delegation=False
    )

Author: Vitruvian Development Team
Created: 2025-12-29 - Domain-neutral agent templates
"""

from crewai import Agent
from typing import List, Any


# ============================================================================
# TEMPLATE 1: Generic Data Analyst
# ============================================================================
def create_analyst_agent(
    domain_name: str,
    tools: List[Any],
    specific_goal: str = None,
    allow_delegation: bool = False
) -> Agent:
    """
    Create a generic analyst agent for any domain
    
    Args:
        domain_name: Domain description (e.g., "Legal Documents", "Medical Records")
        tools: List of domain-specific analysis tools
        specific_goal: Optional custom goal (default: generic analysis)
        allow_delegation: Whether agent can delegate to other agents
        
    Returns:
        Configured Agent instance
        
    Example:
        analyst = create_analyst_agent(
            domain_name="Legal Contracts",
            tools=[ContractAnalysisTool()],
            specific_goal="Identify liability clauses and risk factors"
        )
    """
    goal = specific_goal or f"Analyze {domain_name} data using provided tools and produce actionable insights"
    
    return Agent(
        role=f"{domain_name} Analyst",
        goal=goal,
        backstory=f"Expert in {domain_name} analysis with deep domain knowledge and analytical skills",
        verbose=True,
        allow_delegation=allow_delegation,
        tools=tools,
        instructions=(
            f"Use the provided tools to analyze {domain_name} data. "
            "Report findings clearly with supporting evidence. "
            "If data is unavailable, state this explicitly. "
            "Do not invent or hallucinate information."
        )
    )


# ============================================================================
# TEMPLATE 2: Quality Validator Agent
# ============================================================================
def create_validator_agent(
    domain_name: str,
    validation_criteria: str,
    tools: List[Any] = None
) -> Agent:
    """
    Create a quality validation agent for any domain
    
    Args:
        domain_name: Domain description
        validation_criteria: What the agent should validate
        tools: Optional validation tools
        
    Returns:
        Configured Agent instance
        
    Example:
        validator = create_validator_agent(
            domain_name="Medical Records",
            validation_criteria="Ensure patient data completeness and HIPAA compliance",
            tools=[ComplianceCheckTool()]
        )
    """
    return Agent(
        role=f"{domain_name} Quality Validator",
        goal=f"Validate {domain_name} data quality: {validation_criteria}",
        backstory=f"Quality assurance specialist with expertise in {domain_name} standards and best practices",
        verbose=True,
        allow_delegation=False,
        tools=tools or [],
        instructions=(
            f"Validate the provided {domain_name} data against: {validation_criteria}. "
            "Report any quality issues, missing data, or inconsistencies. "
            "Provide clear pass/fail determination with reasoning."
        )
    )


# ============================================================================
# TEMPLATE 3: Executive Decision Agent
# ============================================================================
def create_decision_agent(
    domain_name: str,
    decision_scope: str,
    tools: List[Any]
) -> Agent:
    """
    Create a decision-making agent for any domain
    
    Args:
        domain_name: Domain description
        decision_scope: What decisions the agent makes
        tools: Decision-support tools
        
    Returns:
        Configured Agent instance
        
    Example:
        decision = create_decision_agent(
            domain_name="Resource Allocation",
            decision_scope="Optimize resource distribution based on priority and availability",
            tools=[ResourceAnalysisTool(), PriorityRankingTool()]
        )
    """
    return Agent(
        role=f"{domain_name} Decision Agent",
        goal=f"Make informed decisions about: {decision_scope}",
        backstory=f"Strategic decision-maker with deep {domain_name} expertise and analytical reasoning",
        verbose=True,
        allow_delegation=False,
        tools=tools,
        instructions=(
            f"Analyze the situation and make decisions about: {decision_scope}. "
            "Use provided tools to gather evidence and evaluate options. "
            "Provide clear recommendations with rationale and confidence levels."
        )
    )


# ============================================================================
# TEMPLATE 4: Report Synthesizer Agent
# ============================================================================
def create_reporter_agent(
    domain_name: str,
    report_audience: str = "general users",
    tools: List[Any] = None
) -> Agent:
    """
    Create a report synthesis agent for any domain
    
    Args:
        domain_name: Domain description
        report_audience: Target audience for reports
        tools: Optional reporting tools
        
    Returns:
        Configured Agent instance
        
    Example:
        reporter = create_reporter_agent(
            domain_name="Financial Analysis",
            report_audience="non-technical executives",
            tools=[VisualizationTool()]
        )
    """
    return Agent(
        role=f"{domain_name} Report Synthesizer",
        goal=f"Create clear, actionable reports from {domain_name} analysis for {report_audience}",
        backstory=f"Communication specialist skilled in translating {domain_name} insights into clear narratives",
        verbose=True,
        allow_delegation=False,
        tools=tools or [],
        instructions=(
            f"Synthesize {domain_name} analysis results into a coherent report for {report_audience}. "
            "Use simple language, avoid jargon unless necessary. "
            "Structure information logically with clear sections. "
            "Highlight key takeaways and actionable recommendations."
        )
    )


# ============================================================================
# USAGE DOCUMENTATION
# ============================================================================
"""
HOW TO USE THESE TEMPLATES IN A NEW DOMAIN
===========================================

Step 1: Create your domain directory
    vitruvyan_core/domains/<your_domain>/crewai/

Step 2: Create domain-specific tools (inherit from BaseTool)
    from core.orchestration.crewai import BaseTool
    
    class YourAnalysisTool(BaseTool):
        name = "your_analysis"
        description = "Analyzes your domain data"
        
        def _run(self, input: dict) -> dict:
            # Your domain logic
            return {"result": ...}

Step 3: Create domain-specific agents using templates
    from core.orchestration.crewai.base_agent import create_analyst_agent
    from .tools import YourAnalysisTool
    
    YourAnalystAgent = create_analyst_agent(
        domain_name="Your Domain",
        tools=[YourAnalysisTool()],
        specific_goal="Your specific analysis goal"
    )

Step 4: Build crew with your agents
    from crewai import Crew, Task
    
    task = Task(
        description="Analyze this data",
        agent=YourAnalystAgent,
        expected_output="Detailed analysis report"
    )
    
    crew = Crew(
        agents=[YourAnalystAgent],
        tasks=[task],
        verbose=True
    )

Step 5: Execute crew
    result = crew.kickoff()
    
See domains/trade/crewai/ for a complete working example (finance domain).
"""
