"""Tests portátiles de contrato sin driver, pantalla ni juegos."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

class ContractTests(unittest.TestCase):
    def test_mcp_initialize_list_stop(self):
        with tempfile.TemporaryDirectory() as home:
            env={**os.environ,"HOME":home,"USERPROFILE":home}
            proc=subprocess.Popen([sys.executable,"-u",str(BASE/"server.py")],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                text=True,encoding="utf-8",env=env)
            try:
                def rpc(i,method,params=None):
                    req={"jsonrpc":"2.0","id":i,"method":method}
                    if params is not None: req["params"]=params
                    proc.stdin.write(json.dumps(req)+"\n"); proc.stdin.flush()
                    return json.loads(proc.stdout.readline())
                r=rpc(1,"initialize",{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1"}})
                self.assertEqual(r["result"]["serverInfo"]["name"],"gemco-joystick")
                ts=rpc(2,"tools/list")["result"]["tools"]
                names={x["name"] for x in ts}
                self.assertTrue({"gemco_status","gemco_stop","gemco_gamepad",
                                 "gemco_screen","gemco_feedback"}.issubset(names))
                self.assertEqual(len(names),len(ts))
                test=rpc(3,"tools/call",{"name":"gemco_gamepad","arguments":{"lx":0.3}})
                self.assertTrue(test["result"]["isError"])
                test=rpc(4,"tools/call",{"name":"gemco_stop","arguments":{}})
                self.assertFalse(test["result"]["isError"])
                status=rpc(5,"tools/call",{"name":"gemco_status","arguments":{}})
                payload=json.loads(status["result"]["content"][0]["text"])
                self.assertFalse(payload["armed"])
                self.assertEqual(payload["cloud"],"off by default")
            finally:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired: proc.kill()

    def test_compact_learning(self):
        with tempfile.TemporaryDirectory() as d:
            m=load_module("gemco_learning_tests",BASE/"learning.py")
            m.ROOT=Path(d)
            record=m.learn("ResidentEvil","pasillo","dodge",0.8,120)
            self.assertEqual(record["samples"],1)
            m.learn("ResidentEvil","pasillo","dodge",0.6,100)
            summary=m.compact("ResidentEvil",max_chars=260)
            self.assertLessEqual(summary["chars"],260)
            self.assertIn("dodge",summary["summary"])
            advice=m.recommend("ResidentEvil","pasillo",top=3)
            self.assertEqual(len(advice["suggestions"]),3)
            with self.assertRaises(ValueError):
                m.learn("ResidentEvil","pasillo","../../secret",0.3)

if __name__=="__main__":
    unittest.main()
