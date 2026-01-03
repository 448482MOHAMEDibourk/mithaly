
import sys
import os

# Add src to python path to emulate package environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    from mithaly.core.policy import PolicyEnforcer
except ImportError:
    print("Could not import PolicyEnforcer from mithaly.core.policy")
    sys.exit(1)

def test_policy_constitution_injection():
    print("Running test_policy_constitution_injection...")
    
    # 1. Ensure constitution file exists or a dummy is created for testing
    constitution_path = os.path.join(os.getcwd(), 'docs', 'MITHALY_CONSTITUTION.md')
    if not os.path.exists(constitution_path):
        print(f"Constitution not found at {constitution_path}, skipping test or assuming failure.")
        # In a real environment we might fail, but here we can't create the file if it doesn't exist?
        # The user has it, so we expect it to exist.
        return False

    pe = PolicyEnforcer()
    payload = {'text': 'test project', 'gap_analysis': {}}
    
    result = pe.process(payload)
    
    constraints = result.get('policy_constraints', {})
    const_data = constraints.get('constitutional_constraints')
    
    if not const_data:
        print("FAIL: 'constitutional_constraints' not found in policy output.")
        return False
        
    print(f"SUCCESS: Found constitutional_constraints.")
    print(f"  Source: {const_data.get('source')}")
    print(f"  Type: {const_data.get('type')}")
    content_preview = const_data.get('content', '')[:50].replace('\n', ' ')
    print(f"  Content Preview: {content_preview}...")
    
    if "Immutable Core" not in const_data.get('content', '') and "ميثاق الثوابت" not in const_data.get('content', ''):
        print("WARN: Content does not look like the expected constitution.")
        
    return True

if __name__ == "__main__":
    if test_policy_constitution_injection():
        print("Test PASSED")
        sys.exit(0)
    else:
        print("Test FAILED")
        sys.exit(1)
