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
