"""
LLM client utility for OpenRouter integration.
Provides a unified interface for making LLM calls.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from pathlib import Path
from typing import Type, Any
import json
import time

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent
_DEBUG_LOG = _PROJECT_ROOT / ".cursor" / "debug.log"
_DEBUG_LOG_FALLBACK = _PROJECT_ROOT / "debug_run.log"
_DEBUG_LOG_LOCAL = _THIS_DIR / "debug_llm.log"


def _dbg_log(entry: dict) -> None:
    for path in (_DEBUG_LOG_LOCAL, _DEBUG_LOG, _DEBUG_LOG_FALLBACK):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            return
        except Exception:
            continue
    import sys
    print(f"[DEBUG] _dbg_log fallback: {entry}", file=sys.stderr)


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
        _dbg_log({"id":"llm_entry","timestamp":time.time()*1000,"location":"llm_client.py:invoke","message":"invoke_with_structured_output called","data":{"schema":output_schema.__name__}})
        # Add JSON schema instructions to system prompt
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
            
            # Remove markdown code blocks if present
            if content and "```" in content:
                if "```json" in content:
                    parts = content.split("```json")[1].split("```")
                else:
                    parts = content.split("```")[1:]
                # Take first non-empty part that looks like JSON, or first part
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
            
            # Fallback: extract JSON object if embedded in surrounding text
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
            
            # Parse JSON
            parsed_dict = json.loads(content)
            # #region agent log
            _dbg_log({"id":"llm_parse_1","timestamp":time.time()*1000,"location":"llm_client.py:parse","message":"Parsed LLM output","data":{"parsed_keys":list(parsed_dict.keys()) if isinstance(parsed_dict,dict) else "not_dict","has_properties":"properties" in parsed_dict if isinstance(parsed_dict,dict) else False,"required_from_schema":schema_dict.get("required",[])}})
            # #endregion

            # Some LLMs return the schema structure with data in "properties" instead of a flat object.
            # Detect and extract: if root has schema keys (properties, type, title) but missing required
            # fields, and "properties" contains actual data values (not nested schemas), use those.
            data_dict = parsed_dict
            if isinstance(parsed_dict, dict):
                schema_keys = {"properties", "type", "title", "description", "required"}
                required_fields = set(output_schema.model_json_schema().get("required", []))
                props = parsed_dict.get("properties", {})
                def _is_data(val: Any) -> bool:
                    if isinstance(val, (str, list, int, float, bool)) or val is None:
                        return True
                    if isinstance(val, dict):
                        return not ({"type", "description"} & set(val.keys()))
                    return False

                cond_match = (
                    required_fields
                    and not required_fields.intersection(parsed_dict.keys())
                    and schema_keys.intersection(parsed_dict.keys())
                    and isinstance(props, dict)
                    and required_fields.issubset(props.keys())
                )
                # #region agent log
                if cond_match:
                    _checks = {f: (type(props.get(f)).__name__, _is_data(props.get(f))) for f in required_fields}
                    _dbg_log({"id":"llm_props_check","timestamp":time.time()*1000,"location":"llm_client.py:props_check","message":"Properties data check","data":{"field_checks":_checks,"all_pass":all(_is_data(props.get(f)) for f in required_fields),"hypothesisId":"D"}})
                # #endregion
                if cond_match and all(_is_data(props.get(f)) for f in required_fields):
                        data_dict = {k: props[k] for k in required_fields}
                        data_dict.update({k: v for k, v in props.items() if k not in required_fields})
                        # #region agent log
                        _dbg_log({"id":"llm_extract","timestamp":time.time()*1000,"location":"llm_client.py:extract_properties","message":"Extracted from properties","data":{"data_dict_keys":list(data_dict.keys()),"hypothesisId":"A"}})
                        # #endregion

            # Validate with Pydantic
            # #region agent log
            _dbg_log({"id":"llm_validate","timestamp":time.time()*1000,"location":"llm_client.py:validate","message":"Before Pydantic validation","data":{"data_dict_keys":list(data_dict.keys()) if isinstance(data_dict,dict) else "N/A","schema_name":output_schema.__name__,"hypothesisId":"B"}})
            # #endregion
            return output_schema(**data_dict)
        except Exception as e:
            # #region agent log
            _dbg_log({"id":"llm_error","timestamp":time.time()*1000,"location":"llm_client.py:except","message":"Parse/validation failed","data":{"error_type":type(e).__name__,"error_msg":str(e),"raw_preview":(response.content or "")[:500],"hypothesisId":"C"}})
            # #endregion
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
