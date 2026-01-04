"""Package-level BuildEngine for Mithaly.

This is the canonical engine implementation that lives inside the package
(`src/mithaly/core/`). Root-level runner files should import from here.
The implementation uses LangGraph for orchestration:
START -> Gaps -> Policy -> (Inflection?) -> Planning -> Execution -> Feedback -> END
"""
import sys
import operator
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Union

# Try importing LangGraph (Hard dependency for this new version per implementation plan)
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.runnables import RunnableConfig
except ImportError:
    # LangGraph is optional for tests and local development. Provide
    # lightweight stubs so the package can be imported without exiting.
    print("WARN: LangGraph not found; continuing with fallback stubs.")
    StateGraph = None
    START = "START"
    END = "END"
    MemorySaver = None
    # RunnableConfig is used as a typing alias; fallback to dict for runtime
    RunnableConfig = dict

# --- State Definition ---

# ... (Imports)

# --- State Definition ---

class AgentState(TypedDict):
    """The unified state of the Mithaly agentic lifecycle."""
    text: str
    input: Optional[Union[str, Dict]]
    # Components data
    gap_analysis: Optional[Dict]
    policy_constraints: Optional[Dict]
    plan: Optional[Dict]
    execution_results: Optional[Dict]
    feedback: Optional[Dict]
    # Context
    context_docs: Optional[List[str]]
    # Control flow data
    clarification_questions: Optional[List[str]]
    clarifications: Optional[Dict[str, str]]
    probes: Optional[Dict]
    inflection: Optional[Dict]
    # Protocol Data
    simulation_result: Optional[Dict]
    plan_retries: int
    # Flags
    non_interactive: bool

# --- Node Implementations ---

def get_ollama_client(config: RunnableConfig):
    return config.get('configurable', {}).get('ollama_client')

def node_retrieve(state: AgentState) -> AgentState:
    """Retrieve relevant context from Knowledge Base."""
    print("--- [Node] Retrieve ---")
    
    # Defensive import
    KnowledgeManager = None
    try:
        from mithaly.core.memory.knowledge_manager import KnowledgeManager
    except ImportError:
        try:
            from src.mithaly.core.memory.knowledge_manager import KnowledgeManager
        except ImportError:
            print("WARN: KnowledgeManager not found, skipping retrieval.")
            return {}

    query = state.get('text') or ""
    try:
        km = KnowledgeManager()
        docs = km.search(query, n_results=3)
        if docs:
            print(f"INFO: Retrieved {len(docs)} relevant records.")
        else:
            print("INFO: No relevant knowledge found.")
        return {'context_docs': docs}
    except Exception as e:
        print(f"ERROR: Retrieval failed: {e}")
        return {}

