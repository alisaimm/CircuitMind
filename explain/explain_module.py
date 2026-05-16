from typing import Any


COMPONENT_INFO = {
    "battery":          {"role": "power source",       "description": "provides electrical energy to the circuit"},
    "power_supply":     {"role": "power source",       "description": "supplies regulated DC voltage to the circuit"},
    "solar_cell":       {"role": "power source",       "description": "converts sunlight into electrical energy"},
    "resistor":         {"role": "current limiter",    "description": "limits and controls the flow of current"},
    "capacitor":        {"role": "energy storage",     "description": "stores and releases electrical charge"},
    "inductor":         {"role": "energy storage",     "description": "stores energy in a magnetic field"},
    "potentiometer":    {"role": "variable resistor",  "description": "adjusts resistance to control current or voltage"},
    "diode":            {"role": "one-way valve",      "description": "allows current to flow in only one direction"},
    "led":              {"role": "light emitter",      "description": "emits light when current flows through it"},
    "zener_diode":      {"role": "voltage regulator",  "description": "maintains a stable reference voltage"},
    "transistor":       {"role": "switch/amplifier",   "description": "amplifies signals or acts as an electronic switch"},
    "mosfet":           {"role": "switch",             "description": "controls large currents using a small gate voltage"},
    "op_amp":           {"role": "amplifier",            "description": "amplifies the difference between two input signals"},
    "op-amp":           {"role": "amplifier",            "description": "amplifies the difference between two input signals"},
    "555_timer":        {"role": "timer IC",             "description": "generates timing signals and pulses"},
    "arduino":          {"role": "microcontroller",      "description": "runs code to control other components"},
    "microcontroller":  {"role": "microcontroller",      "description": "executes programmed logic to control the circuit"},
    "npn_transistor":   {"role": "NPN switch/amplifier", "description": "allows current from collector to emitter when base is triggered with a positive signal"},
    "pnp_transistor":   {"role": "PNP switch/amplifier", "description": "allows current from emitter to collector when base is pulled low"},
    "buzzer":           {"role": "sound output",       "description": "produces an audible beep or tone"},
    "motor":            {"role": "mechanical output",  "description": "converts electrical energy into rotational motion"},
    "speaker":          {"role": "audio output",       "description": "converts electrical signals into sound waves"},
    "relay":            {"role": "switch",             "description": "uses a small current to control a larger circuit"},
    "display":          {"role": "visual output",      "description": "shows text or graphics driven by control signals"},
    "lcd":              {"role": "visual output",      "description": "displays alphanumeric characters or graphics"},
    "switch":           {"role": "manual control",     "description": "opens or closes the circuit when toggled"},
    "button":           {"role": "manual control",     "description": "momentarily closes the circuit when pressed"},
    "sensor":           {"role": "input",              "description": "detects a physical quantity and produces a signal"},
    "thermistor":       {"role": "temperature sensor", "description": "changes resistance based on temperature"},
    "ldr":              {"role": "light sensor",       "description": "changes resistance based on light intensity"},
    "photodiode":       {"role": "light sensor",       "description": "generates current when exposed to light"},
    "ground":           {"role": "reference point",    "description": "serves as the 0V reference for the circuit"},
    "fuse":             {"role": "protection",         "description": "breaks the circuit if current exceeds a safe limit"},
    "transformer":      {"role": "voltage converter",  "description": "steps voltage up or down using magnetic induction"},
}

NEEDS_CURRENT_LIMIT = {"led", "diode", "zener_diode"}
CURRENT_LIMITERS    = {"resistor", "potentiometer", "mosfet", "transistor", "npn_transistor", "pnp_transistor"}
POWER_SOURCES       = {"battery", "power_supply", "solar_cell"}


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _article(word: str) -> str:
    return "an" if word and word[0].lower() in "aeiou" else "a"


