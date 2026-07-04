import json
from export_module import export_module

#1: LED Circuit
led = '''{"circuit_name": "LED Circuit", "components": ["battery", "resistor", "led"], "connections": ["battery -> resistor -> led"]}'''

#2: Motor Circuit
motor = '''{"circuit_name": "Motor Circuit", "components": ["battery", "switch", "motor"], "connections": ["battery -> switch -> motor"]}'''

#3: Fan Circuit
fan = '''{"circuit_name": "Fan Circuit", "components": ["battery", "switch", "capacitor", "motor"], "connections": ["battery -> switch -> capacitor -> motor"]}'''

#4: Empty input
empty = ''

#5: Invalid JSON
invalid = 'not json at all'

#6: Solar Charging Circuit — verifies no component falls back to the "?" default value.
#   charge_controller legitimately maps to symbol "X" (subcircuit), so we do NOT do a
#   blanket "no X in netlist" check.  Instead we confirm:
#     a) The netlist contains none of the fallback "?" values that signal a missing map entry.
#     b) Components with real SPICE primitives (battery → V, solar_cell → V, diode → D)
#        appear in the netlist with their correct symbols.
solar = json.dumps({
    "circuit_name": "Solar Charging Circuit",
    "components":   ["solar_cell", "diode", "charge_controller", "battery"],
    "connections":  ["solar_cell -> diode -> charge_controller -> battery"],
})

# Running of all tests
results = []

for test in [led, motor, fan, empty, invalid]:
    result = export_module(test)
    results.append(result)
    print(json.dumps(result, ensure_ascii=True, indent=2))

# ── Test #6: Solar Charging Circuit ───────────────────────────────────────────
print("\n--- Test #6: Solar Charging Circuit (map-coverage check) ---")
solar_result = export_module(solar, export_format="spice")
results.append(solar_result)
print(json.dumps(solar_result, ensure_ascii=True, indent=2))

assert solar_result["status"] == "success", \
    f"Test #6 failed: expected status 'success', got {solar_result['status']!r}"

netlist = solar_result["spice_netlist"]

# (a) No fallback "?" values — every component must have a real entry in COMPONENT_VALUES.
assert "?" not in netlist, (
    "Test #6 failed: netlist contains '?' — at least one component is missing from "
    "COMPONENT_VALUES and fell back to the default.\n"
    f"Netlist:\n{netlist}"
)

# (b) Components with native SPICE primitives must appear with the correct symbol.
#     charge_controller → "X" is intentional (subcircuit) and is NOT checked here.
assert any(line.startswith("V") for line in netlist.splitlines()), (
    "Test #6 failed: no 'V' element found — solar_cell and/or battery are not "
    "mapped to the voltage-source symbol.\n"
    f"Netlist:\n{netlist}"
)
assert any(line.startswith("D") for line in netlist.splitlines()), (
    "Test #6 failed: no 'D' element found — diode is not mapped to the diode symbol.\n"
    f"Netlist:\n{netlist}"
)

print("Test #6 passed: solar_cell, diode, charge_controller, battery all resolved "
      "correctly (no '?' fallback values).")

#Save results to test_results.json
with open("test_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("\nAll tests done - saved to test_results.json")