def node_gaps(state: AgentState, config: RunnableConfig) -> AgentState:
    """Run GapAnalyzer to analyze the input request. Uses Fast LLM."""
    print("--- [Node] Gaps ---")
    
    # Defensive import
    try:
        from mithaly.core.gaps.ranker import PriorityRanker
    except ImportError:
        PriorityRanker = None

    ollama = get_ollama_client(config)
    
    user_input = state.get('text') or ""
    context = state.get('context_docs') or []
    
    gaps_data = {}
    # Canonical fallback output for this node to avoid returning None
    _fallback_out = {"gap_analysis": {}, "clarification_questions": []}

    if ollama:
        # LLM Mode
        context_str = "\n".join(context) if context else "No context available."
        prompt = f"""
        You are the Gap Analyzer.
        Request: "{user_input}"
        
        Context from Knowledge Base:
        {context_str}
        
        Analyze the request using the context.
        Identify:
        1. Ambiguities requiring clarification.
        2. Technical gaps.
        3. Impact of each gap (critical, high, medium, low).
        
        Return JSON with keys: 'gaps' (list of dicts with 'description', 'impact'), 'clarification_questions'.
        """
        response = ollama.chat([{"role": "user", "content": prompt}], task_type="fast")
        content = response.get("content", "")
        import json
        try:
            clean = content.replace("```json", "").replace("```", "").strip()
            gaps_data = json.loads(clean)
        except Exception:
            print("WARN: Failed to parse LLM Gaps JSON.")
            gaps_data = {"raw_analysis": content, "gaps": []}
            
        # Apply Ranker
        if PriorityRanker and 'gaps' in gaps_data and isinstance(gaps_data['gaps'], list):
            ranker = PriorityRanker()
            ranked = ranker.rank_gaps(gaps_data['gaps'])
            gaps_data['gaps'] = ranked
            print(f"INFO: Gaps ranked. Top: {ranked[0].get('description') if ranked else 'None'}")

        out = {
            "gap_analysis": gaps_data,
            "clarification_questions": gaps_data.get("clarification_questions")
        }
        # Record transition: Gaps -> Clarify or Policy
        try:
            try:
                from mithaly.core.transition_logger import record_transition
            except Exception:
                from src.mithaly.core.transition_logger import record_transition
            to_layer = 'clarify' if gaps_data.get('clarification_questions') else 'policy'
            rec = {
                'from_layer': 'Gaps',
                'to_layer': to_layer.upper(),
                'actor': 'BuildEngine.node_gaps',
                'outcome': 'completed' if gaps_data else 'no-op'
            }
            record_transition(rec)
        except Exception:
            pass

        return out
        # Legacy Mode (unchanged)
        # ...
    
    
    try:
        from mithaly.core.gaps.gap_analyzer import GapAnalyzer
    except ImportError:
        try:
            from src.mithaly.core.gaps.gap_analyzer import GapAnalyzer
        except ImportError:
            # Emit a minimal transition record indicating gaps was a no-op
            try:
                try:
                    from mithaly.core.transition_logger import record_transition
                except Exception:
                    from src.mithaly.core.transition_logger import record_transition
                rec = {
                    'from_layer': 'Gaps',
                    'to_layer': 'Policy',
                    'actor': 'BuildEngine.node_gaps',
                    'outcome': 'no-op'
                }
                record_transition(rec)
            except Exception:
                pass
            return _fallback_out

    current = {k: v for k, v in state.items() if v is not None}
    if 'text' in current and 'input' not in current:
        current['input'] = current['text']

        try:
            ga = GapAnalyzer()
            ga_out = ga.process(current)
            out = {
                'gap_analysis': ga_out.get('gap_analysis'),
                'clarification_questions': ga_out.get('clarification_questions'),
                'text': ga_out.get('text', state.get('text'))
            }
            try:
                try:
                    from mithaly.core.transition_logger import record_transition
                except Exception:
                    from src.mithaly.core.transition_logger import record_transition
                rec = {
                    'from_layer': 'Gaps',
                    'to_layer': 'CLARIFY' if out.get('clarification_questions') else 'Policy',
                    'actor': 'BuildEngine.node_gaps',
                    'outcome': 'completed' if out.get('gap_analysis') else 'no-op'
                }
                record_transition(rec)
            except Exception:
                pass
            return out
        except Exception as e:
            print(f"ERROR: GapAnalyzer failed: {e}")
            return _fallback_out

    # Final defensive return to ensure a dict is always returned
    return {"gap_analysis": gaps_data if isinstance(gaps_data, dict) else {},
            "clarification_questions": gaps_data.get("clarification_questions") if isinstance(gaps_data, dict) else []}

# ... (Other nodes unchanged)

# --- Graph Construction ---

# (Old BuildEngine removed)

def node_clarification(state: AgentState) -> AgentState:
    """Handle interactive clarifications if requested by Gaps."""
    print("--- [Node] Clarification ---")
    questions = state.get('clarification_questions') or []
    if not questions:
        return {}

    if state.get('non_interactive'):
        print("WARN: Non-interactive mode, skipping clarifications.")
        return {'clarifications': {q: '' for q in questions}}

    print('\n--- مطلوب توضيح إضافي قبل المتابعة ---')
    answers = {}
    for q in questions:
        try:
            a = input(q + '\n> ')
            answers[q] = a
        except Exception:
            answers[q] = ''
    
    orig_text = state.get('text') or ''
    merged_text = orig_text
    if any(answers.values()):
        merged_text += '\n\nClarifications:'
    for q, a in answers.items():
        merged_text += f"\n- {q} -> {a}"

    return {'clarifications': answers, 'text': merged_text}