def _parse_connections(connections: list[str]) -> list[list[str]]:
    parsed = []
    for conn in connections:
        if "->" in conn:
            nodes = [n.strip().lower() for n in conn.split("->")]
        elif "--" in conn:
            nodes = [n.strip().lower() for n in conn.split("--")]
        else:
            nodes = [conn.strip().lower()]
        parsed.append(nodes)
    return parsed


def _build_flow_description(components: list[str], connections: list[str]) -> str:
    flow_sentences = []

    for path in _parse_connections(connections):
        if len(path) < 2:
            continue

        readable = [p.replace("_", " ") for p in path]
        sentence = "Current flows from the " + " → ".join(readable) + "."

        terminal = path[-1]
        if terminal == "led":
            sentence += " This causes the LED to emit light."
        elif terminal == "motor":
            sentence += " This causes the motor to spin."
        elif terminal == "buzzer":
            sentence += " This causes the buzzer to sound."
        elif terminal == "speaker":
            sentence += " This drives the speaker to produce audio."

        flow_sentences.append(sentence)

    if not flow_sentences:
        has_power  = any(c in POWER_SOURCES for c in components)
        has_output = any(c in {"led", "motor", "buzzer", "speaker", "display"} for c in components)
        if has_power and has_output:
            return "Power from the source flows through the circuit to drive the output component."

    return " ".join(flow_sentences)


def _check_warnings(components: list[str], unknown: list[str]) -> list[str]:
    warnings = []

    if not any(c in POWER_SOURCES for c in components):
        warnings.append("No power source detected. The circuit cannot operate without one.")

    has_limiter = any(c in CURRENT_LIMITERS for c in components)
    for comp in NEEDS_CURRENT_LIMIT:
        if comp in components and not has_limiter:
            warnings.append(f"'{comp}' detected without a current-limiting component. Add a resistor to prevent burnout.")

    for u in unknown:
        warnings.append(f"'{u}' is not in the knowledge base. Description may be incomplete.")

    return warnings


def explain_circuit(circuit_json: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(circuit_json, dict):
        return {"explanation": "", "component_details": [], "flow_description": "", "warnings": ["Input must be a JSON object."]}

    raw_components  = circuit_json.get("components", [])
    raw_connections = circuit_json.get("connections", [])

    if not raw_components:
        return {"explanation": "", "component_details": [], "flow_description": "", "warnings": ["No components found in circuit JSON."]}

    components = [_normalize(c) for c in raw_components]

    component_details  = []
    unknown_components = []

    for comp in components:
        if comp in COMPONENT_INFO:
            info = COMPONENT_INFO[comp]
            component_details.append({"name": comp, "role": info["role"], "description": info["description"]})
        else:
            unknown_components.append(comp)
            component_details.append({"name": comp, "role": "unknown", "description": f"a {comp} component (no description available)"})

    parts = []
    for detail in component_details:
        comp_name = detail["name"].replace("_", " ")
        parts.append(f"{_article(comp_name)} {comp_name} ({detail['role']}) that {detail['description']}")

    if len(parts) > 1:
        explanation = "This circuit uses " + ", ".join(parts[:-1]) + ", and " + parts[-1] + "."
    else:
        explanation = "This circuit uses " + parts[0] + "."

    flow_description = _build_flow_description(components, raw_connections)
    if flow_description:
        explanation += " " + flow_description

    return {
        "explanation":       explanation,
        "component_details": component_details,
        "flow_description":  flow_description,
        "warnings":          _check_warnings(components, unknown_components),
    }


def explain_circuits_batch(circuits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [explain_circuit(c) for c in circuits]


def pretty_print(result: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print(f"\n📝 EXPLANATION:\n  {result['explanation']}")

    if result.get("flow_description"):
        print(f"\n⚡ FLOW:\n  {result['flow_description']}")

    if result.get("component_details"):
        print("\n🔩 COMPONENTS:")
        for c in result["component_details"]:
            print(f"  • {c['name']:20s} | {c['role']:20s} | {c['description']}")

    if result.get("warnings"):
        print("\n⚠️  WARNINGS:")
        for w in result["warnings"]:
            print(f"  ! {w}")
