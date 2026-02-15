```xml
<?xml version="1.0" encoding="UTF-8"?>
<astraeus version="1.0" type="multi-agent-research-pipeline">

  <meta>
    <name>Astraeus</name>
    <tagline>Multi-Agent AI Deep Researcher</tagline>
    <entry-points>
      <entry type="web" command="streamlit run app.py" port="8501"/>
      <entry type="cli" command="python cli.py &quot;{query}&quot;" module="cli.py"/>
    </entry-points>
    <shared-context type="dict" flow="sequential-mutation">
      <description>All agents read from and write to a single Python dictionary.
      Each agent receives the full context, adds its output keys, and returns
      the mutated dict to the orchestrator.</description>
    </shared-context>
  </meta>

  <pipeline module="pipeline/orchestrator.py" execution="sequential">
    <state-machine>
      <state id="not_started" initial="true"/>
      <state id="waiting"/>
      <state id="working"/>
      <state id="complete" terminal="true"/>
      <state id="error" terminal="true"/>
      <transition from="not_started" to="waiting"/>
      <transition from="waiting" to="working"/>
      <transition from="working" to="complete"/>
      <transition from="working" to="error"/>
    </state-machine>

    <callbacks>
      <callback name="on_state_change" signature="(PipelineState) -> None" timing="after-each-transition"/>
      <callback name="before_agent_run" signature="(agent_id: str) -> None" timing="before-agent"/>
      <callback name="after_agent_run" signature="(agent_id: str) -> None" timing="after-agent"/>
    </callbacks>
  </pipeline>

  <agents count="6" registry="pipeline.orchestrator.AGENT_REGISTRY">

    <agent id="coordinator" index="0">
      <name>Research Coordinator</name>
      <module>agents/coordinator.py</module>
      <function>run(context: Dict[str, Any]) -> Dict[str, Any]</function>
      <role>Master orchestrator — analyzes query, expands search variants, sets routing</role>
      <skill ref="query-expansion"/>
      <config>
        <param name="MAX_QUERY_EXPANSIONS" source="config.py" default="3"/>
      </config>
      <context-contract>
        <input>
          <key name="query" type="str" required="true">Raw user research query</key>
        </input>
        <output>
          <key name="expanded_queries" type="List[str]">Alternative query phrasings for multi-query retrieval</key>
          <key name="query_analysis" type="dict">Intent, complexity, topics extracted from query</key>
          <key name="routing_hint" type="str">Target retrieval backend (vector_store for v1)</key>
          <key name="coordinator_output" type="dict">Aggregated output for telemetry</key>
        </output>
      </context-contract>
      <internals>
        <function name="_analyze_query">Rule-based intent detection (explanatory/comparative/definitional/enumerative/exploratory), complexity estimation, topic extraction</function>
        <function name="_expand_query">LLM-powered expansion via OpenRouter with template-based fallback</function>
        <function name="_expand_query_via_llm">Sends expansion prompt to chat_completion, parses one-query-per-line response</function>
        <function name="_extract_topic">Strips question words to isolate core topic string</function>
      </internals>
    </agent>

    <agent id="retriever" index="1">
      <name>Contextual Retriever</name>
      <module>agents/retriever.py</module>
      <function>run(context: Dict[str, Any]) -> Dict[str, Any]</function>
      <role>Multi-source evidence collector — vector search + web search, reranking, chunk assembly</role>
      <skill ref="evidence-retrieval"/>
      <config>
        <param name="TOP_K_RESULTS" source="config.py" default="10"/>
        <param name="RERANK_ENABLED" source="config.py" default="true"/>
        <param name="TAVILY_API_KEY" source="config.py" required-for="web,hybrid"/>
      </config>
      <context-contract>
        <input>
          <key name="query" type="str" required="true"/>
          <key name="expanded_queries" type="List[str]" required="true"/>
          <key name="retrieval_mode" type="str" default="hybrid">One of: local, hybrid, web</key>
        </input>
        <output>
          <key name="retrieved_chunks" type="List[dict]">Ranked evidence chunks with text, source, score, source_type</key>
          <key name="retriever_output" type="dict">num_chunks, web_results_count for telemetry</key>
        </output>
      </context-contract>
      <dependencies>
        <dependency module="rag/vector_store.py" for="local vector search"/>
        <dependency module="rag/web_search.py" for="Tavily web search"/>
        <dependency module="rag/document_ingestion.py" for="PDF/doc chunking and embedding"/>
      </dependencies>
    </agent>

    <agent id="critical_analysis" index="2">
      <name>Critical Analysis</name>
      <module>agents/critical_analysis.py</module>
      <function>run(context: Dict[str, Any]) -> Dict[str, Any]</function>
      <role>Evidence analyzer — claim extraction, contradiction detection, evidence chain building</role>
      <skill ref="contradiction-detection"/>
      <context-contract>
        <input>
          <key name="query" type="str" required="true"/>
          <key name="retrieved_chunks" type="List[dict]" required="true"/>
        </input>
        <output>
          <key name="claims" type="List[dict]">Extracted atomic claims with source attribution</key>
          <key name="contradictions" type="List[dict]">Detected conflicts between claims (claim_a, claim_b, conflict_type, confidence)</key>
          <key name="evidence_chains" type="List[dict]">Claims linked to supporting source chunks</key>
          <key name="critical_analysis_output" type="dict">total_claims, contradictions_found for telemetry</key>
        </output>
      </context-contract>
      <techniques>
        <technique name="LLM JSON extraction">Primary claim extraction via structured LLM prompt</technique>
        <technique name="regex fallback">Backup extraction when LLM output is malformed</technique>
        <technique name="semantic conflict heuristics">Negation, numeric, temporal conflict detection without fine-tuned models</technique>
      </techniques>
    </agent>

    <agent id="fact_checker" index="3">
      <name>Fact-Checker</name>
      <module>agents/fact_checker.py</module>
      <function>run(context: Dict[str, Any]) -> Dict[str, Any]</function>
      <role>Claim verifier — source credibility scoring, cross-source validation, verdicting</role>
      <skill ref="source-credibility"/>
      <context-contract>
        <input>
          <key name="query" type="str" required="true"/>
          <key name="claims" type="List[dict]" required="true"/>
          <key name="retrieved_chunks" type="List[dict]" required="true"/>
        </input>
        <output>
          <key name="verified_claims" type="List[dict]">Claims with verdict (Supported/Likely/Plausible/Unverified/Disputed) and confidence</key>
          <key name="fact_checker_output" type="dict">verified, disputed, total_checked for telemetry</key>
        </output>
      </context-contract>
      <credibility-tiers>
        <tier level="1" score="0.95" sources="arxiv, PubMed, IEEE, ACM"/>
        <tier level="2" score="0.90" sources="official docs, RFCs, API references"/>
        <tier level="3" score="0.80" sources="Nature, MIT Tech Review, established publications"/>
        <tier level="4" score="0.65" sources="quality blogs, Towards Data Science"/>
        <tier level="5" score="0.45" sources="general web, unknown origin"/>
        <tier level="6" score="0.50" sources="user-uploaded documents"/>
      </credibility-tiers>
    </agent>

    <agent id="insight_generator" index="4">
      <name>Insight Generator</name>
      <module>agents/insight_generator.py</module>
      <function>run(context: Dict[str, Any]) -> Dict[str, Any]</function>
      <role>Pattern recognizer — theme clustering, knowledge gap detection, hypothesis generation</role>
      <skill ref="theme-synthesis"/>
      <context-contract>
        <input>
          <key name="verified_claims" type="List[dict]" required="true"/>
          <key name="contradictions" type="List[dict]"/>
          <key name="evidence_chains" type="List[dict]"/>
        </input>
        <output>
          <key name="themes" type="List[dict]">Clustered themes with label, strength, claim_ids</key>
          <key name="knowledge_gaps" type="List[dict]">Topics with insufficient evidence</key>
          <key name="hypotheses" type="List[dict]">Testable statements grounded in evidence</key>
          <key name="insight_generator_output" type="dict">themes_found, gaps_identified, hypotheses_generated</key>
        </output>
      </context-contract>
      <techniques>
        <technique name="LLM-driven synthesis">Primary clustering and hypothesis generation</technique>
        <technique name="stats-based fallback">Keyword overlap grouping when LLM unavailable</technique>
      </techniques>
    </agent>

    <agent id="report_builder" index="5">
      <name>Report Builder</name>
      <module>agents/report_builder.py</module>
      <function>run(context: Dict[str, Any]) -> Dict[str, Any]</function>
      <role>Final synthesis — executive summary, key findings, citations, downloadable markdown report</role>
      <skill ref="report-generation"/>
      <context-contract>
        <input>
          <key name="query" type="str" required="true"/>
          <key name="verified_claims" type="List[dict]"/>
          <key name="themes" type="List[dict]"/>
          <key name="knowledge_gaps" type="List[dict]"/>
          <key name="hypotheses" type="List[dict]"/>
          <key name="contradictions" type="List[dict]"/>
          <key name="retrieved_chunks" type="List[dict]"/>
        </input>
        <output>
          <key name="report_markdown" type="str">Full markdown report with citations</key>
          <key name="executive_summary" type="str">3-5 sentence overview</key>
          <key name="key_findings" type="List[str]">Top verified findings</key>
          <key name="report_builder_output" type="dict">word_count, sections for telemetry</key>
        </output>
      </context-contract>
      <report-sections>
        <section order="1">Executive Summary</section>
        <section order="2">Key Findings (with confidence badges)</section>
        <section order="3">Detailed Analysis (per theme, with inline citations)</section>
        <section order="4">Contradictions and Caveats</section>
        <section order="5">Knowledge Gaps</section>
        <section order="6">Sources (numbered reference list)</section>
      </report-sections>
    </agent>

  </agents>

  <skills loader="skills/__init__.py" standard="agentskills.io" format="SKILL.md">
    <description>Each skill is a directory under skills/ containing a SKILL.md with
    YAML frontmatter (name, description) and markdown instructions. Skills are
    loaded at runtime via discover_skills() and mapped to agents via
    get_skill_for_agent(agent_id).</description>

    <skill name="query-expansion" agent="coordinator" path="skills/query-expansion/SKILL.md"/>
    <skill name="evidence-retrieval" agent="retriever" path="skills/evidence-retrieval/SKILL.md"/>
    <skill name="contradiction-detection" agent="critical_analysis" path="skills/contradiction-detection/SKILL.md"/>
    <skill name="source-credibility" agent="fact_checker" path="skills/source-credibility/SKILL.md"/>
    <skill name="theme-synthesis" agent="insight_generator" path="skills/theme-synthesis/SKILL.md"/>
    <skill name="report-generation" agent="report_builder" path="skills/report-generation/SKILL.md"/>

    <api>
      <function name="discover_skills(skills_root?) -> List[Skill]">Scan directory for all valid skills</function>
      <function name="load_skill(skill_dir: Path) -> Skill|None">Load single skill from directory</function>
      <function name="get_skill(name: str) -> Skill|None">Lookup by skill name</function>
      <function name="get_skill_for_agent(agent_id: str) -> Skill|None">Lookup by agent ID using mapping</function>
    </api>
  </skills>

  <cli module="cli.py" entry="python cli.py">
    <description>Headless pipeline execution without Streamlit dependency.
    Uses argparse for argument parsing, calls pipeline.orchestrator.run_pipeline
    directly.</description>

    <arguments>
      <arg name="query" type="positional" required="true">Research query string</arg>
      <arg name="--output|-o" type="str">Save report to file path</arg>
      <arg name="--mode|-m" type="choice" choices="local,hybrid,web" default="hybrid">Retrieval mode</arg>
      <arg name="--model" type="str" default="config.LLM_MODEL">OpenRouter model ID override</arg>
      <arg name="--json" type="flag">Output structured JSON instead of markdown</arg>
      <arg name="--verbose|-v" type="flag">Show tracebacks on error</arg>
      <arg name="--no-color" type="flag">Disable ANSI terminal colors</arg>
      <arg name="--list-agents" type="flag">Print agent registry and exit</arg>
    </arguments>

    <json-output-schema>
      <field name="query" type="str"/>
      <field name="model" type="str"/>
      <field name="mode" type="str"/>
      <field name="elapsed_seconds" type="float"/>
      <field name="agents" type="List[{id, name, state, elapsed, summary}]"/>
      <field name="report" type="str"/>
    </json-output-schema>
  </cli>

  <telemetry module="llm/__init__.py">
    <description>Per-agent token and cost tracking. Each agent's LLM calls are
    tagged with agent_id via set_current_agent(). Totals aggregated in
    pipeline state for dashboard display.</description>
    <metrics>
      <metric name="input_tokens" per="agent"/>
      <metric name="output_tokens" per="agent"/>
      <metric name="total_cost_usd" per="agent"/>
      <metric name="call_count" per="agent"/>
      <metric name="elapsed_seconds" per="agent"/>
    </metrics>
  </telemetry>

  <rag>
    <vector-store module="rag/vector_store.py" backend="chromadb">
      <config>
        <param name="VECTOR_DB_PATH" default="./data/chroma_db"/>
        <param name="COLLECTION_NAME" default="research_docs"/>
        <param name="EMBEDDING_MODEL" default="all-MiniLM-L6-v2"/>
        <param name="EMBEDDING_DIMENSION" default="384"/>
      </config>
    </vector-store>
    <ingestion module="rag/document_ingestion.py">
      <config>
        <param name="UPLOAD_CHUNK_SIZE" default="900"/>
        <param name="UPLOAD_CHUNK_OVERLAP" default="150"/>
      </config>
    </ingestion>
    <web-search module="rag/web_search.py" provider="tavily">
      <config>
        <param name="TAVILY_API_KEY" required="true" for-modes="hybrid,web"/>
      </config>
    </web-search>
  </rag>

  <ui framework="streamlit" module="app.py">
    <styles entry="ui/styles.py" architecture="modular">
      <module file="ui/styles_base.py" lines="344">Global theme, layout, responsive, polish</module>
      <module file="ui/styles_components.py" lines="474">Agent cards, badges, robots, status</module>
      <module file="ui/styles_pipeline.py" lines="185">Pipeline progress, arrows, timeline</module>
      <module file="ui/styles_animations.py" lines="127">21 @keyframes definitions</module>
    </styles>
    <components>
      <component module="ui/components.py">Pipeline cards, progress bar, metric cards</component>
      <component module="ui/embedding_viewer.py">2D embedding space visualization</component>
      <component module="ui/retrieval_waterfall.py">Retrieval score waterfall chart</component>
      <component module="ui/source_or_claims.py">Claims-evidence panel</component>
      <component module="ui/token_cost_viewer.py">Token/cost analytics</component>
      <component module="ui/chat_widget.py">Interactive report Q&amp;A</component>
    </components>
  </ui>

  <testing>
    <suite path="tests/" framework="pytest" config="pytest.ini">
      <test-file name="tests/test_pipeline_smoke.py" tests="2">Pipeline happy path and error handling</test-file>
      <test-file name="tests/test_agents.py" tests="15">Agent imports, basic execution, config validation</test-file>
      <test-file name="tests/test_cli.py" tests="18">CLI parser, colors, agent listing, entry point</test-file>
      <test-file name="tests/test_skills.py" tests="27">Skill discovery, loading, agent mapping, frontmatter parser</test-file>
    </suite>
  </testing>

</astraeus>
```