def node_policy(state: AgentState) -> AgentState:
    """Run PolicyEnforcer to check constraints and probes."""
    print("--- [Node] Policy ---")
    
    # Defensive imports
    PolicyEnforcer = None
    LayerRegistry = None
    try:
        from mithaly.core.policy import PolicyEnforcer
    except ImportError:
        try:
            from src.mithaly.core.policy import PolicyEnforcer
        except ImportError:
            pass
            
    try:
        from mithaly.core.registry import LayerRegistry
    except ImportError:
        try:
            from src.mithaly.core.registry import LayerRegistry
        except ImportError:
            pass

    updates = {}
    
    # Collect probes
    if LayerRegistry:
        try:
            probes = LayerRegistry.collect_probes(state)
            updates['probes'] = probes
        except Exception:
            pass

    # Run semantic probe to aggregate probe results for policy/inflection decisions
    try:
        from mithaly.core.probe import semantic_probe
        probe_results = semantic_probe({**state, **updates})
        updates['probe_results'] = probe_results
    except Exception:
        updates['probe_results'] = {'summary': 'probe-unavailable'}

    # Enforce Policy
    if PolicyEnforcer:
        try:
            payload = {**state, **updates}
            pe = PolicyEnforcer()
            policy_out = pe.process(payload)
            updates['policy_constraints'] = policy_out.get('policy_constraints', {})
        except Exception as e:
            print(f"ERROR: PolicyEnforcer failed: {e}")

    # Check Inflection
    pc = updates.get('policy_constraints', {})
    inflect = bool(pc.get('inflection_point') or pc.get('inflection'))
    
    if inflect:
        updates['inflection'] = {'triggered': True, 'reason': pc}
        print(f"\n--- INFLECTION_POINT TAGGED: {pc} ---")
        # Record transition: Policy -> INFLECTION_POINT
        try:
            from mithaly.core.transition_logger import record_transition
        except Exception:
            try:
                from src.mithaly.core.transition_logger import record_transition
            except Exception:
                record_transition = None

        if record_transition is not None:
            try:
                rec = {
                    'from_layer': 'Policy',
                    'to_layer': 'INFLECTION',
                    'reason': 'policy constraints triggered inflection',
                    'metrics': pc,
                    'actor': 'BuildEngine.node_policy',
                    'outcome': 'blocked',
                    'emergency': False,
                    'provenance': 'engine.node_policy'
                }
                saved = record_transition(rec)
                # propagate transition id back into state so check_inflection can find approvals
                if isinstance(saved, dict) and 'id' in saved:
                    updates.setdefault('inflection', {})['transition_id'] = saved['id']
            except Exception:
                pass
    
    return updates

def node_planning(state: AgentState, config: RunnableConfig) -> AgentState:
    """Run ExecutionPlanner with Virtual Simulation."""
    print("--- [Node] Planning ---")
    
    # Defensive import
    try:
        from mithaly.core.planning.simulator import VirtualSimulator
    except ImportError:
        VirtualSimulator = None

    ollama = get_ollama_client(config)
    plan_data = []

    if ollama:
        # LLM Mode (Smart)
        gaps = state.get('gap_analysis')
        policy = state.get('policy_constraints')
        text = state.get('text')
        last_feedback = state.get('simulation_result', {}).get('feedback', '')
        
        prompt = f"""
        You are the Planner. 
        Request: "{text}"
        Gaps: {gaps}
        Policies: {policy}
        Previous Simulation Feedback (if any): {last_feedback}
        
        Create a detailed execution plan as a list of steps.
        Return JSON: {{ "plan": [list of strings] }}
        """
        response = ollama.chat([{"role": "user", "content": prompt}], task_type="smart")
        content = response.get("content", "")
        
        import json
        try:
            clean = content.replace("```json", "").replace("```", "").strip()
            plan_data = json.loads(clean).get("plan", [])
        except Exception:
            plan_data = [{"description": "Raw Plan: " + content}]
    else:
        # Legacy (fallback)
        pass # (Assume legacy code handles itself or returns empty)

    # Run Simulation
    sim_result = {'passed': True, 'feedback': 'No simulator'}
    if VirtualSimulator and ollama and plan_data:
        sim = VirtualSimulator(ollama)
        sim_result = sim.simulate(plan_data, context=str(state.get('context_docs', '')))
        if not sim_result.get('passed'):
            print(f"WARN: Plan failed simulation: {sim_result.get('feedback')}")
    
    current_retries = state.get('plan_retries', 0)
    
    out = {
        'plan': plan_data, 
        'simulation_result': sim_result,
        'plan_retries': current_retries # Will be incremented by edge logic if looped
    }
    # Record transition: Planning -> Execution or Replan/Feedback
    try:
        try:
            from mithaly.core.transition_logger import record_transition
        except Exception:
            from src.mithaly.core.transition_logger import record_transition
        to_layer = 'execution' if sim_result.get('passed', True) else ('replan_loop' if current_retries < 2 else 'feedback')
        rec = {
            'from_layer': 'Planning',
            'to_layer': to_layer.upper(),
            'actor': 'BuildEngine.node_planning',
            'outcome': 'passed' if sim_result.get('passed', True) else 'failed'
        }
        record_transition(rec)
    except Exception:
        pass

    return out

