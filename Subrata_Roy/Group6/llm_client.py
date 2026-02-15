"""
LLM client utility for OpenRouter integration.
Provides a unified interface for making LLM calls.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from typing import Type, Any
import json


class LLMClient:
    """Wrapper for OpenRouter LLM calls with structured output parsing"""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4o"):
        """
        Initialize LLM client
        
        Args:
            api_key: OpenRouter API key
            model: Model name (default: openai/gpt-4o)
        """
        self.api_key = api_key
        self.model = model
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,  # Low temperature for consistent outputs
            max_tokens=2000
        )
    
    def invoke_with_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[BaseModel]
    ) -> BaseModel:
        """
        Invoke LLM with structured output parsing
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            output_schema: Pydantic model for output validation
            
        Returns:
            Parsed and validated output as Pydantic model
        """
        schema_dict = output_schema.model_json_schema()
        format_instructions = f"""
You must respond with valid JSON. Return a flat JSON OBJECT with the field names at the root level.
Do NOT return a JSON Schema definition (with "properties", "type", "title"). Return the actual data.

Expected structure (field names as top-level keys):
{json.dumps({k: "<value>" for k in schema_dict.get("required", []) + [p for p in schema_dict.get("properties", {}) if p not in schema_dict.get("required", [])]}, indent=2)}

Full schema for reference:
{json.dumps(schema_dict, indent=2)}

Ensure your response is ONLY valid JSON, no markdown formatting or explanation.
"""
        enhanced_system_prompt = f"{system_prompt}\n\n{format_instructions}"
        
        # Create messages
        messages = [
            SystemMessage(content=enhanced_system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Invoke LLM
        response = self.llm.invoke(messages)
        
        # Parse output
        try:
            # Extract raw text (handle list of content blocks from some LLM APIs)
            raw = response.content
            if isinstance(raw, list):
                content = "".join(
                    b.get("text", b) if isinstance(b, dict) else str(b)
                    for b in raw
                )
            else:
                content = str(raw) if raw is not None else ""
            
            # Remove markdown code blocks, pick segment that looks like JSON
            if content and "```" in content:
                if "```json" in content:
                    parts = content.split("```json")[1].split("```")
                else:
                    parts = content.split("```")[1:]
                extracted = ""
                for p in parts:
                    candidate = p.strip()
                    if candidate and (candidate.startswith("{") or candidate.startswith("[")):
                        extracted = candidate
                        break
                    elif candidate:
                        extracted = candidate
                content = extracted or content
            elif content:
                content = content.strip()
            
            # Fallback: extract JSON object if embedded in text
            if not content:
                content = str(raw) if raw is not None else ""
            if content.strip() and not content.strip().startswith("{") and not content.strip().startswith("["):
                start = content.find("{")
                if start >= 0:
                    depth = 0
                    for i, c in enumerate(content[start:], start):
                        if c == "{":
                            depth += 1
                        elif c == "}":
                            depth -= 1
                            if depth == 0:
                                content = content[start : i + 1]
                                break
            
            parsed_dict = json.loads(content)
            data_dict = parsed_dict
            if isinstance(parsed_dict, dict):
                schema_keys = {"properties", "type", "title", "description", "required"}
                required_fields = set(output_schema.model_json_schema().get("required", []))
                props = parsed_dict.get("properties", {})
                def _is_data(val):
                    if isinstance(val, (str, list, int, float, bool)) or val is None:
                        return True
                    if isinstance(val, dict):
                        return not ({"type", "description"} & set(val.keys()))
                    return False
                cond_match = (
                    required_fields and not required_fields.intersection(parsed_dict.keys())
                    and schema_keys.intersection(parsed_dict.keys())
                    and isinstance(props, dict) and required_fields.issubset(props.keys())
                )
                if cond_match and all(_is_data(props.get(f)) for f in required_fields):
                    data_dict = {k: props[k] for k in required_fields}
                    data_dict.update({k: v for k, v in props.items() if k not in required_fields})
            return output_schema(**data_dict)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM output: {str(e)}\nRaw output: {response.content}")
    
    def invoke_simple(self, system_prompt: str, user_prompt: str) -> str:
        """
        Simple LLM invocation without structured output
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            
        Returns:
            Raw string response
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
