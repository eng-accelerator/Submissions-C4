"""
Remediation Agent
Maps detected issues to root causes and recommended fixes using RAG-style reasoning.
"""

from orchestrator.state import IncidentAnalysisState, RemediationPlan
from utils.llm_client import LLMClient


class RemediationAgent:
    """
    Agent responsible for generating remediation plans.
    Uses RAG-style reasoning to map incidents to solutions.
    """
    
    SYSTEM_PROMPT = """You are an expert DevOps Site Reliability Engineer (SRE) with deep knowledge of:
- System architecture and distributed systems
- Common failure patterns and their root causes
- Best practices for incident remediation
- Production system recovery procedures

Your task is to analyze incidents and provide actionable remediation plans.

For each incident, you must:
1. Hypothesize the root cause based on technical evidence
2. Provide specific, actionable remediation steps (not generic advice)
3. Explain the technical rationale behind your recommendations
4. Estimate the impact of the remediation
5. Assess urgency (LOW, MEDIUM, HIGH, CRITICAL)

Be specific and technical. Avoid vague suggestions like "check the logs" - instead provide concrete commands, configurations, or actions."""
    
    # Knowledge base of common incident patterns (RAG-style)
    INCIDENT_PATTERNS = {
        "DatabaseConnectionTimeout": {
            "common_causes": [
                "Connection pool exhaustion",
                "Database server overload",
                "Network latency or firewall issues",
                "Max connections limit reached"
            ],
            "typical_fixes": [
                "Scale up database connection pool size",
                "Verify database server health and resource utilization",
                "Check network connectivity and latency",
                "Investigate long-running queries blocking connections"
            ]
        },
        "APITimeout": {
            "common_causes": [
                "Downstream service slowness",
                "Network congestion",
                "Insufficient timeout configuration",
                "Resource exhaustion on API server"
            ],
            "typical_fixes": [
                "Implement circuit breaker pattern",
                "Increase timeout thresholds if appropriate",
                "Add request retries with exponential backoff",
                "Scale API servers horizontally"
            ]
        },
        "MemoryLeak": {
            "common_causes": [
                "Unclosed resources (connections, file handles)",
                "Growing cache without eviction",
                "Event listener leaks",
                "Circular references preventing garbage collection"
            ],
            "typical_fixes": [
                "Restart affected service immediately",
                "Enable heap dump analysis",
                "Review recent code changes for resource management",
                "Implement memory profiling in staging"
            ]
        },
        "DiskSpaceFull": {
            "common_causes": [
                "Log file accumulation",
                "Temporary file buildup",
                "Database growth without rotation",
                "Misconfigured retention policies"
            ],
            "typical_fixes": [
                "Clear old log files: find /var/log -mtime +30 -delete",
                "Expand disk volume or add storage",
                "Implement log rotation policies",
                "Archive and purge old data"
            ]
        }
    }
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize Remediation Agent
        
        Args:
            llm_client: LLM client for analysis
        """
        self.llm = llm_client
    
    def get_pattern_context(self, incident_type: str) -> str:
        """
        Retrieve relevant context from knowledge base (RAG-style)
        
        Args:
            incident_type: Type of incident
            
        Returns:
            Context string with relevant patterns
        """
        # Find matching or similar patterns
        context_parts = []
        
        for pattern_name, pattern_info in self.INCIDENT_PATTERNS.items():
            if pattern_name.lower() in incident_type.lower() or incident_type.lower() in pattern_name.lower():
                context_parts.append(f"""
Pattern: {pattern_name}
Common Causes:
{chr(10).join(f"- {cause}" for cause in pattern_info['common_causes'])}

Typical Fixes:
{chr(10).join(f"- {fix}" for fix in pattern_info['typical_fixes'])}
""")
        
        if context_parts:
            return "RELEVANT KNOWLEDGE BASE PATTERNS:\n" + "\n".join(context_parts)
        else:
            return "No exact pattern match in knowledge base. Use general SRE principles."
    
    def generate_remediation_plan(self, state: IncidentAnalysisState) -> RemediationPlan:
        """
        Generate remediation plan using LLM with RAG context
        
        Args:
            state: Current state with classified incident
            
        Returns:
            Remediation plan
        """
        incident = state.classified_incident
        
        # Get relevant context from knowledge base
        pattern_context = self.get_pattern_context(incident.incident_type)
        
        user_prompt = f"""Analyze this incident and create a detailed remediation plan:

INCIDENT CLASSIFICATION:
- Type: {incident.incident_type}
- Severity: {incident.severity}
- Affected Service: {incident.affected_service}
- Summary: {incident.summary}
- Technical Details: {incident.technical_details}

RAW LOG:
{incident.log_entry.raw_log}

{pattern_context}

Based on the above information and your SRE expertise, provide:
1. Root cause hypothesis (specific technical explanation)
2. Recommended fixes (concrete, actionable steps with commands/configs where applicable)
3. Technical rationale (why these fixes address the root cause)
4. Estimated impact (what will improve after remediation)
5. Urgency assessment (LOW, MEDIUM, HIGH, CRITICAL)

Be specific and actionable. Include actual commands, configuration changes, or code fixes when possible."""
        
        remediation_plan = self.llm.invoke_with_structured_output(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=RemediationPlan
        )
        
        return remediation_plan
    
    def process(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """
        Main processing method for the agent
        
        Args:
            state: Current incident analysis state
            
        Returns:
            Updated state with remediation plan
        """
        try:
            if not state.classified_incident:
                raise ValueError("No classified incident available")
            
            # Generate remediation plan
            remediation_plan = self.generate_remediation_plan(state)
            
            # Update state
            state.remediation_plan = remediation_plan
            
        except Exception as e:
            state.errors.append(f"Remediation Agent Error: {str(e)}")
        
        return state
