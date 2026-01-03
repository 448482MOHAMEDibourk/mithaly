# Knowledge Log: core
Generated: 2026-01-03 01:45:34.492595

## 2026-01-03T01:45:25.924070 | ID: e9afd975
**Topics**: documentation, core, adapter | **Trusted**: True

"""Adapter package for external components to interface with Mithaly Core."""


---
## 2026-01-03T01:45:25.421196 | ID: 510121b6
**Topics**: documentation, core, adapter | **Trusted**: True

"""Generator Adapter - The Sovereign Embassy for the Generator.

This component provides a stable interface for the Project Generator (and other
external tools) to interact with the Mithaly Core layers (Gaps, Planning,
Execution, Feedback). It solves the "Floating Generator" gap by anchoring
the generator's identity within the core architecture.
"""
from typing import Dict, Any, Optional
from mithaly.core.registry import LayerRegistry

class GeneratorAdapter:
    """The embassy class for the Generator."""

    def __init__(self, generator_id: str = "default_generator"):
        self.generator_id = generator_id
        # Ensure we can see the layers
        LayerRegistry.autodiscover()

    def request_gap_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the GapAnalyzer layer."""
        return self._delegate_to_layer('Gaps', 'gap_analyzer', payload)

    def request_planning(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the ExecutionPlanner layer."""
        return self._delegate_to_layer('Planning', 'execution_planner', payload)

    def request_execution(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the SafeExecutor layer."""
        return self._delegate_to_layer('Execution', 'safe_executor', payload)

    def request_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the FeedbackLoop layer."""
        return self._delegate_to_layer('Feedback', 'feedback_loop', payload)

    def _delegate_to_layer(self, layer_category: str, layer_hint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generic delegation logic with error handling."""
        # Try to find by name, or use registry keys if known
        # Current registry logic relies on manual registration or auto-discovery.
        # We'll assume the standard names are registered or we try to find them.
        
        # Simple lookup: try to find a class named similarly to layer_hint
        # in the registry keys (case-insensitive search for robustness)
        target_cls = None
        for name in LayerRegistry.list():
            if layer_hint.lower() in name.lower():
                target_cls = LayerRegistry.get(name)
                break
        
        if not target_cls:
             # Fallback: try to instantiate directly if we know the path (shortcuts)
             # This is a bit "floating" but helpful if registry is empty
             return {"error": f"Layer {layer_hint} not found in registry", "status": "failed"}

        try:
            instance = target_cls()
            if hasattr(instance, 'process'):
                return instance.process(payload)
            else:
                return {"error": f"Layer {layer_hint} does not have process() method", "status": "failed"}
        except Exception as e:
            return {"error": f"Exception calling layer {layer_hint}: {str(e)}", "status": "failed"}

    def get_status(self):
        """Return the status of the embassy."""
        return {
            "id": self.generator_id,
            "connected_layers": LayerRegistry.list(),
            "status": "active"
        }


---
## 2026-01-03T01:45:24.951272 | ID: 1fb9ee19
**Topics**: documentation, core, adapter | **Trusted**: True

"""LangGraph adapter shim for optional integration.

This module provides a lightweight wrapper so the codebase can probe for
LangGraph availability without hard-failing at import time.
"""
from typing import Optional

try:
    from langgraph.graph import StateGraph
    from langgraph.checkpoint.memory import MemorySaver
    _HAS_LANGGRAPH = True
except Exception:
    StateGraph = None
    MemorySaver = None
    _HAS_LANGGRAPH = False


class LangGraphAdapter:
    """Adapter to hide LangGraph as an optional dependency.

    Usage:
      adapter = LangGraphAdapter()
      if adapter.is_available():
          g = adapter.create_state_graph()
    """

    def __init__(self):
        self.available = _HAS_LANGGRAPH

    def is_available(self) -> bool:
        return self.available

    def create_state_graph(self, *args, **kwargs) -> Optional[object]:
        """Create a StateGraph instance when LangGraph is installed.

        Returns None if LangGraph is not available.
        """
        if not self.available or StateGraph is None:
            return None
        # Keep construction light here; callers can configure nodes/actions.
        try:
            saver = MemorySaver()
            graph = StateGraph(checkpoint=saver, *args, **kwargs)
            return graph
        except Exception:
            return None


---
## 2026-01-03T01:45:24.464603 | ID: 71a72741
**Topics**: documentation, core, adapter | **Trusted**: True

"""McpClient - Adapter for Model Context Protocol.

This component allows Mithaly to connect to MCP servers (like filesystem, postgres, etc.)
and unify tool/resource access.
"""
import asyncio
import json
import os
import shutil
import subprocess
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    # Fallback to avoid crash if mcp is not yet installed (e.g. during bootstrap)
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


class McpClient:
    """Client to manage connections to MCP servers."""

    def __init__(self):
        self.sessions = {} # server_name -> session
        self.exit_stack = AsyncExitStack()

    async def connect_server(self, name: str, config: Dict[str, Any]):
        """Connect to an MCP server using the provided configuration."""
        if not ClientSession:
            print("ERROR: 'mcp' package not installed.")
            return

        command = config.get('command')
        args = config.get('args', [])
        env = config.get('env', {})

        # Merge current env with config env
        full_env = os.environ.copy()
        full_env.update(env)

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=full_env
        )

        try:
            # We use the stdio_client context manager
            # Note: In a long-running app, we need to keep the context open.
            # Using AsyncExitStack to manage these generic contexts.
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            print(f"Connected to MCP server: {name}")
            self.sessions[name] = session
        except Exception as e:
            print(f"Failed to connect to MCP server {name}: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools from all connected servers."""
        all_tools = []
        for name, session in self.sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    # Namespacing: server__tool
                    t_dict = tool.model_dump() if hasattr(tool, 'model_dump') else tool.__dict__
                    t_dict['name'] = f"{name}__{t_dict['name']}"
                    all_tools.append(t_dict)
            except Exception as e:
                print(f"Error listing tools from {name}: {e}")
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool on a specific server."""
        session = self.sessions.get(server_name)
        if not session:
            return {"error": f"Server {server_name} not connected"}
        
        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def read_resource(self, uri: str) -> Any:
        """Read a resource from any server that supports it."""
        # Naive implementation: try all servers or route by scheme?
        # For now, let's just try all.
        for name, session in self.sessions.items():
            try:
                result = await session.read_resource(uri)
                return result
            except Exception:
                # continue to next server
                pass
        return None

    async def cleanup(self):
        """Close all connections."""
        await self.exit_stack.aclose()


---
## 2026-01-03T01:45:23.980848 | ID: 4ac36b12
**Topics**: documentation, core, adapter | **Trusted**: True

"""OllamaClient - Adapter for Local LLM (Ollama).

This adapter handles connection to the local Ollama instance and provides
a unified interface for chat completions, including model routing and
performance tracking.
"""
import time
import json
import os
import httpx
from typing import List, Dict, Any, Optional

class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.routing_table = {}
        self.metrics_file = None
        self._load_config()

    def _load_config(self):
        """Load routing table and metrics file path."""
        # Defaults
        self.routing_table = {
            "fast": "qwen2.5-coder:3b",
            "standard": "qwen2.5-coder:7b-instruct-q4_K_M",
            "smart": "deepseek-coder-v2:16b-lite-instruct-q3_K_S"
        }
        
        # Try to load from file
        try:
            base = os.getcwd()
            path = os.path.join(base, 'docs', 'knowledge', 'routing_table.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.routing_table = json.load(f)
            
            # Setup metrics path
            metrics_dir = os.path.join(base, 'docs', 'knowledge', 'metrics')
            if not os.path.exists(metrics_dir):
                os.makedirs(metrics_dir, exist_ok=True)
            self.metrics_file = os.path.join(metrics_dir, 'model_metrics.jsonl')
        except Exception as e:
            print(f"WARN: Failed to load LLM config: {e}")

    def route(self, task_type: str) -> str:
        """Select the best model for the task type."""
        # Fallback to standard if unknown
        model = self.routing_table.get(task_type, self.routing_table.get("standard"))
        # Fallback to hardcoded string if config is empty
        return model or "qwen2.5-coder:7b"

    def chat(self, messages: List[Dict[str, str]], task_type: str = "standard") -> Dict[str, Any]:
        """Send chat request to Ollama with automatic routing and tracking."""
        model = self.route(task_type)
        print(f"--- [LLM] Asking {model} (Task: {task_type}) ---")
        
        start_time = time.time()
        success = False
        response_content = ""
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            # Use httpx for sync call (can be async'd later)
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                
                response_content = data.get("message", {}).get("content", "")
                success = True
                return {"content": response_content, "raw": data}
                
        except Exception as e:
            print(f"ERROR: LLM Call failed ({model}): {e}")
            return {"content": f"Error: {str(e)}", "error": True}
            
        finally:
            duration = time.time() - start_time
            self._track_metrics(model, task_type, duration, success)

    def _track_metrics(self, model: str, task_type: str, duration: float, success: bool):
        """Log performance metrics."""
        if not self.metrics_file:
            return
            
        entry = {
            "timestamp": time.time(),
            "model": model,
            "task_type": task_type,
            "duration": duration,
            "success": success
        }
        
        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass # Don't crash on logging


---
## 2026-01-03T01:45:23.488392 | ID: 360adc8e
**Topics**: documentation, core | **Trusted**: True

# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer
from datetime import datetime, timezone
import json
import pathlib


@register_layer('feedback')
class FeedbackLoop:
    """Simple FeedbackLoop stub for mithaly.core.feedback."""

    def __init__(self):
        pass

    def process(self, data):
        """Record results and indicate the feedback layer is running."""
        print("[feedback] FeedbackLoop تعمل الآن. المدخل:", data)
        return {
            'layer': 'feedback',
            'status': 'ok',
            'recorded': True,
            'input': data,
            'probe': {
                'layer': 'feedback',
                'capabilities': ['record_result', 'detect_risks'],
                'requirements': {'requires_network': 'no'},
                'attributes': {'estimated_time_seconds': 2, 'sensitive': False},
            }
        }

    def probe(self, data=None):
        return {
            'layer': 'feedback',
            'capabilities': ['record_result', 'detect_risks'],
            'requirements': {'requires_network': 'no'},
            'attributes': {'estimated_time_seconds': 2, 'sensitive': False},
        }

    def persist_to_kb(self, record: dict) -> bool:
        """Persist a trusted record into a simple on-disk KB under `docs/knowledge/kb.json`.

        Returns True on success, False otherwise.
        """
        try:
            # Enforce trusted filter: only persist records explicitly marked trusted
            if not bool(record.get('trusted')):
                # Reject untrusted records; caller should handle audit tickets
                return False
            kb_dir = pathlib.Path('docs') / 'knowledge'
            kb_dir.mkdir(parents=True, exist_ok=True)
            kb_file = kb_dir / 'kb.json'
            if kb_file.exists():
                try:
                    with open(kb_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f) or []
                except Exception:
                    existing = []
            else:
                existing = []
            existing.append({'timestamp': datetime.now(timezone.utc).isoformat(), 'record': record})
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


---
## 2026-01-03T01:45:23.015515 | ID: 42c2dcb6
**Topics**: documentation, core | **Trusted**: True

"""
mithaly.core.feedback
طبقة التغذية الراجعة (layer): تسجيل النتائج، تحديث المعرفة، والنسخ الاحتياطي الذكي.
واجهات مقترحة:
- `FeedbackManager`

تأكيد: 'طبقة' هو المصطلح المعتمد لوصف التقسيم المعماري.
"""

__all__ = [
    "FeedbackManager",
]

try:
    from .feedback_loop import FeedbackLoop  # noqa: F401
except Exception:
    FeedbackLoop = None


---
## 2026-01-03T01:45:22.548689 | ID: 4c382f56
**Topics**: documentation, core | **Trusted**: True

# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer


@register_layer('execution')
class SafeExecutor:
    """Simple SafeExecutor stub for mithaly.core.execution."""

    def __init__(self):
        pass

    def process(self, data):
        """Execute a plan or step and indicate the execution layer is running."""
        print("[execution] SafeExecutor تعمل الآن. المدخل:", data)
        return {
            'layer': 'execution',
            'status': 'ok',
            'result': {},
            'input': data,
            'probe': {
                'layer': 'execution',
                'capabilities': ['run_steps', 'sandbox'],
                'requirements': {'requires_container_runtime': 'maybe'},
                'attributes': {'estimated_time_seconds': 60, 'sensitive': False},
            }
        }

    def probe(self, data=None):
        return {
            'layer': 'execution',
            'capabilities': ['run_steps', 'sandbox'],
            'requirements': {'requires_container_runtime': 'maybe'},
            'attributes': {'estimated_time_seconds': 60, 'sensitive': False},
        }


---
## 2026-01-03T01:45:22.076496 | ID: 8ac7e486
**Topics**: documentation, core | **Trusted**: True

"""
mithaly.core.execution
طبقة التنفيذ الآمن (layer): تنفيذ آمن مع رصد، تراجع، ووقف طارئ.
واجهة مقترحة:
- `SafeExecutor`

نستخدم مصطلح "طبقة" بشكل موحّد عبر الكود والوثائق.
"""

__all__ = [
    "SafeExecutor",
]

try:
    from .safe_executor import SafeExecutor  # noqa: F401
except Exception:
    SafeExecutor = None


---
## 2026-01-03T01:45:21.516841 | ID: 2470a141
**Topics**: documentation, core | **Trusted**: True

# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer


@register_layer('planning')
class ExecutionPlanner:
    """Simple ExecutionPlanner stub for mithaly.core.planning."""

    def __init__(self):
        pass

    def process(self, data):
        """Process input data and indicate the planning layer is running."""
        print("[planning] ExecutionPlanner تعمل الآن. المدخل:", data)
        return {
            'layer': 'planning',
            'status': 'ok',
            'plan': {'steps': []},
            'input': data,
            'probe': {
                'layer': 'planning',
                'capabilities': ['create_plan', 'estimate_time'],
                'requirements': {'requires_network': 'maybe'},
                'attributes': {'estimated_time_seconds': 10, 'sensitive': False},
            }
        }

    def probe(self, data=None):
        return {
            'layer': 'planning',
            'capabilities': ['create_plan', 'estimate_time'],
            'requirements': {'requires_network': 'maybe'},
            'attributes': {'estimated_time_seconds': 10, 'sensitive': False},
        }


---
## 2026-01-03T01:45:21.058456 | ID: d45816b1
**Topics**: documentation, core | **Trusted**: True

"""
mithaly.core.planning
طبقة التخطيط (layer): التخطيط المعرفي، التخطيط التكيفي، ومحاكاة التنفيذ.
واجهات مقترحة:
- `KnowledgePlanner`, `AdaptivePlanner`, `Simulator`.

ملاحظة: المصطلح الرسمي عبر المشروع هو "طبقة" (layer).
"""

__all__ = [
    "KnowledgePlanner",
    "AdaptivePlanner",
    "Simulator",
]

try:
    from .execution_planner import ExecutionPlanner  # noqa: F401
except Exception:
    ExecutionPlanner = None


---
## 2026-01-03T01:45:20.613918 | ID: a0f8a7b6
**Topics**: documentation, core | **Trusted**: True

'missing_language')
            suggestions.append('لم تُذكر لغة برمجة مفضلة؛ حدد لغة أو أطر عمل إن وُجدت.')
        # if text implies persistent data but no DB mentioned
        if any(w in norm for w in ['data', 'database', 'حفظ', 'تخزين', 'بيانات', 'store']):
            if not detected_databases:
                technical_gaps.append('missing_database')
                suggestions.append('المشروع يتعامل مع بيانات لكن لم تُذكر قاعدة بيانات؛ ضع متطلبات التخزين.')
        # generate clarification questions when technical gaps exist for web/bot projects
        clarification_questions = []
        if technical_gaps and project_type in ('web', 'bot'):
            if 'missing_language' in technical_gaps:
                clarification_questions.append('ما لغة البرمجة والإطار المفضل لديك؟ مثال: Python/Django، JavaScript/Node.js/Express')
            if 'missing_database' in technical_gaps:
                clarification_questions.append('ما قاعدة البيانات التي تفضل استخدامها لحفظ السجلات والبيانات؟ مثال: PostgreSQL، MySQL، MongoDB')
            if needs_clarification:
                clarification_questions.append('هل يمكنك إعطاء أمثلة للبيانات أو السيناريوهات الرئيسية لاستخدام النظام؟')

        print('[gaps] GapAnalyzer تعمل الآن. الكلمات المفتاحية المستخرجة:', keywords)
        print('[gaps] تصنيف نوع المشروع:', project_type)
        if detected_languages:
            print('[gaps] لغات مكتشفة:', detected_languages)
        if detected_databases:
            print('[gaps] قواعد بيانات مكتشفة:', detected_databases)
        if clarification_questions:
            print('[gaps] أسئلة توضيحية مقترحة:', clarification_questions)
        elif needs_clarification or technical_gaps:
            print('[gaps] احتياج إلى توضيح أو فجوات تقنية — اقتراحات:', suggestions)
        else:
            print('[gaps] الوصف كافٍ للمستوى الأولي.')

        return {
            'layer': 'gaps',
            'status': 'ok',
            'keywords': keywords,
            'needs_clarification': needs_clarification,
            'suggestions': suggestions,
            'project_type': project_type,
            'detected_languages': detected_languages,
            'detected_databases': detected_databases,
            'technical_gaps': technical_gaps,
            'clarification_questions': clarification_questions,
            'input': data,
            'probe': {
                'layer': 'gaps',
                'capabilities': ['extract_keywords', 'detect_databases'],
                'requirements': {
                    'requires_db': 'yes' if detected_databases else 'maybe'
                },
                'attributes': {
                    'estimated_time_seconds': 5,
                    'sensitive': False,
                }
            },
        }

    def probe(self, data=None):
        """Return a lightweight probe describing capabilities/requirements."""
        # re-run a light detection if data provided, otherwise generic
        if data and isinstance(data, dict):
            det = []
            g = self.process(data)
            det = g.get('detected_databases', [])
            req = {'requires_db': 'yes' if det else 'maybe'}
        else:
            req = {'requires_db': 'maybe'}

        return {
            'layer': 'gaps',
            'capabilities': ['extract_keywords', 'detect_databases'],
            'requirements': req,
            'attributes': {'estimated_time_seconds': 5, 'sensitive': False},
        }



---
## 2026-01-03T01:45:20.130690 | ID: 965e77c0
**Topics**: documentation, core | **Trusted**: True

# -*- coding: utf-8 -*-
from mithaly.core.registry import register_layer


@register_layer('gaps')
class GapAnalyzer:
    """Simple GapAnalyzer stub for mithaly.core.gaps.

    Upgraded: `process` now extracts keywords and flags incomplete descriptions.
    """

    def __init__(self):
        pass

    def process(self, data):
        """Process input data: extract keywords and assess completeness.

        Heuristics implemented:
        - Tokenize text, remove common stopwords (Arabic + English)
        - Choose top keywords by frequency
        - Flag `needs_clarification` when text is short or few keywords found

        Args:
            data: input string or dict containing 'text' key.
        Returns:
            dict with keys: `layer`, `status`, `keywords`, `needs_clarification`, `suggestions`, `input`
        """
        text = None
        if isinstance(data, dict):
            text = data.get('text') or data.get('description')
        elif isinstance(data, str):
            text = data

        if not text:
            print('[gaps] GapAnalyzer: لا يوجد وصف نصي؛ يلزم توضيح الوصف.')
            return {
                'layer': 'gaps',
                'status': 'ok',
                'keywords': [],
                'needs_clarification': True,
                'suggestions': ['أضف وصفاً مختصراً عن الهدف، النتيجة المتوقعة، والقيود.'],
                'input': data,
            }

        import re
        from collections import Counter

        # minimal stopword sets (expandable)
        arabic_stop = set(['و', 'في', 'على', 'من', 'إلى', 'عن', 'هذا', 'هذه', 'هو', 'هي', 'أن', 'ما', 'مع', 'كل', 'ل', 'لا', 'نحن', 'أنا', 'هناك', 'قد', 'كان', 'كانت'])
        english_stop = set(['the', 'and', 'or', 'in', 'on', 'of', 'to', 'a', 'an', 'for', 'with', 'by', 'is', 'are', 'be'])

        # normalize and tokenize
        norm = text.lower()
        tokens = re.findall(r"[\w\u0600-\u06FF']+", norm)
        # filter tokens
        tokens = [t for t in tokens if len(t) > 1 and t not in arabic_stop and t not in english_stop]

        counts = Counter(tokens)
        # choose top keywords (up to 8)
        keywords = [w for w, _ in counts.most_common(8)]

        # heuristics for clarification
        needs_clarification = False
        suggestions = []
        if len(text.strip()) < 40 or len(keywords) < 3:
            needs_clarification = True
            suggestions.append('الوصف قصير أو مفتقر لتفاصيل كافية؛ أضف هدفًا واضحًا ونطاقًا أو أمثلة.')

        # detect vague terms
        vague = set(['بعض', 'متعدد', 'غير محدد', 'etc', 'etc.'])
        if any(v in norm for v in vague):
            needs_clarification = True
            suggestions.append('تجنّب الكلمات الفضفاضة مثل "بعض" أو "متعدد"؛ حدد أمثلة أو أرقام إن أمكن.')
        # Context analysis: classify project type and detect technical mentions
        project_type = None
        detected_languages = []
        detected_databases = []
        technical_gaps = []

        # project type heuristics
        if any(k in norm for k in ['web', 'ويب', 'frontend', 'backend', 'django', 'flask', 'react', 'angular', 'vue']):
            project_type = 'web'
        elif any(k in norm for k in ['cli', 'command-line', 'سطر', 'terminal']):
            project_type = 'cli'
        elif any(k in norm for k in ['bot', 'telegram', 'slack', 'discord', 'روبوت']):
            project_type = 'bot'
        else:
            project_type = 'unknown'

        # detect languages and databases
        language_keywords = {'python', 'javascript', 'java', 'go', 'rust', 'php', 'ruby', 'c#', 'c++'}
        db_keywords = {'mysql', 'postgres', 'postgresql', 'sqlite', 'mongodb', 'redis'}
        for lang in language_keywords:
            if lang in norm:
                detected_languages.append(lang)
        for db in db_keywords:
            if db in norm:
                detected_databases.append(db)

        # technical gap heuristics
        if not detected_languages:
            technical_gaps.append(

---
## 2026-01-03T01:45:19.691382 | ID: 25c17ea5
**Topics**: documentation, core | **Trusted**: True

"""
mithaly.core.gaps
طبقة الفجوات (layer): استكشاف، تحليل السبب الجذري، وترتيب الأولويات.
تحتوي هذه الطبقة على واجهات وملفات تنفيذية لـ:
- `GapAnalyzer`: اكتشاف الفجوات، تحليل الأسباب الجذرية، وترتيب الأولويات.

ملاحظة: نستخدم مصطلح "طبقات (layers)" عبر المشروع لوصف التقسيم المعماري.
"""

__all__ = [
    "GapAnalyzer",
]

try:
    from .gap_analyzer import GapAnalyzer  # noqa: F401
except Exception:
    GapAnalyzer = None


---
## 2026-01-03T01:45:19.220792 | ID: d3c535e0
**Topics**: documentation, core | **Trusted**: True

mestamp': ts, 'record': record}, f, ensure_ascii=False, indent=2)
        return {'delivered': False, 'via': 'docs/context', 'snapshot': str(snapshot_path)}
    except Exception as e:
        return {'delivered': False, 'via': 'error', 'error': str(e)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Snapshot runtime context to docs/context")
    parser.add_argument("phase", help="Name of the engine phase (e.g. gaps, planning)")
    parser.add_argument("payload_file", nargs="?", help="Optional JSON file with payload to snapshot")
    args = parser.parse_args()

    payload = {}
    if args.payload_file:
        try:
            with open(args.payload_file, "r", encoding="utf-8") as pf:
                payload = json.load(pf)
        except Exception:
            payload = {"error": "failed to load payload file"}

    result = snapshot_context(args.phase, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


---
## 2026-01-03T01:45:18.752346 | ID: 5156b47e
**Topics**: documentation, core | **Trusted**: True

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class ContextUpdateRequiresConfirmation(Exception):
    pass


def _read_constitution(path: str = "docs/MITHALY_CONSTITUTION.md") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _is_phase_permitted(phase_name: str) -> bool:
    """Naive check: if the phase name appears in the constitution text,
    consider it permitted. This is intentionally conservative: absence means
    "requires confirmation".
    """
    text = _read_constitution()
    if not text:
        return False
    return phase_name in text


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def snapshot_context(phase_name: str, payload: dict, docs_dir: str = "docs/context") -> dict:
    """Write a snapshot of `payload` to `docs/context/current_context.json` and
    a timestamped snapshot file. Append an entry to `docs/context/history.md`.

    Behavior:
    - Always write non-destructive snapshots.
    - If the constitution does not explicitly permit the phase, the function
      returns `{'requires_confirmation': True}` and records that in the history.

    Returns a dict with keys `ok` or `requires_confirmation` and metadata.
    """
    base = Path(docs_dir)
    _ensure_dir(base)

    ts = datetime.now(timezone.utc).isoformat()
    current = {
        "phase": phase_name,
        "timestamp": ts,
        "payload": payload,
    }

    current_path = base / "current_context.json"
    snapshot_path = base / f"snapshot_{phase_name}_{ts.replace(':','-')}.json"

    # Write current context (overwrites safely)
    with open(current_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    # Write a timestamped snapshot for audit/history
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    permitted = _is_phase_permitted(phase_name)

    history_path = base / "history.md"
    entry_lines = [
        f"- **{ts}** — Phase: **{phase_name}**",
        f"  - permitted: {str(permitted)}",
        f"  - snapshot: {snapshot_path.name}",
        "",
    ]
    with open(history_path, "a", encoding="utf-8") as h:
        h.write("\n".join(entry_lines) + "\n")

    if not permitted:
        return {"requires_confirmation": True, "snapshot": str(snapshot_path), "current": str(current_path)}

    return {"ok": True, "snapshot": str(snapshot_path), "current": str(current_path)}


def deliver_record(record: dict, prefer_feedback: bool = True) -> dict:
    """Attempt to deliver `record` permanently via `FeedbackLoop.persist_to_kb`.

    If `prefer_feedback` is True, try to import and call FeedbackLoop.persist_to_kb.
    On failure, fall back to writing the record as a snapshot under `docs/context`.

    Returns a dict describing the outcome: `{'delivered': bool, 'via': 'feedback'|'docs/context', ...}`
    """
    if prefer_feedback:
        try:
            try:
                from mithaly.core.feedback.feedback_loop import FeedbackLoop as _FL
            except Exception:
                from src.mithaly.core.feedback.feedback_loop import FeedbackLoop as _FL
            fl = _FL()
            ok = False
            try:
                ok = bool(fl.persist_to_kb(record))
            except Exception:
                ok = False
            if ok:
                return {'delivered': True, 'via': 'feedback'}
        except Exception:
            # feedback not available or failed — fall through to docs/context
            pass

    # fallback: write to docs/context as a timestamped snapshot
    base = Path("docs/context")
    _ensure_dir(base)
    ts = datetime.now(timezone.utc).isoformat()
    snapshot_path = base / f"delivered_record_{ts.replace(':','-')}.json"
    try:
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump({'ti

---
## 2026-01-03T01:45:18.249833 | ID: 0254c13c
**Topics**: documentation, core | **Trusted**: True

"""KnowledgeManager - The Central Nervous System of Mithaly's Memory.

This module implements the "Hybrid Memory" architecture:
1.  **Source of Truth**: A JSONL ledger (`knowledge.jsonl`) storing all knowledge with metadata.
2.  **Search Index**: ChromaDB for semantic retrieval.
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from mithaly.core.memory.vector_store import VectorStore
except ImportError:
    # Local import fallback if running as script
    import sys
    sys.path.append(os.getcwd() + '/src')
    from mithaly.core.memory.vector_store import VectorStore

class KnowledgeManager:
    """Manages the lifecycle of knowledge: Logging, Indexing, and Retrieval."""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.ledger_path = os.path.join(project_root, "docs/context/knowledge.jsonl")
        self.vector_store = VectorStore()
        
        # Ensure context dir exists
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)

    def log_knowledge(self, 
                      content: str, 
                      topics: List[str], 
                      provenance: str = "system", 
                      trusted: bool = True,
                      metadata: Dict[str, Any] = None) -> str:
        """
        Log a piece of knowledge to the ledger and index it.
        Returns the Record ID.
        """
        record_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        record = {
            "id": record_id,
            "ts": timestamp,
            "topics": topics,
            "content": content,
            "provenance": provenance,
            "trusted": trusted,
            "metadata": metadata or {}
        }

        # 1. Write to Ledger (JSONL)
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            print(f"INFO: Logged knowledge record {record_id} to ledger.")
        except Exception as e:
            print(f"ERROR: Failed to write to ledger: {e}")
            return None

        # 2. Index in VectorStore (if trusted or desired)
        # We generally index everything so we can find it, but maybe we filter queries later.
        if self.vector_store:
            # Metadata for Chroma
            v_meta = {
                "source": "knowledge_ledger",
                "record_id": record_id,
                "topics": ",".join(topics),
                "trusted": str(trusted),
                "provenance": provenance
            }
            # Add topic to content for better semantic match
            v_content = f"Topics: {', '.join(topics)}\nContent: {content}"
            self.vector_store.add_documents([v_content], [v_meta])

        return record_id

    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search for knowledge. 
        Returns list of records (either from VectorDB or fetched from Ledger if needed).
        For now, returns the content string from VectorDB to save IO.
        """
        if not self.vector_store:
            return []
            
        # Raw docs from Chroma
        docs = self.vector_store.search(query, n_results)
        # TODO: In full implementation, we might fetch the full JSON from ledger using ID.
        # For now, the vector store content is sufficient context.
        return docs


---
## 2026-01-03T01:45:17.771740 | ID: ab7bc51f
**Topics**: documentation, core | **Trusted**: True

"""VectorStore - Adapter for Semantic Memory (RAG) using ChromaDB.

This component manages the storage and retrieval of semantic context.
It uses ChromaDB's default local embedding model (all-MiniLM-L6-v2).
"""
import os
import uuid
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

class VectorStore:
    """Manages semantic memory using ChromaDB."""

    def __init__(self, persistence_path: str = "docs/knowledge/chroma_db", collection_name: str = "mithaly_memory"):
        self.client = None
        self.collection = None
        
        if not chromadb:
            print("WARN: 'chromadb' not installed. RAG disabled.")
            return

        try:
            # Ensure directory exists
            os.makedirs(persistence_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=persistence_path)
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            print(f"ERROR: Failed to initialize ChromaDB: {e}")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]] = None):
        """Add documents to the vector store."""
        if not self.collection:
            return

        count = len(documents)
        ids = [str(uuid.uuid4()) for _ in range(count)]
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in range(count)]
            
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"INFO: Added {count} documents to memory.")
        except Exception as e:
            print(f"ERROR: Failed to add documents: {e}")

    def search(self, query: str, n_results: int = 3) -> List[str]:
        """Search for relevant documents."""
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            # results['documents'] is a list of lists (one per query)
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"ERROR: Vector search failed: {e}")
            return []


---
## 2026-01-03T01:45:17.328468 | ID: b37a321a
**Topics**: documentation, core | **Trusted**: True

 'text' not in data and isinstance(initial_data, str):
            data = {'text': initial_data}
            
        print("Starting LangGraph Lifecycle...")

        # Initialize MCP if available
        import asyncio
        if self.mcp_client:
            # Helper to run async connect in sync context (since run_lifecycle is sync for now)
            pass 
            
        # Setup thread for checkpointer
        config = {"configurable": {"thread_id": "cli-session-1"}}
        
        # Inject clients if available
        if self.ollama_client:
            config['configurable']['ollama_client'] = self.ollama_client
        if self.mcp_client:
             config['configurable']['mcp_client'] = self.mcp_client
        
        # Run graph
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


---
## 2026-01-03T01:45:16.883924 | ID: efee0229
**Topics**: documentation, core | **Trusted**: True

   print("--- [Node] Feedback ---")
    try:
        from mithaly.core.feedback.feedback_loop import FeedbackLoop
    except ImportError:
        try:
            from src.mithaly.core.feedback.feedback_loop import FeedbackLoop
        except ImportError:
            print("WARN: FeedbackLoop not found.")
            return {}

    try:
        fl = FeedbackLoop()
        fb_out = fl.process(state)
        return {'feedback': fb_out.get('feedback') if isinstance(fb_out, dict) else None}
    except Exception as e:
        print(f"ERROR: FeedbackLoop failed: {e}")
        return {}

# --- Conditional Logic ---

def check_clarification(state: AgentState) -> str:
    if state.get('clarification_questions'):
        return "clarify"
    return "policy"

def check_inflection(state: AgentState) -> str:
    inflect = state.get('inflection', {})
    if inflect.get('triggered'):
        if state.get('non_interactive'):
            return "end" # Halt on inflection if non-interactive
        # In a real LangGraph app, we would use interrupt. 
        # Here we simulate the legacy interactive prompt behavior 
        # but cleaner would be to allow user to resume. 
        pass
    return "planning"

# --- Graph Construction ---

class BuildEngine:
    def __init__(self, plan: Dict = None, project_path: str = '.', comm_hub=None):
        self.project_path = project_path
        self.comm_hub = comm_hub
        # Initialize Graph
        self.workflow = StateGraph(AgentState)
        
        # Add Nodes
        self.workflow.add_node("retrieve", node_retrieve)
        self.workflow.add_node("gaps", node_gaps)
        self.workflow.add_node("clarify", node_clarification)
        self.workflow.add_node("policy", node_policy)
        self.workflow.add_node("planning", node_planning)
        self.workflow.add_node("execution", node_execution)
        self.workflow.add_node("feedback", node_feedback)

        # Add Edges
        self.workflow.add_edge(START, "retrieve")
        self.workflow.add_edge("retrieve", "gaps")
        
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
        
        # Conditional: Policy -> Planning (unless Inflection halts it)
        self.workflow.add_conditional_edges(
            "policy",
            check_inflection,
            {
                "end": END,         # Halt if non-interactive inflection
                "planning": "planning"
            }
        )

        self.workflow.add_edge("planning", "execution")
        self.workflow.add_edge("execution", "feedback")
        self.workflow.add_edge("feedback", END)

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
        # Ensure 'text' key exists
        if

---
## 2026-01-03T01:45:16.427110 | ID: 0a92fb70
**Topics**: documentation, core | **Trusted**: True

bes
        except Exception:
            pass

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
    
    return updates

def node_planning(state: AgentState, config: RunnableConfig) -> AgentState:
    """Run ExecutionPlanner. Uses Smart LLM."""
    print("--- [Node] Planning ---")
    
    ollama = get_ollama_client(config)
    if ollama:
        # LLM Mode (Smart)
        gaps = state.get('gap_analysis')
        policy = state.get('policy_constraints')
        text = state.get('text')
        
        prompt = f"""
        You are the Planner. 
        Request: "{text}"
        Gaps: {gaps}
        Policies: {policy}
        
        Create a detailed execution plan as a list of steps.
        Return JSON: {{ "plan": [list of strings] }}
        """
        response = ollama.chat([{"role": "user", "content": prompt}], task_type="smart")
        content = response.get("content", "")
        
        import json
        plan_data = []
        try:
            clean = content.replace("```json", "").replace("```", "").strip()
            plan_data = json.loads(clean).get("plan", [])
        except Exception:
            plan_data = [{"description": "Raw Plan: " + content}]
            
        return {'plan': plan_data}

    else:
        # Legacy
        try:
            from mithaly.core.planning.execution_planner import ExecutionPlanner
        except ImportError:
            try:
                from src.mithaly.core.planning.execution_planner import ExecutionPlanner
            except ImportError:
                print("WARN: ExecutionPlanner not found.")
                return {}

        try:
            ep = ExecutionPlanner()
            plan_out = ep.process(state)
            return {'plan': plan_out.get('plan') if isinstance(plan_out, dict) else plan_out}
        except Exception as e:
            print(f"ERROR: ExecutionPlanner failed: {e}")
            return {}

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
        return {'execution_results': response.get("content")}

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
            return {'execution_results': exec_out.get('execution_results') if isinstance(exec_out, dict) else None}
        except Exception as e:
            print(f"ERROR: SafeExecutor failed: {e}")
            return {}

def node_feedback(state: AgentState) -> AgentState:
    """Run FeedbackLoop."""
 

---
## 2026-01-03T01:45:15.973715 | ID: c0865fdf
**Topics**: documentation, core | **Trusted**: True

return {
            "gap_analysis": gaps_data,
            "clarification_questions": gaps_data.get("clarification_questions")
        }
    else:
        # Legacy Mode (unchanged)
        # ...
        try:
            from mithaly.core.gaps.gap_analyzer import GapAnalyzer
        except ImportError:
            try:
                from src.mithaly.core.gaps.gap_analyzer import GapAnalyzer
            except ImportError:
                return {}

        current = {k: v for k, v in state.items() if v is not None}
        if 'text' in current and 'input' not in current:
            current['input'] = current['text']
            
        try:
            ga = GapAnalyzer()
            ga_out = ga.process(current)
            return {
                'gap_analysis': ga_out.get('gap_analysis'),
                'clarification_questions': ga_out.get('clarification_questions'),
                'text': ga_out.get('text', state.get('text'))
            }
        except Exception as e:
            print(f"ERROR: GapAnalyzer failed: {e}")
            return {}

# ... (Other nodes unchanged)

# --- Graph Construction ---

class BuildEngine:
    def __init__(self, plan: Dict = None, project_path: str = '.', comm_hub=None):
        self.project_path = project_path
        self.comm_hub = comm_hub
        # Initialize Graph
        self.workflow = StateGraph(AgentState)
        
        # Add Nodes
        self.workflow.add_node("retrieve", node_retrieve) # NEW
        self.workflow.add_node("gaps", node_gaps)
        self.workflow.add_node("clarify", node_clarification)
        self.workflow.add_node("policy", node_policy)
        self.workflow.add_node("planning", node_planning)
        self.workflow.add_node("execution", node_execution)
        self.workflow.add_node("feedback", node_feedback)

        # Add Edges
        self.workflow.add_edge(START, "retrieve") # CHANGED from "gaps"
        self.workflow.add_edge("retrieve", "gaps") # NEW Edge
        
        # ... (rest of edges)
        self.workflow.add_conditional_edges(
            "gaps",
            check_clarification,
            {
                "clarify": "clarify",
                "policy": "policy"
            }
        )
# ...

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
            updates['probes'] = pro

---
## 2026-01-03T01:45:15.476280 | ID: 8f629235
**Topics**: documentation, core | **Trusted**: True

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
    print("ERROR: LangGraph not found. Please install: pip install langgraph langchain-core")
    sys.exit(1)

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
            # print snippet
            print(f"DEBUG: Record 1: {docs[0][:100]}...")
        else:
            print("INFO: No relevant knowledge found.")
        return {'context_docs': docs}
    except Exception as e:
        print(f"ERROR: Retrieval failed: {e}")
        return {}

def node_gaps(state: AgentState, config: RunnableConfig) -> AgentState:
    """Run GapAnalyzer to analyze the input request. Uses Fast LLM."""
    print("--- [Node] Gaps ---")
    
    ollama = get_ollama_client(config)
    user_input = state.get('text') or ""
    context = state.get('context_docs') or []
    
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
        
        Return JSON with keys: 'gaps', 'clarification_questions'.
        """
        response = ollama.chat([{"role": "user", "content": prompt}], task_type="fast")
        content = response.get("content", "")
        # ... (rest of parsing logic same as before)
        import json
        gaps_data = {}
        try:
            clean = content.replace("```json", "").replace("```", "").strip()
            gaps_data = json.loads(clean)
        except Exception:
            print("WARN: Failed to parse LLM Gaps JSON.")
            gaps_data = {"raw_analysis": content}
            
        

---
## 2026-01-03T01:45:15.014150 | ID: bcde07a4
**Topics**: documentation, core | **Trusted**: True

"""Simple LayerRegistry for registering and discovering Mithaly layers.

Layers can register themselves (or be registered by the package initializer).
The generator (project-generator) can query the registry to find available
capabilities without hard-coding class locations.
"""
from typing import Dict, Type, Optional
import importlib
import pkgutil


class LayerRegistry:
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, layer_cls: Type):
        cls._registry[name] = layer_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        return cls._registry.get(name)

    @classmethod
    def list(cls):
        return list(cls._registry.keys())

    @classmethod
    def collect_probes(cls, data=None):
        """Instantiate registered layer classes and collect their probe() output.

        Returns a dict mapping layer name -> probe dict (if available).
        """
        probes = {}
        for name, layer_cls in cls._registry.items():
            try:
                inst = layer_cls()
                if hasattr(inst, 'probe'):
                    probes[name] = inst.probe(data)
                else:
                    probes[name] = None
            except Exception:
                probes[name] = None
        return probes

    @classmethod
    def autodiscover(cls, package: str = 'mithaly.core'):
        """Import submodules under `package` to trigger module-level registrations.

        This is a non-destructive fallback that simply imports discovered
        submodules so that any `@register_layer` decorators run on import.
        """
        try:
            pkg = importlib.import_module(package)
        except Exception:
            return

        path = getattr(pkg, '__path__', None)
        if not path:
            return

        for finder, name, ispkg in pkgutil.walk_packages(path, package + '.'):
            try:
                importlib.import_module(name)
            except Exception:
                # ignore import-time errors during discovery
                pass


