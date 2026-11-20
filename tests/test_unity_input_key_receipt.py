from pathlib import Path
import importlib.util
import unittest

path = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/InputKeySafety/run_native_input_keys.py"
spec = importlib.util.spec_from_file_location("keys", path)
qa = importlib.util.module_from_spec(spec); spec.loader.exec_module(qa)
VALID = {"letter_a", "alpha_1", "left_control", "return", "keypad_enter", "keypad_0"}

def data():
    return {"engineVersion": "6000.6.7f1", "aliasLegacyValueUndefined": True, "aliasNewValueDefined": True,
        "cases": [dict(name=name, expected=name in VALID, nativeHeld=True, nativeEdge=True, pressed=name in VALID, edge=name in VALID, passed=True, error="") for name in sorted(qa.CASES)]}

class InputKeyReceiptTests(unittest.TestCase):
    def test_complete_contract(self): self.assertTrue(qa.classify(0, data()))
    def test_missing_duplicate_or_unknown_case(self):
        for name in qa.CASES:
            d=data(); d["cases"]=[r for r in d["cases"] if r["name"]!=name]
            self.assertFalse(qa.classify(0,d))
        d=data();d["cases"][0]=d["cases"][1].copy();self.assertFalse(qa.classify(0,d))
    def test_valid_bindings_cannot_be_redefined_as_negative_controls(self):
        d=data()
        for row in d["cases"]:row.update(expected=False,pressed=False,edge=False)
        self.assertFalse(qa.classify(0,d))
    def test_failed_exception_or_wrong_exit(self):
        for key,val in (("nativeHeld",False),("nativeEdge",False),("passed",False),("error","IndexOutOfRangeException"),("pressed",1),("edge",False)):
            d=data();row=next(r for r in d["cases"] if r["name"]=="letter_a");row[key]=val
            self.assertFalse(qa.classify(0,d))
        for code in (3,-999):self.assertFalse(qa.classify(code,data()))
    def test_invalid_control_preconditions_and_payload(self):
        for value in (None,[],{}):self.assertFalse(qa.classify(0,value))
        d=data();d["aliasLegacyValueUndefined"]=False;self.assertFalse(qa.classify(0,d))
