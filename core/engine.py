"""
core/engine.py
Compatibility shim: expose BuildEngine at `core.engine.BuildEngine` for tests
This implementation is a lightweight build executor adapted from
`data/experience/i-project/modules/build_engine.py`.
"""
import time
import os
import shlex
import shutil
import subprocess
from typing import Dict
from specialists.debugger import DebuggerSpecialist


class BuildError(Exception):
    def __init__(self, message: str, step: Dict = None):
        super().__init__(message)
        self.step = step


class BuildEngine:
    def __init__(self, plan: Dict, project_path: str, comm_hub=None, correction_unit=None, rules_enforcer=None):
        self.plan = plan
        self.project_path = project_path
        self.current_phase = None
        self.comm_hub = comm_hub
        self.correction_unit = correction_unit
        self.rules_enforcer = rules_enforcer
        self.metrics = {}
        self.specialists = {}
        # Register default specialists
        self.register_specialist('debugger', DebuggerSpecialist())
        # Safe coordinator instantiation (step 1 of integration)
        try:
            from core.task_coordinator import TaskCoordinator
            # provide engine reference for potential use by coordinator
            # TaskCoordinator in this project is lightweight and accepts no required args,
            # but we keep this pattern in case implementations expect an engine ref.
            try:
                self.coordinator = TaskCoordinator(engine_ref=self)
            except TypeError:
                # older shim may not accept engine_ref; fall back to no-arg constructor
                self.coordinator = TaskCoordinator()
        except Exception:
            # If coordinator isn't available, keep backward-compatible behavior
            self.coordinator = None

    def register_specialist(self, name: str, specialist):
        """Register a specialist by name."""
        self.specialists[name] = specialist
        # If a TaskCoordinator is present, register the specialist there as well
        try:
            if getattr(self, 'coordinator', None) is not None and hasattr(self.coordinator, 'register'):
                try:
                    self.coordinator.register(name, specialist)
                except Exception:
                    # registration to coordinator failed; ignore to preserve backward compatibility
                    pass
        except Exception:
            pass

    def execute(self) -> Dict:
        start = time.time()
        result = {
            'project_id': self.plan.get('project_id'),
            'status': 'UNKNOWN',
            'phases': [],
        }

        for phase in self.plan.get('phases', []):
            self.current_phase = phase.get('name')
            if self.comm_hub:
                self.comm_hub.publish('build.phase.started', {'phase': self.current_phase, 'project': self.plan.get('project_id')})

            try:
                # execute all steps in the phase
                for step in phase.get('steps', []):
                    try:
                        self._execute_step(step)
                    except BuildError as e:
                        # handle and possibly retry the same step
                        handled = self._handle_build_error(e)
                        if handled:
                            # retry once after auto-fix
                            self._execute_step(e.step)
                        else:
                            raise

                result['phases'].append({'name': self.current_phase, 'status': 'COMPLETED'})
            except BuildError as e:
                phase_entry = {'name': self.current_phase, 'status': 'FAILED', 'error': str(e)}
                # If the BuildError.step contains a debug report, include it in the phase result
                try:
                    dbg = (e.step or {}).get('_debug_report') if isinstance(e.step, dict) else None
                    if dbg:
                        phase_entry['debug_report'] = dbg
                except Exception:
                    pass
                result['phases'].append(phase_entry)
                result['status'] = 'FAILED'
                break

            if self.comm_hub:
                self.comm_hub.publish('build.phase.completed', {'phase': self.current_phase, 'project': self.plan.get('project_id')})

        if result['status'] != 'FAILED':
            result['status'] = 'SUCCESS'

        # Sync final success
        try:
            from mithaly_management.scripts.state_manager import update_persistent_state
            update_persistent_state('completed', result['status'], {'project': self.plan.get('project_id')})
        except ImportError:
            pass

        result['duration'] = time.time() - start
        return result

    def _handle_build_error(self, error: BuildError) -> bool:
        """Handle a BuildError. Returns True if error was auto-handled and a retry should be attempted."""
        # Sync error state
        try:
            from mithaly_management.scripts.state_manager import update_persistent_state
            update_persistent_state('error', 'handling', {'error': str(error)})
        except ImportError:
            pass

        # Placeholder for correction/retry/human-in-loop logic.
        try:
            if self.correction_unit:
                correction = self.correction_unit.suggest_fix(error=error, context={'project_type': self.plan.get('project_type'), 'phase': self.current_phase, 'command': (error.step or {}).get('run') if isinstance(error, BuildError) else None})
                if correction.get('auto_fixable'):
                    ok = self.correction_unit.apply_fix(correction, self.project_path)
                    if ok:
                        # applied a fix successfully; inform via comm_hub and request a retry
                        if self.comm_hub:
                            self.comm_hub.publish('build.auto_correction', {'fix': correction, 'project': self.project_path})
                        return True
        except Exception:
            pass

        # If not auto-fixable or auto-fix failed, try retry/backoff logic (not implemented here)
        if self.comm_hub:
            self.comm_hub.publish('build.failure.human_needed', {'error': str(error), 'project': self.project_path})
        return False

    def _execute_step(self, step: Dict):
        """Execute a single build step dict with key 'run' and optional 'timeout'.

        This method is defensive: if required tool is missing (e.g., `npm`) it will
        attempt reasonable fallbacks or emit a warning and continue (so demos work
        on systems without all toolchains).
        """
        cmd = step.get('run')
        if not cmd:
            return None

        # Sync step start
        try:
            from mithaly_management.scripts.state_manager import update_persistent_state
            update_persistent_state(self.current_phase or 'executing', 'running_step', {'command': cmd})
        except ImportError:
            pass

        timeout = step.get('timeout', 300)

        # check if the executable exists (first token)
        parts = shlex.split(cmd)
        exe = parts[0] if parts else None
        # detect pytest invocation for special handling (e.g., no-tests exit code)
        try:
            is_pytest = 'pytest' in cmd or any('pytest' in str(p) for p in (parts or []))
        except Exception:
            is_pytest = 'pytest' in cmd
        if exe and shutil.which(exe) is None:
            # handle common npm case gracefully for demos
            if exe == 'npm':
                node_modules = os.path.join(self.project_path, 'node_modules')
                if os.path.exists(node_modules):
                    # assume dependencies are satisfied
                    msg = f"Tool 'npm' not found; skipping install because node_modules exists"
                    print('WARN:', msg)
                    if self.comm_hub:
                        self.comm_hub.publish('build.warning', {'message': msg, 'project': self.project_path})
                    return None

                msg = f"Tool 'npm' not found; attempting to continue without install (demo mode)"
                print('WARN:', msg)
                if self.comm_hub:
                    self.comm_hub.publish('build.warning', {'message': msg, 'project': self.project_path})
                return None

            # For other missing tools, emit warning and skip step to keep demo flow
            msg = f"Tool '{exe}' not available; skipping step '{cmd}'"
            print('WARN:', msg)
            if self.comm_hub:
                self.comm_hub.publish('build.warning', {'message': msg, 'project': self.project_path})
            return None

        # prepare environment: merge provided env with current
        env = os.environ.copy()
        if isinstance(step.get('env'), dict):
            env.update(step.get('env'))

            # If this step is running tests via pytest and the project has no tests folder,
            # optionally skip the step to avoid failing builds for projects that don't include tests.
            try:
                from pathlib import Path as _Path
                # Make skip behavior configurable via environment variable.
                skip_env = os.environ.get('SKIP_TESTS_IF_EMPTY', 'true').lower()
                skip_if_empty = skip_env in ('1', 'true', 'yes')

                tests_path = _Path(self.project_path) / 'tests'
                # Detect pytest invocations robustly (cmd string or tokenized parts)
                is_pytest = False
                try:
                    is_pytest = 'pytest' in cmd or any('pytest' in str(p) for p in (parts or []))
                except Exception:
                    is_pytest = 'pytest' in cmd

                if skip_if_empty and is_pytest and not tests_path.exists():
                    msg = f"No tests found at {tests_path}; skipping test step (SKIP_TESTS_IF_EMPTY={skip_env})"
                    print('WARN:', msg)
                    if self.comm_hub:
                        self.comm_hub.publish('build.warning', {'message': msg, 'project': self.project_path})
                    return None
            except Exception:
                # If anything goes wrong while checking for tests, fall back to running the step.
                pass

            print(f"⏳ Running: {cmd}")
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )

            # log metric
            self.metrics[f"{self.current_phase}:{cmd}"] = {
                'return_code': proc.returncode,
                'stdout': proc.stdout[:2000],
                'stderr': proc.stderr[:2000],
            }

            if proc.returncode != 0:
                # Special-case: pytest returns 5 when no tests were collected.
                # Treat this as non-fatal (acceptable) so that projects without tests
                # don't cause the whole build to fail. This preserves stricter
                # behavior for other failures while being permissive for empty test suites.
                if is_pytest and proc.returncode == 5:
                    msg = "NOTE: pytest returned code 5 (no tests collected); treating as success"
                    print(msg)
                    if self.comm_hub:
                        self.comm_hub.publish('build.warning', {'message': msg, 'project': self.project_path})
                    # consider the step completed
                    return proc
                # Attempt to route debug task via TaskCoordinator if available.
                # If TaskCoordinator isn't available or routing fails, fall back
                # to existing DebuggerSpecialist behaviour to preserve backward
                # compatibility.
                try:
                    # Prefer the BuildEngine's coordinator instance if present
                    coordinator = getattr(self, 'coordinator', None)
                    if coordinator is None:
                        # Fallback: attempt to import and create a temporary coordinator
                        try:
                            from core.task_coordinator import TaskCoordinator
                            try:
                                coordinator = TaskCoordinator(engine_ref=self)
                            except TypeError:
                                coordinator = TaskCoordinator()
                        except Exception:
                            coordinator = None

                    failure_ctx = {'command': cmd, 'stdout': proc.stdout, 'stderr': proc.stderr}

                    routed = None
                    if coordinator is not None:
                        try:
                            routed = coordinator.route_task('debug', failure_ctx, context={'project': self.project_path, 'phase': self.current_phase}, specialists=self.specialists)
                        except Exception:
                            routed = None

                    if routed and isinstance(routed, dict):
                        # routed expected keys: diagnosis, suggestion, dry_apply
                        step = dict(step) if step is not None else {}
                        step.update({'_debug_report': {'diagnosis': routed.get('diagnosis'), 'suggestion': routed.get('suggestion'), 'dry_apply': routed.get('dry_apply')}})
                    else:
                        # Fall back to direct specialist API
                        debugger = self.specialists.get('debugger')
                        if debugger:
                            try:
                                diagnosis = debugger.analyze_failure(failure_ctx)
                            except TypeError:
                                diagnosis = debugger.analyze_failure(failure_ctx)
                            suggestion = debugger.suggest_patch(diagnosis)
                            dry_apply = debugger.apply_patch(suggestion, dry_run=True)
                            step = dict(step) if step is not None else {}
                            step.update({'_debug_report': {'diagnosis': diagnosis, 'suggestion': suggestion, 'dry_apply': dry_apply}})
                except Exception:
                    # ignore debugger/coordinator failures and propagate original build error
                    try:
                        debugger = self.specialists.get('debugger')
                        if debugger:
                            failure_ctx = {'command': cmd, 'stdout': proc.stdout, 'stderr': proc.stderr}
                            diagnosis = debugger.analyze_failure(failure_ctx)
                            suggestion = debugger.suggest_patch(diagnosis)
                            dry_apply = debugger.apply_patch(suggestion, dry_run=True)
                            step = dict(step) if step is not None else {}
                            step.update({'_debug_report': {'diagnosis': diagnosis, 'suggestion': suggestion, 'dry_apply': dry_apply}})
                    except Exception:
                        pass

                raise BuildError(f"Command failed: {cmd}\nExit: {proc.returncode}\nStderr: {proc.stderr}", step=step)

            print(f"✓ Completed: {cmd}")
            if proc.stdout:
                print(proc.stdout)
            return proc
        except subprocess.TimeoutExpired:
            raise BuildError(f"Timeout executing: {cmd}", step=step)
        except BuildError:
            raise
        except Exception as e:
            raise BuildError(f"Error executing {cmd}: {str(e)}", step=step)