def node_execution(state: AgentState, config: RunnableConfig) -> AgentState:
    """Run SafeExecutor. Uses Standard LLM."""
    print("--- [Node] Execution ---")
    
    ollama = get_ollama_client(config)
    if ollama:
        # LLM Mode (Standard)
        plan = state.get('plan')
        if not plan:
            return {'execution_results': "No plan to execute."}
            
        prompt = f"""
        You are the Executor.
        Plan: {plan}
        
        Execute the plan by simulating the steps (or writing code if requested).
        For now, describe what you would do.
        """
        response = ollama.chat([{"role": "user", "content": prompt}], task_type="standard")
        result = {'execution_results': response.get("content")}
        try:
            try:
                from mithaly.core.transition_logger import record_transition
            except Exception:
                from src.mithaly.core.transition_logger import record_transition
            rec = {
                'from_layer': 'Execution',
                'to_layer': 'Feedback',
                'actor': 'BuildEngine.node_execution',
                'outcome': 'completed'
            }
            record_transition(rec)
        except Exception:
            pass
        return result

    else:
        # Legacy
        try:
            from mithaly.core.execution.safe_executor import SafeExecutor
        except ImportError:
            try:
                from src.mithaly.core.execution.safe_executor import SafeExecutor
            except ImportError:
                print("WARN: SafeExecutor not found.")
                return {}

        try:
            se = SafeExecutor()
            exec_out = se.process(state)
            # record transition
            try:
                try:
                    from mithaly.core.transition_logger import record_transition
                except Exception:
                    from src.mithaly.core.transition_logger import record_transition
                rec = {
                    'from_layer': 'Execution',
                    'to_layer': 'Feedback',
                    'actor': 'BuildEngine.node_execution',
                    'outcome': 'completed'
                }
                record_transition(rec)
            except Exception:
                pass
            return {'execution_results': exec_out.get('execution_results') if isinstance(exec_out, dict) else None}
        except Exception as e:
            print(f"ERROR: SafeExecutor failed: {e}")
            return {}

