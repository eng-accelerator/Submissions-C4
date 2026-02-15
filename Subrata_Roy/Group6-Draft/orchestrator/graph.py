"""
LangGraph Orchestrator
Coordinates the multi-agent workflow using LangGraph state machine.
"""

from langgraph.graph import StateGraph, END
from orchestrator.state import IncidentAnalysisState
from agents.log_classifier import LogClassifierAgent
from agents.remediation import RemediationAgent
from agents.cookbook import CookbookAgent
from agents.notification import NotificationAgent
from agents.jira_ticket import JIRATicketAgent
from utils.llm_client import LLMClient
from typing import Literal


class IncidentAnalysisOrchestrator:
    """
    Orchestrates the multi-agent incident analysis workflow.
    
    Flow:
    1. Log Classifier → Parse and classify incident
    2. Remediation Agent → Generate remediation plan
    3. Conditional: If CRITICAL → JIRA Agent
    4. Cookbook Agent → Create runbook checklist
    5. Notification Agent → Send Slack notification
    """
    
    def __init__(self, state: IncidentAnalysisState):
        """
        Initialize orchestrator with configuration
        
        Args:
            state: Initial state with configuration
        """
        self.initial_state = state
        
        # Initialize LLM client
        self.llm_client = LLMClient(
            api_key=state.openrouter_api_key,
            model=state.llm_model
        )
        
        # Initialize agents
        self.log_classifier = LogClassifierAgent(self.llm_client)
        self.remediation_agent = RemediationAgent(self.llm_client)
        self.cookbook_agent = CookbookAgent(self.llm_client)
        
        # Initialize API-based agents if credentials provided
        self.notification_agent = None
        if state.slack_webhook_url:
            self.notification_agent = NotificationAgent(state.slack_webhook_url)
        
        self.jira_agent = None
        if state.jira_url and state.jira_username and state.jira_api_token:
            project_key = (state.jira_project_key or "OPS").strip()
            issue_type = (state.jira_issue_type or "Task").strip()
            self.jira_agent = JIRATicketAgent(
                jira_url=state.jira_url,
                username=state.jira_username,
                api_token=state.jira_api_token,
                project_key=project_key,
                issue_type=issue_type
            )
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine
        
        Returns:
            Compiled state graph
        """
        # Create graph
        workflow = StateGraph(IncidentAnalysisState)
        
        # Add nodes (agents)
        workflow.add_node("classify_log", self._classify_log_node)
        workflow.add_node("generate_remediation", self._remediation_node)
        workflow.add_node("create_jira_ticket", self._jira_node)
        workflow.add_node("create_cookbook", self._cookbook_node)
        workflow.add_node("send_notification", self._notification_node)
        
        # Define edges (flow)
        workflow.set_entry_point("classify_log")
        
        # classify_log → generate_remediation
        workflow.add_edge("classify_log", "generate_remediation")
        
        # generate_remediation → conditional (JIRA or Cookbook)
        workflow.add_conditional_edges(
            "generate_remediation",
            self._should_create_jira,
            {
                "jira": "create_jira_ticket",
                "cookbook": "create_cookbook"
            }
        )
        
        # create_jira_ticket → create_cookbook
        workflow.add_edge("create_jira_ticket", "create_cookbook")
        
        # create_cookbook → send_notification
        workflow.add_edge("create_cookbook", "send_notification")
        
        # send_notification → END
        workflow.add_edge("send_notification", END)
        
        # Compile graph
        return workflow.compile()
    
    def _classify_log_node(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """Node: Log classification"""
        return self.log_classifier.process(state)
    
    def _remediation_node(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """Node: Remediation plan generation"""
        return self.remediation_agent.process(state)
    
    def _jira_node(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """Node: JIRA ticket creation"""
        if self.jira_agent:
            return self.jira_agent.process(state)
        else:
            # Skip if no JIRA credentials
            from orchestrator.state import JIRATicketStatus
            state.jira_ticket_status = JIRATicketStatus(
                created=False,
                error="JIRA credentials not configured"
            )
            return state
    
    def _cookbook_node(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """Node: Cookbook checklist creation"""
        return self.cookbook_agent.process(state)
    
    def _notification_node(self, state: IncidentAnalysisState) -> IncidentAnalysisState:
        """Node: Slack notification"""
        if self.notification_agent:
            return self.notification_agent.process(state)
        else:
            # Skip if no Slack webhook
            from orchestrator.state import NotificationStatus
            state.notification_status = NotificationStatus(
                sent=False,
                error="Slack webhook not configured"
            )
            return state
    
    def _should_create_jira(
        self, 
        state: IncidentAnalysisState
    ) -> Literal["jira", "cookbook"]:
        """
        Conditional edge: Determine if JIRA ticket should be created
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.should_create_jira and self.jira_agent:
            return "jira"
        else:
            return "cookbook"
    
    # def run(self) -> IncidentAnalysisState:
        # """
        # Execute the incident analysis workflow
        
        # Returns:
        #     Final state after all agents have processed
        # """
        # # Run the graph
        # final_state = self.graph.invoke(self.initial_state)
        
        # return final_state
    
    def run(self) -> IncidentAnalysisState:
        """
        Execute the incident analysis workflow
        
        Returns:
            Final state after all agents have processed
        """
        try:
            # Run the graph - it returns the state object directly
            final_state = self.graph.invoke(self.initial_state)
            
            # LangGraph returns the state object directly in newer versions
            # If it's a dict, convert back to Pydantic model
            if isinstance(final_state, dict):
                final_state = IncidentAnalysisState(**final_state)
            
            return final_state
        except Exception as e:
            # If execution fails, return initial state with error
            self.initial_state.errors.append(f"Orchestrator execution failed: {str(e)}")
            return self.initial_state    

    def get_graph_visualization(self) -> str:
        """
        Get a text representation of the graph structure
        
        Returns:
            Graph structure as string
        """
        return """
Incident Analysis Workflow Graph:

┌─────────────────┐
│  START          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log Classifier  │  (Parse & classify logs)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Remediation     │  (Generate fix plan)
└────────┬────────┘
         │
         ▼
      ┌──┴──┐
      │ IF  │ severity == CRITICAL?
      └─┬─┬─┘
    YES │ │ NO
        │ │
        ▼ └──────────┐
┌─────────────────┐  │
│ JIRA Ticket     │  │
└────────┬────────┘  │
         │           │
         └───┬───────┘
             │
             ▼
    ┌─────────────────┐
    │ Cookbook        │  (Create runbook)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Notification    │  (Send to Slack)
    └────────┬────────┘
             │
             ▼
         ┌───────┐
         │  END  │
         └───────┘
"""
