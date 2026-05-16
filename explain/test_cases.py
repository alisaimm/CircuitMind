import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from explain_module import explain_circuit

TEST_CASES = [
    {
        "label": "Basic LED Circuit",
        "input": {
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"]
        }
    },
    {
        "label": "Motor Control Circuit",
        "input": {
            "components": ["battery", "resistor", "transistor", "motor"],
            "connections": ["battery -> resistor -> transistor -> motor"]
        }
    },
    {
        "label": "Arduino Sensor Circuit",
        "input": {
            "components": ["power_supply", "arduino", "ldr", "resistor", "led"],
            "connections": [
                "power_supply -> arduino",
                "ldr -> resistor -> arduino",
                "arduino -> led"
            ]
        }
    },
    {
        "label": "LED Without Resistor",
        "input": {
            "components": ["battery", "led"],
            "connections": ["battery -> led"]
        }
    },
    {
        "label": "No Power Source",
        "input": {
            "components": ["resistor", "led"],
            "connections": ["resistor -> led"]
        }
    },
]

results = []
for test in TEST_CASES:
    output = explain_circuit(test["input"])
    results.append({
        "label":  test["label"],
        "input":  test["input"],
        "output": output
    })
output_path1 = "test_results.json"
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to {output_path}")
for r in results:
    warnings = r["output"].get("warnings", [])
    print(f"  {r['label']:30s} | warnings: {len(warnings)}")
print(output_path1)    
