
import sys
import os
import unittest

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from mithaly.core.adapter.generator_adapter import GeneratorAdapter
    from mithaly.core.registry import LayerRegistry
    # We might need to mock or register dummy layers if we want to test delegation,
    # but for structure verification, instantiation is enough.
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

class TestGeneratorAdapter(unittest.TestCase):
    def test_instantiation(self):
        adapter = GeneratorAdapter(generator_id="test_gen")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.generator_id, "test_gen")
        
    def test_status(self):
        adapter = GeneratorAdapter()
        status = adapter.get_status()
        self.assertEqual(status['status'], 'active')
        self.assertIn('connected_layers', status)

if __name__ == '__main__':
    unittest.main()
