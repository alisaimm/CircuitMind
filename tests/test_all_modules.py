"""
CircuitMind - Unified Test Suite
tests/test_all_modules.py

Run with: pytest tests/
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_circuit
from explain.explain_module import explain_circuit
from diagnose.diagnose_module import diagnose_circuit
from export.export_module import export_module


# ── Fixtures ───────────────────────────────────────────────────────────────────

LED_CIRCUIT = {
    "circuit_name": "LED Circuit",
    "components":   ["battery", "resistor", "led"],
    "connections":  ["battery -> resistor -> led"],
}

BAD_CIRCUIT = {
    "circuit_name": "Bad Circuit",
    "components":   ["battery", "led"],
    "connections":  ["battery -> led"],
}

SHORT_CIRCUIT = {
    "circuit_name": "Short",
    "components":   ["battery", "ground"],
    "connections":  ["battery -> ground"],
}


# ── Generate ───────────────────────────────────────────────────────────────────

class TestGenerate:
    def test_led_prompt(self):
        result = generate_circuit("make me a LED circuit")
        assert "components" in result
        assert "led" in result["components"]

    def test_motor_prompt(self):
        result = generate_circuit("I want a motor circuit")
        assert "motor" in " ".join(result.get("components", [])).lower() or result.get("source") == "rule-based"

    def test_empty_input(self):
        result = generate_circuit("")
        assert "error" in result
        assert result["error_code"] == "INVALID_INPUT"

    def test_too_short_input(self):
        result = generate_circuit("ab")
        assert "error" in result

    def test_too_long_input(self):
        result = generate_circuit("a" * 1001)
        assert "error" in result

    def test_always_returns_dict(self):
        for prompt in ["led", "motor", "unknown xyz circuit", "", "ab"]:
            result = generate_circuit(prompt)
            assert isinstance(result, dict)


# ── Explain ────────────────────────────────────────────────────────────────────

class TestExplain:
    def test_led_circuit_explanation(self):
        result = explain_circuit(LED_CIRCUIT)
        assert "explanation" in result
        assert "battery" in result["explanation"].lower()

    def test_component_details_present(self):
        result = explain_circuit(LED_CIRCUIT)
        assert "component_details" in result
        names = [d["name"] for d in result["component_details"]]
        assert "battery" in names
        assert "led" in names

    def test_warning_for_missing_power(self):
        no_power = {"components": ["resistor", "led"], "connections": ["resistor -> led"]}
        result = explain_circuit(no_power)
        assert len(result.get("warnings", [])) > 0

    def test_no_warnings_for_valid_circuit(self):
        result = explain_circuit(LED_CIRCUIT)
        assert result.get("warnings", []) == []

    def test_empty_circuit(self):
        result = explain_circuit({"components": [], "connections": []})
        assert "explanation" in result


# ── Diagnose ───────────────────────────────────────────────────────────────────

class TestDiagnose:
    def test_valid_circuit_passes(self):
        result = diagnose_circuit(LED_CIRCUIT)
        assert result["passed"] is True
        assert len(result["issues"]) == 1
        assert "Info:" in result["issues"][0]

    def test_missing_resistor_flagged(self):
        result = diagnose_circuit(BAD_CIRCUIT)
        assert result["passed"] is False
        assert any("current-limiting" in i for i in result["issues"])

    def test_short_circuit_detected(self):
        result = diagnose_circuit(SHORT_CIRCUIT)
        assert result["passed"] is False
        assert any("short circuit" in i.lower() for i in result["issues"])

    def test_no_power_source_flagged(self):
        no_power = {"components": ["resistor", "led"], "connections": ["resistor -> led"]}
        result = diagnose_circuit(no_power)
        assert any("power source" in i.lower() for i in result["issues"])

    def test_result_always_has_passed_and_issues(self):
        result = diagnose_circuit(LED_CIRCUIT)
        assert "passed" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)


# ── Export ─────────────────────────────────────────────────────────────────────

class TestExport:
    def _json(self, circuit: dict) -> str:
        return json.dumps(circuit)

    def test_spice_export(self):
        result = export_module(self._json(LED_CIRCUIT), export_format="spice")
        assert result["status"] == "success"
        assert "spice_netlist" in result
        assert ".end" in result["spice_netlist"]

    def test_gate_json_export(self):
        result = export_module(self._json(LED_CIRCUIT), export_format="gate_json")
        assert result["status"] == "success"
        assert "gate_json" in result
        assert "gates" in result["gate_json"]

    def test_empty_input(self):
        result = export_module("")
        assert result["status"] == "error"

    def test_invalid_json(self):
        result = export_module("not json at all")
        assert result["status"] == "error"

    def test_missing_fields(self):
        result = export_module('{"circuit_name": "X"}', export_format="spice")
        assert result["status"] == "error"

    def test_invalid_format(self):
        result = export_module(self._json(LED_CIRCUIT), export_format="pdf")
        assert result["status"] == "error"

    def test_no_circuit_name_uses_default(self):
        no_name = {"components": ["battery", "resistor"], "connections": ["battery -> resistor"]}
        result = export_module(json.dumps(no_name), export_format="spice")
        assert result["status"] == "success"
        assert result["circuit_name"] == "CircuitMind_Generated_Circuit"


# ── Integration ────────────────────────────────────────────────────────────────

class TestIntegration:
    def test_generate_then_diagnose(self):
        circuit = generate_circuit("make me a LED circuit")
        assert "components" in circuit
        result = diagnose_circuit(circuit)
        assert "passed" in result

    def test_generate_then_explain(self):
        circuit = generate_circuit("make me a LED circuit")
        result = explain_circuit(circuit)
        assert "explanation" in result

    def test_generate_then_export(self):
        circuit = generate_circuit("make me a LED circuit")
        result = export_module(json.dumps(circuit), export_format="spice")
        assert result["status"] == "success"
