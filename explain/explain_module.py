"""
CircuitMind - Explain Module
explain/explain_module.py

Takes a circuit JSON and returns a human-readable explanation,
component details, current flow description, and any warnings.
"""

from typing import Any


# ── Component knowledge base ───────────────────────────────────────────────────

COMPONENT_DB: dict[str, dict] = {
    # Power
    "battery":       {"role": "power source",      "description": "provides electrical energy to the circuit"},
    "power_supply":  {"role": "power source",       "description": "supplies regulated DC voltage to the circuit"},
    "solar_cell":    {"role": "power source",       "description": "converts sunlight into electrical energy"},

    # Passive
    "resistor":      {"role": "current limiter",    "description": "limits and controls the flow of current"},
    "capacitor":     {"role": "energy storage",     "description": "stores and releases electrical energy"},
    "inductor":      {"role": "energy storage",     "description": "stores energy in a magnetic field and opposes current change"},
    "potentiometer": {"role": "variable resistor",  "description": "provides adjustable resistance"},

    # Diodes
    "diode":         {"role": "one-way valve",      "description": "allows current to flow in only one direction"},
    "led":           {"role": "light emitter",      "description": "emits light when current flows through it"},
    "zener_diode":   {"role": "voltage regulator",  "description": "maintains a stable reference voltage"},

    # Transistors
    "transistor":        {"role": "switch/amplifier",  "description": "amplifies signals or acts as an electronic switch"},
    "npn_transistor":    {"role": "NPN switch",         "description": "switches on when base is driven high"},
    "pnp_transistor":    {"role": "PNP switch",         "description": "switches on when base is driven low"},
    "mosfet":            {"role": "FET switch",         "description": "voltage-controlled switch with very low gate current"},

    # ICs
    "op_amp":            {"role": "amplifier",          "description": "amplifies the difference between two input voltages"},
    "555_timer":         {"role": "timer IC",            "description": "generates timing pulses and oscillations"},
    "arduino":           {"role": "microcontroller",    "description": "runs code to control other components"},
    "microcontroller":   {"role": "microcontroller",    "description": "processes data and controls the circuit"},

    # Output devices
    "buzzer":    {"role": "audio output",    "description": "produces sound when current flows through it"},
    "motor":     {"role": "mechanical output","description": "converts electrical energy into rotational motion"},
    "dc_motor":  {"role": "mechanical output","description": "converts electrical energy into rotational motion"},
    "speaker":   {"role": "audio output",    "description": "converts electrical signals into sound waves"},
    "relay":     {"role": "electromagnetic switch","description": "uses a small current to control a larger circuit"},
    "display":   {"role": "visual output",   "description": "shows numerical or graphical information"},
    "lcd":       {"role": "visual output",   "description": "displays text or graphics using liquid crystals"},

    # Sensors
    "ldr":          {"role": "light sensor",     "description": "changes resistance based on light intensity"},
    "thermistor":   {"role": "temperature sensor","description": "changes resistance based on temperature"},
    "photodiode":   {"role": "light sensor",      "description": "generates current proportional to light intensity"},
    "button":       {"role": "input switch",      "description": "opens or closes a circuit when pressed"},
    "switch":       {"role": "circuit switch",    "description": "manually opens or closes a circuit"},
    "sensor":       {"role": "sensor",            "description": "detects physical quantities and converts them to electrical signals"},

    # Other
    "ground":       {"role": "reference",         "description": "provides the zero-voltage reference point"},
    "fuse":         {"role": "protection",        "description": "breaks the circuit if current exceeds a safe level"},
    "transformer":  {"role": "voltage converter", "description": "steps voltage up or down using electromagnetic induction"},
}

POWER_SOURCES       = {"battery", "power_supply", "solar_cell"}
NEEDS_CURRENT_LIMIT = {"led", "diode", "zener_diode"}
CURRENT_LIMITERS    = {"resistor", "potentiometer", "mosfet", "transistor",
                       "npn_transistor", "pnp_transistor"}

LED_OUTPUTS    = {"led"}
MOTOR_OUTPUTS  = {"motor", "dc_motor"}
BUZZER_OUTPUTS = {"buzzer"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _parse_flow(connections: list[str]) -> str:
    parts = []
    for conn in connections:
        sep = "->" if "->" in conn else "--"
        nodes = [n.strip() for n in conn.split(sep)]
        arrow_chain = " → ".join(nodes)
        parts.append(f"Current flows from the {arrow_chain}.")

        # Add effect note
        last = _normalize(nodes[-1]) if nodes else ""
        if last in LED_OUTPUTS:
            parts[-1] += " This causes the LED to emit light."
        elif last in MOTOR_OUTPUTS:
            parts[-1] += " This causes the motor to spin."
        elif last in BUZZER_OUTPUTS:
            parts[-1] += " This causes the buzzer to produce sound."

    return " ".join(parts)


def _check_warnings(components: list[str], unknown: list[str]) -> list[str]:
    warnings = []
    if not any(c in POWER_SOURCES for c in components):
        warnings.append("No power source detected. The circuit cannot operate without one.")
    has_limiter = any(c in CURRENT_LIMITERS for c in components)
    for comp in NEEDS_CURRENT_LIMIT:
        if comp in components and not has_limiter:
            warnings.append(f"'{comp}' detected without a current-limiting component. Add a resistor to prevent burnout.")
    for u in unknown:
        warnings.append(f"Unknown component '{u}' — not in the knowledge base. Check the component name.")
    return warnings


# ── Main Entry Point ───────────────────────────────────────────────────────────

def explain_circuit(circuit_json: dict[str, Any]) -> dict[str, Any]:
    """
    Input:  circuit JSON with 'components' and 'connections' lists
    Output: { explanation, component_details, flow_description, warnings }
    """
    raw_components = circuit_json.get("components", [])
    connections    = circuit_json.get("connections", [])

    components        = [_normalize(c) for c in raw_components]
    component_details = []
    unknown_components: list[str] = []

    for comp in components:
        if comp in COMPONENT_DB:
            info = COMPONENT_DB[comp]
            component_details.append({
                "name":        comp,
                "role":        info["role"],
                "description": info["description"],
            })
        else:
            unknown_components.append(comp)
            component_details.append({
                "name":        comp,
                "role":        "unknown",
                "description": "component not in knowledge base",
            })

    if not components:
        explanation = "No components provided. Cannot generate an explanation."
    else:
        parts = []
        for detail in component_details:
            parts.append(f"a {detail['name']} ({detail['role']}) that {detail['description']}")
        explanation = "This circuit uses " + ", ".join(parts[:-1])
        if len(parts) > 1:
            explanation += f", and {parts[-1]}."
        else:
            explanation += f"{parts[0]}."

    flow_description = _parse_flow(connections) if connections else ""

    if flow_description:
        explanation = explanation.rstrip(".") + ". " + flow_description

    return {
        "explanation":       explanation,
        "component_details": component_details,
        "flow_description":  flow_description,
        "warnings":          _check_warnings(components, unknown_components),
    }


def explain_circuits_batch(circuits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [explain_circuit(c) for c in circuits]