def register_layer(name: str):
    def _decorator(layer_cls: Type):
        LayerRegistry.register(name, layer_cls)
        return layer_cls
    return _decorator


---
## 2026-01-03T01:45:14.566127 | ID: 7b5d635e
**Topics**: documentation, core | **Trusted**: True

'utf-8') as f:
                        existing = json.load(f) or []
                except Exception:
                    existing = []
            else:
                existing = []
            existing.append(entry)
            with open(pending, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception:
            # non-fatal: continue even if writing the pending file fails
            pass

        # Dispatch to layers that expose `analyze_error`
        analyses = {}
        try:
            from mithaly.core.registry import LayerRegistry as _LR
        except Exception:
            try:
                from src.mithaly.core.registry import LayerRegistry as _LR
            except Exception:
                _LR = None

        if _LR is not None:
            for name in _LR.list():
                try:
                    layer_cls = _LR.get(name)
                    inst = layer_cls()
                    if hasattr(inst, 'analyze_error'):
                        try:
                            res = inst.analyze_error(error_report)
                            analyses[name] = res
                        except Exception as e:
                            analyses[name] = {'error': str(e)}
                except Exception:
                    analyses[name] = {'error': 'failed to instantiate layer'}

        # Simple heuristics to decide recommendation
        recommendation = 'defer'
        try:
            # if any analysis marks as 'confident' or 'actionable', escalate
            for a in analyses.values():
                if isinstance(a, dict) and a.get('action') == 'auto_resolve':
                    recommendation = 'auto_resolve'
                    break
                if isinstance(a, dict) and a.get('action') == 'requires_admin':
                    recommendation = 'requires_admin'
                    break
        except Exception:
            recommendation = 'defer'

        ticket = {
            'ticket_id': f"err-{int(__import__('time').time())}",
            'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'recommendation': recommendation,
            'analyses': analyses,
            'trusted': False,
        }

        # write ticket record for audit
        try:
            tickets = base / 'analysis_tickets.json'
            if tickets.exists():
                try:
                    with open(tickets, 'r', encoding='utf-8') as f:
                        tlist = json.load(f) or []
                except Exception:
                    tlist = []
            else:
                tlist = []
            tlist.append(ticket)
            with open(tickets, 'w', encoding='utf-8') as f:
                json.dump(tlist, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # If recommendation suggests auto-resolve, prefer to persist via FeedbackLoop
        try:
            from mithaly.core.utils.context_updater import deliver_record as _deliver
        except Exception:
            try:
                from src.mithaly.core.utils.context_updater import deliver_record as _deliver
            except Exception:
                _deliver = None

        if _deliver is not None and ticket.get('recommendation') == 'auto_resolve':
            try:
                deliver_res = _deliver(ticket, prefer_feedback=True)
                ticket['delivered'] = deliver_res
            except Exception:
                ticket['delivered'] = {'delivered': False, 'via': 'error', 'error': 'deliver_failed'}

        return ticket


---
## 2026-01-03T01:45:14.069392 | ID: bd2f0370
**Topics**: documentation, core | **Trusted**: True

se None
        techs = None
        try:
            techs = gap.get('technical_gaps') if isinstance(gap, dict) else None
        except Exception:
            techs = None

        if techs:
            combined = ' '.join(map(str, techs)).lower()
            if 'db' in combined or 'database' in combined or 'postgres' in combined or 'mysql' in combined:
                constraints['requires_db'] = True
            if 'docker' in combined or 'container' in combined:
                constraints['requires_container_runtime'] = True

        text = payload.get('text') if isinstance(payload, dict) else None
        if isinstance(text, str):
            t = text.lower()
            if 'third-party api' in t or 'external api' in t or 'oauth' in t:
                constraints['requires_network_access'] = True

        # Inspect probes (if any) and derive constraints from reported requirements
        probes = None
        try:
            probes = payload.get('probes') if isinstance(payload, dict) else None
        except Exception:
            probes = None

        if isinstance(probes, dict):
            for pname, probe in probes.items():
                if not isinstance(probe, dict):
                    continue
                reqs = probe.get('requirements') or {}
                # normalize string values
                for k, v in reqs.items():
                    sval = v
                    if isinstance(v, str):
                        sval = v.lower()
                    # map common requirement keys to policy flags
                    if k in ('requires_db',) and sval in (True, 'yes', 'true'):
                        constraints['requires_db'] = True
                    if k in ('requires_container_runtime',) and sval in (True, 'yes', 'true'):
                        constraints['requires_container_runtime'] = True
                    if k in ('requires_network',) and sval in (True, 'yes', 'true'):
                        constraints['requires_network_access'] = True

                attrs = probe.get('attributes') or {}
                if attrs.get('sensitive') is True:
                    # flag for human review and potential inflection
                    constraints['sensitive_project_review'] = True
                    constraints['inflection_point'] = True

        # Inject Constitutional Hard Constraints
        constitution = self._load_constitution_core()
        if constitution:
            constraints['constitutional_constraints'] = {
                'source': 'MITHALY_CONSTITUTION.md',
                'type': 'HARD_CONSTRAINT',
                'content': constitution
            }

        return {'policy_constraints': constraints}

    def report_error(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        """Receive an error report and convert it into an analysis request.

        Behavior:
        - Persist the report non-destructively under `docs/context/errors_pending.json`.
        - Attempt to dispatch the report to registered layers that implement
          `analyze_error(report) -> dict` and collect their analysis outputs.
        - Return an `analysis_ticket` describing the dispatched analyses and a
          recommended action: `defer`, `requires_admin`, or `auto_resolve`.

        This method deliberately does NOT write to the Knowledge Base. callers
        should honor the returned recommendation.
        """
        # ensure docs/context exists and append the pending error
        import pathlib
        base = pathlib.Path('docs') / 'context'
        base.mkdir(parents=True, exist_ok=True)
        pending = base / 'errors_pending.json'

        entry = {
            'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'report': error_report,
        }

        # Append to pending list (safe, non-destructive)
        try:
            if pending.exists():
                try:
                    with open(pending, 'r', encoding=

---
## 2026-01-03T01:45:13.575295 | ID: 8e98fa12
**Topics**: documentation, core | **Trusted**: True

"""PolicyEnforcer for Mithaly.

Provides a small, testable policy-enforcement component that evaluates a
payload (usually produced by `GapAnalyzer`) and returns `policy_constraints`.
By default it attempts to load a policy file from the workspace
`docs/knowledge/policies/policies.yaml` (or `policies.json`) unless
explicit `policies` are provided to the constructor.
"""
import os
import json
from typing import Dict, Any, Optional


def _load_policies_from_file(path: str) -> Optional[Dict[str, Any]]:
    """Try to load policies from YAML (if PyYAML is installed) or JSON.

    Returns a dict or None if file not found or parsing failed.
    """
    if not os.path.exists(path):
        return None
    # Prefer YAML if available
    try:
        import yaml  # type: ignore
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback to JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None


class PolicyEnforcer:
    def __init__(self, policies: Dict[str, Any] = None, policy_path: str = None):
        # If policies explicitly provided, use them.
        if policies is not None:
            self.policies = policies
            return

        # Allow overriding policy file path via env var or constructor
        candidate = policy_path or os.environ.get('MITHALY_POLICY_PATH')
        if candidate:
            loaded = _load_policies_from_file(candidate)
            self.policies = loaded or {}
            return

        # Default locations under docs/knowledge/policies
        base = os.getcwd()
        defaults = [
            os.path.join(base, 'docs', 'knowledge', 'policies', 'policies.yaml'),
            os.path.join(base, 'docs', 'knowledge', 'policies', 'policies.yml'),
            os.path.join(base, 'docs', 'knowledge', 'policies', 'policies.json'),
        ]
        loaded = None
        for p in defaults:
            loaded = _load_policies_from_file(p)
            if loaded is not None:
                break

        self.policies = loaded or {}

    def _load_constitution_core(self) -> Optional[str]:
        """Load the 'Immutable Core' section from the constitution."""
        try:
            # Try to locate MITHALY_CONSTITUTION.md
            candidates = [
                os.path.join(os.getcwd(), 'docs', 'MITHALY_CONSTITUTION.md'),
                os.path.join(os.getcwd(), 'MITHALY_CONSTITUTION.md'),
            ]
            path = None
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break
            
            if not path:
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract 'Mithaly — ميثاق الثوابت' or relevant core section
            # For now, we take the whole file or a significant chunk if markers exist.
            # The gaps analysis requested "full text" or "summary" as hard constraint.
            # We will return the whole text to be safe as the "Core".
            return content
        except Exception:
            return None


    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate payload and return a dict with `policy_constraints`.

        This implementation is intentionally small and rule-based. It looks
        for common technical gap indicators and returns simple constraints.
        The returned constraints are merged with loaded policies (policies as base,
        detected constraints override when present).
        """
        constraints: Dict[str, Any] = {}

        # Start from configured policies as defaults
        if isinstance(self.policies, dict):
            constraints.update(self.policies)

        # Inspect gap analysis for indicators
        gap = payload.get('gap_analysis') if isinstance(payload, dict) el

---
## 2026-01-03T01:45:12.955224 | ID: 9f47e432
**Topics**: documentation, core | **Trusted**: True

# Core package initializer: import known layer modules to trigger registration

# Import order: keep lightweight to avoid heavy side-effects at import time.
from .gaps import gap_analyzer  # registers 'gaps'
from .planning import execution_planner  # registers 'planning'
from .execution import safe_executor  # registers 'execution'
from .feedback import feedback_loop  # registers 'feedback'

# Optionally perform autodiscovery as fallback (non-destructive)
try:
    from .registry import LayerRegistry
    # perform autodiscovery to catch any additional modules
    LayerRegistry.autodiscover('mithaly.core')
except Exception:
    pass


---