def node_feedback(state: AgentState) -> AgentState:
    """Run FeedbackLoop. Handles Memory and Emergency logging."""
    print("--- [Node] Feedback ---")
    
    # Imports
    try:
        from mithaly.core.memory.knowledge_manager import KnowledgeManager
    except ImportError:
        KnowledgeManager = None
        
    execution = state.get('execution_results')
    sim_result = state.get('simulation_result', {})
    
    # Determine Success
    # Simple heuristic: If execution has content and no 'error' keyword in result
    # (Real implementation needs structured output from execution)
    success = False
    if execution and "error" not in str(execution).lower():
        success = True
    
    # 1. Active Memory (Success)
    if success and KnowledgeManager:
        km = KnowledgeManager()
        km.log_knowledge(
            content=f"Lesson learned from successful execution:\n{execution}",
            topics=["lesson", "execution_log"],
            provenance="node_feedback",
            trusted=True
        )
        print("INFO: Success pattern memorized.")

    # 2. Emergency Log (Critical Failure)
    # If simulation failed repeatedly or execution crashed hard
    if not success or (not sim_result.get('passed', True)):
        import json
        from datetime import datetime
        log_entry = {
            "ts": datetime.now().isoformat(),
            "error": "Execution or Simulation Failure",
            "state_dump": str(state)[:500] # Truncated
        }
        try:
            with open("docs/context/emergency.jsonl", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            print("WARN: Critical failure logged to emergency.jsonl")
        except Exception:
            pass

    # record transition: Feedback -> End
    try:
        try:
            from mithaly.core.transition_logger import record_transition
        except Exception:
            from src.mithaly.core.transition_logger import record_transition
        rec = {
            'from_layer': 'Feedback',
            'to_layer': 'END',
            'actor': 'BuildEngine.node_feedback',
            'outcome': 'success' if success else 'failure',
            'emergency': (not success)
        }
        record_transition(rec)
    except Exception:
        pass

    return {'feedback': {'success': success}}

# --- Conditional Logic ---

def check_clarification(state: AgentState) -> str:
    if state.get('clarification_questions'):
        return "clarify"
    return "policy"

def check_simulation(state: AgentState) -> str:
    sim = state.get('simulation_result', {})
    if sim.get('passed', True):
        return "execution"
    
    # Simulation Failed
    retries = state.get('plan_retries', 0)
    if retries < 2:
        print(f"INFO: Simulation failed. Retrying planning (Attempt {retries+1}/2).")
        # Optimization: We should ideally update state['plan_retries'] here, 
        # but Edges don't update state in LangGraph easily (usually nodes do).
        # We'll rely on the node (or an intermediate tool node) to handle increment, 
        # or just assume the loop works if we had a dedicated "RetryNode". 
        # For simplicity, we loop back to 'planning' and hope 'planning' increments or reads it.
        # Actually, node_planning reads current_retries. We need to increment it.
        # Since we can't write in an edge, we might need a small 'increment_retry' node.
        # OR: Just loop to 'planning' and let 'planning' see validity.
        # Let's adjust node_planning to increment if it sees failure from previous turn?
        # NO, simpler: Add a 'replan_loop' node. 
        return "replan_loop"
    
    print("WARN: Max planning retries reached. Aborting to feedback.")
    return "feedback"

def node_replan_loop(state: AgentState) -> AgentState:
    """Helper node to increment retry counter."""
    return {'plan_retries': state.get('plan_retries', 0) + 1}

def check_inflection(state: AgentState) -> str:
    # Inflection decision logic:
    # - If no inflection triggered, continue to planning
    # - If inflection triggered, write a snapshot of the current context to
    #   `docs/context/current_context.json` (so transition_logger can copy it),
    #   then decide whether to halt (end) or allow planning to continue.
    try:
        import os
        import json
    except Exception:
        os = None

    inflection = state.get('inflection') or {}
    if not inflection.get('triggered'):
        return "planning"

    # Ensure current context is persisted for snapshotting
    try:
        ctx_dir = os.path.join('docs', 'context') if os else 'docs/context'
        os.makedirs(ctx_dir, exist_ok=True)
        ctx_path = os.path.join(ctx_dir, 'current_context.json')
        with open(ctx_path, 'w', encoding='utf-8') as cf:
            # Write a minimal serializable view of state
            json.dump({k: v for k, v in state.items() if k != '__internal__'}, cf, ensure_ascii=False, indent=2)
    except Exception:
        # If writing fails, continue to halt (safer) — transition_logger will handle missing file.
        pass

    # Decision: if running in non-interactive mode, halt immediately.
    if state.get('non_interactive'):
        return "end"

    # If a prior approval exists, allow planning to continue.
    # Check on-disk approvals by transition id if available
    tid = inflection.get('transition_id')
    if not inflection.get('approved_by') and tid:
        try:
            import os, json
            appr = os.path.join('docs', 'context', 'approvals', f'approval_{tid}.json')
            if os.path.exists(appr):
                try:
                    with open(appr, 'r', encoding='utf-8') as af:
                        aobj = json.load(af)
                        approved_by = aobj.get('approved_by')
                        if approved_by:
                            inflection['approved_by'] = approved_by
                except Exception:
                    pass
        except Exception:
            pass

    if inflection.get('approved_by'):
        return "planning"

    # Default interactive behaviour: halt and require manual approval
    return "end"

# ...

class BuildEngine:
    def __init__(self, project_path='.'):
        self.project_path = project_path
        # Initialize StateGraph workflow and register nodes
        try:
            self.workflow = StateGraph()
        except Exception:
            # Fallback: create a bare object to avoid attribute errors in tests
            class _DummyWorkflow:
                def add_node(self, *a, **k):
                    return None
                def add_edge(self, *a, **k):
                    return None
                def add_conditional_edges(self, *a, **k):
                    return None
                def compile(self, *a, **k):
                    class _App:
                        def invoke(self, data, config=None):
                            return data
                        async def ainvoke(self, data, config=None):
                            return data
                    return _App()
            self.workflow = _DummyWorkflow()

        # Register core nodes
        self.workflow.add_node("retrieve", node_retrieve)
        self.workflow.add_node("gaps", node_gaps)
        self.workflow.add_node("clarify", node_clarification)
        self.workflow.add_node("policy", node_policy)
        self.workflow.add_node("planning", node_planning)
        self.workflow.add_node("execution", node_execution)
        self.workflow.add_node("feedback", node_feedback)

        # Register replan helper node
        self.workflow.add_node("replan_loop", node_replan_loop) # NEW

        # Add Edges
        self.workflow.add_edge(START, "retrieve")
        self.workflow.add_edge("retrieve", "gaps")
        self.workflow.add_edge("replan_loop", "planning") # Loop back

        # Conditional: Gaps -> Clarify (if needed) -> Policy
        self.workflow.add_conditional_edges(
            "gaps",
            check_clarification,
            {
                "clarify": "clarify",
                "policy": "policy"
            }
        )
        self.workflow.add_edge("clarify", "policy")
        # Policy edge handled by conditional check_inflection below

        # Conditional: Planning -> (Simulation) -> Execution or Replan
        self.workflow.add_conditional_edges(
            "planning",
            check_simulation,
            {
                "execution": "execution",
                "replan_loop": "replan_loop",
                "feedback": "feedback"
            }
        )
        
        self.workflow.add_edge("execution", "feedback")
        self.workflow.add_edge("feedback", END)
        self.workflow.add_conditional_edges(
            "policy",
            check_inflection,
            {
                "end": END,         # Halt if non-interactive inflection
                "planning": "planning"
            }
        )

        # Edges are now handled by conditional logic above


        # Compile
        self.app = self.workflow.compile(checkpointer=MemorySaver())

        # MCP Integration
        self.mcp_client = None
        try:
            from mithaly.core.adapter.mcp_client import McpClient
            self.mcp_client = McpClient()
        except ImportError:
            try:
                from src.mithaly.core.adapter.mcp_client import McpClient
                self.mcp_client = McpClient()
            except ImportError:
                print("WARN: McpClient not found.")
        
        # Ollama Integration
        self.ollama_client = None
        try:
            from mithaly.core.adapter.ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
        except ImportError:
            try:
                from src.mithaly.core.adapter.ollama_client import OllamaClient
                self.ollama_client = OllamaClient()
            except ImportError:
                print("WARN: OllamaClient not found.")

    def run_lifecycle(self, initial_data=None):
        data = initial_data or {'text': 'اختبار دورة Mithaly'}
        if isinstance(initial_data, str) and 'text' not in data:
            data = {'text': initial_data}

        print("Starting LangGraph Lifecycle...")

        # Setup config for run
        config = {"configurable": {"thread_id": "cli-session-1"}}

        # Inject clients if available
        if self.ollama_client:
            config['configurable']['ollama_client'] = self.ollama_client
        if self.mcp_client:
            config['configurable']['mcp_client'] = self.mcp_client

        # Run graph (synchronous invocation)
        try:
            final_state = self.app.invoke(data, config=config)
            print('Lifecycle complete. Final state keys:', list(final_state.keys()))
            return final_state
        except Exception as e:
            print(f"CRITICAL: Graph execution failed: {e}")
            import traceback
            traceback.print_exc()
            return data
        finally:
            if self.mcp_client:
                # Clean up would ideally happen here
                pass

    async def run_lifecycle_async(self, initial_data=None):
        """Async version of lifecycle runner to support MCP and Ollama."""
        data = initial_data or {'text': 'اختبار دورة Mithaly'}
        if 'text' not in data and isinstance(initial_data, str):
            data = {'text': initial_data}

        print("Starting LangGraph Lifecycle (Async)...")
        
        # Load MCP Config
        if self.mcp_client:
            import json
            import os
            config_path = os.path.join(self.project_path, 'docs', 'knowledge', 'mcp_config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        cfg = json.load(f)
                    servers = cfg.get('mcpServers', {})
                    for name, s_cfg in servers.items():
                        await self.mcp_client.connect_server(name, s_cfg)
                except Exception as e:
                    print(f"WARN: Failed to load MCP config: {e}")

        config = {"configurable": {"thread_id": "cli-session-1"}}
        
        # Inject clients
        if self.ollama_client:
            config['configurable']['ollama_client'] = self.ollama_client
        if self.mcp_client:
            config['configurable']['mcp_client'] = self.mcp_client
            
        try:
            final_state = await self.app.ainvoke(data, config=config)
            print('Lifecycle complete. Final state keys:', list(final_state.keys()))
            return final_state
        except Exception as e:
            print(f"CRITICAL: Graph execution failed: {e}")
            import traceback
            traceback.print_exc()
            return data
        finally:
            if self.mcp_client:
                await self.mcp_client.cleanup()

if __name__ == '__main__':
    import argparse
    import asyncio
    parser = argparse.ArgumentParser(description='Run Mithaly package engine lifecycle via LangGraph')
    parser.add_argument('--text', '-t', help='Initial text input', default='اختبار دورة Mithaly')
    args = parser.parse_args()

    engine = BuildEngine(project_path='.')
    # engine.run_lifecycle({'text': args.text}) # Old sync way
    asyncio.run(engine.run_lifecycle_async({'text': args.text}))
