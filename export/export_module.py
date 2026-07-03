"""
CircuitMind - Export Module
export/export_module.py

Converts circuit JSON into:
  - SPICE netlist  (export_format="spice")
  - SVG diagram    (export_format="svg")
  - Gate JSON      (export_format="gate_json")
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Component maps ─────────────────────────────────────────────────────────────

COMPONENT_MAP = {
    "battery":   "V",
    "resistor":  "R",
    "led":       "D",
    "capacitor": "C",
    "switch":    "S",
    "motor":     "M",
    "inductor":  "L",
    "transistor":"Q",
}

COMPONENT_VALUES = {
    "battery":   "9V",
    "resistor":  "330ohm",
    "led":       "LED",
    "capacitor": "100uF",
    "switch":    "SW",
    "motor":     "MOTOR",
    "inductor":  "1mH",
    "transistor":"2N2222",
}

VALID_FORMATS = {"spice", "svg", "gate_json"}


# ── SPICE generator ────────────────────────────────────────────────────────────

def generate_spice(circuit_name: str, components: list) -> str:
    lines    = [circuit_name]
    counters: dict = {}
    node     = 1
    for component in components:
        symbol = COMPONENT_MAP.get(component, "X")
        value  = COMPONENT_VALUES.get(component, "?")
        counters[symbol] = counters.get(symbol, 0) + 1
        name = f"{symbol}{counters[symbol]}"
        lines.append(f"{name} {node} {node + 1} {value}")
        node += 1
    lines.append(".end")
    return "\n".join(lines)


# ── SVG generator ──────────────────────────────────────────────────────────────

def generate_svg(circuit_name: str, components: list) -> str:
    """Generate an SVG circuit schematic and return SVG markup string."""
    try:
        import schemdraw
        import schemdraw.elements as elm
    except ImportError:
        raise RuntimeError("schemdraw is not installed. Run: pip install schemdraw")

    SVG_MAP = {
        # Power sources
        "battery":       elm.Battery,
        "power_supply":  elm.SourceV,
        "solar_cell":    elm.SourceV,
        "solar_panel":   elm.SourceV,
        # Passive
        "resistor":      elm.Resistor,
        "capacitor":     elm.Capacitor,
        "inductor":      elm.Inductor,
        "potentiometer": elm.Potentiometer,
        # Diodes
        "diode":         elm.Diode,
        "led":           elm.LED2,
        "zener_diode":   elm.Zener,
        # Switches
        "switch":        elm.Switch,
        "button":        elm.Button,
        # Output devices
        "motor":         elm.Motor,
        "dc_motor":      elm.Motor,
        "dc_fan":        elm.Motor,
        "buzzer":        elm.Speaker,
        "speaker":       elm.Speaker,
        # Protection
        "fuse":          elm.Fuse,
    }

    def _norm(name: str) -> str:
        return name.strip().lower().replace(" ", "_").replace("-", "_")

    normalized = [_norm(c) for c in components]
    drawable   = [c for c in normalized if c != "ground"]

    if not drawable:
        raise RuntimeError("No drawable components found in the circuit.")

    d = schemdraw.Drawing(show=False)
    d.config(fontsize=12)

    first_elem = None
    for i, comp in enumerate(drawable):
        label    = comp.replace("_", " ").title()
        elem_cls = SVG_MAP.get(comp, elm.RBox)
        elem     = d.add(elem_cls().right().label(label, loc="top"))
        if i == 0:
            first_elem = elem

    # Close the circuit with a return path to form a loop
    if first_elem and len(drawable) > 1:
        d.add(elm.Line().down().length(d.unit * 0.6))
        d.add(elm.Line().left().tox(first_elem.start))
        d.add(elm.Line().up().toy(first_elem.start))

    return d.get_imagedata("svg").decode("utf-8")


# ── Gate JSON generator ────────────────────────────────────────────────────────

def generate_gate_json(circuit_name: str, components: list, connections: list) -> dict:
    gates  = []
    wires  = []
    x, y   = 80, 100
    input_counter  = 0
    output_counter = 0

    for i, component in enumerate(components):
        if i == 0:
            gate_type, num_inputs, has_output = "INPUT",  0, True
            input_counter += 1
        elif i == len(components) - 1:
            gate_type, num_inputs, has_output = "OUTPUT", 1, False
            output_counter += 1
        else:
            gate_type, num_inputs, has_output = component.upper(), 1, True

        gates.append({
            "id":          i,
            "type":        gate_type,
            "x":           x + (i * 200),
            "y":           y,
            "inputs":      num_inputs,
            "hasOutput":   has_output,
            "output":      None,
            "inputValues": [False] if gate_type == "INPUT" else [],
            "label":       component.upper(),
        })

    wire_id = 0
    for conn in connections:
        parts = [p.strip() for p in conn.split("->")]
        for j in range(len(parts) - 1):
            from_id = next((g["id"] for g in gates if g["label"] == parts[j].upper()), None)
            to_id   = next((g["id"] for g in gates if g["label"] == parts[j + 1].upper()), None)
            if from_id is not None and to_id is not None:
                wires.append({"id": wire_id, "fromId": from_id, "toId": to_id, "toIndex": 0})
                wire_id += 1

    return {
        "gates":           gates,
        "wires":           wires,
        "gateIdCounter":   len(gates),
        "wireIdCounter":   len(wires),
        "inputCounter":    input_counter,
        "outputCounter":   output_counter,
        "exportedAt":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }


# ── Main Entry Point ───────────────────────────────────────────────────────────

def export_module(json_input: str, export_format: str = "spice") -> dict:
    """
    Input:  JSON string with 'components' and 'connections'
    Output: dict with export result or error
    """
    if not json_input or not json_input.strip():
        return {"status": "error", "message": "Input is empty."}

    if export_format not in VALID_FORMATS:
        return {"status": "error", "message": f"Invalid format. Use one of: {', '.join(VALID_FORMATS)}."}

    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {e}"}

    if "components" not in data or "connections" not in data:
        return {"status": "error", "message": "Missing required fields: 'components' and 'connections'."}

    name        = data.get("circuit_name", "CircuitMind_Generated_Circuit")
    components  = data["components"]
    connections = data["connections"]

    logger.info(f"Exporting '{name}' as {export_format}")

    if export_format == "spice":
        spice = generate_spice(name, components)
        return {
            "status":        "success",
            "format":        "spice",
            "circuit_name":  name,
            "components":    ", ".join(components),
            "connections":   ", ".join(c.replace("->", "→") for c in connections),
            "spice_netlist": spice,
        }

    if export_format == "svg":
        try:
            svg_markup = generate_svg(name, components)
        except RuntimeError as e:
            return {"status": "error", "message": str(e)}
        return {
            "status":       "success",
            "format":       "svg",
            "circuit_name": name,
            "components":   ", ".join(components),
            "connections":  ", ".join(c.replace("->", "→") for c in connections),
            "svg_markup":   svg_markup,
        }

    # gate_json
    gate_data = generate_gate_json(name, components, connections)
    return {
        "status":       "success",
        "format":       "gate_json",
        "circuit_name": name,
        "gate_json":    gate_data,
    }
