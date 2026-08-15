from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from transformers import AutoTokenizer

from src.analysis import analyze, target_condition_means, tost
from src.common import ROOT, read_json, read_jsonl, sha256_path
from src.renderer import normalize_shell, render_c_matched
from src.audit import prompt_shell
from src.execution import FORMAL_AUTHORIZATION, SMOKE_AUTHORIZATION, _record_acceptance_gate, _require_authorization
import src.execution as execution
import src.episode_adapter as adapter
import src.scheduler as scheduler


class ProtocolControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.experiences=read_jsonl(ROOT/"materials/experience_pairs.jsonl")
        cls.public=read_jsonl(ROOT/"formal/formal_manifest.jsonl")
        cls.bindings=read_jsonl(ROOT/"sealed/sealed_execution_bindings.jsonl")

    def test_manifest_complete_and_blinded(self):
        self.assertEqual(len(self.public),3200);self.assertEqual(len({r["run_id"] for r in self.public}),3200);self.assertTrue(all("condition" not in r and "source_seed" not in r for r in self.public));self.assertEqual(sorted(r["run_order"] for r in self.public),list(range(1,3201)))

    def test_each_target_arm_has_two_repetitions(self):
        cells={}
        for row in self.public:cells.setdefault((row["target_id"],row["masked_arm"]),set()).add(row["repetition"])
        self.assertEqual(len(cells),1600);self.assertTrue(all(value=={1,2} for value in cells.values()))

    def test_pair_hashes_shell_steps_and_length(self):
        for row in self.experiences:
            self.assertEqual(hashlib.sha256(row["p_text"].encode()).hexdigest(),row["p_sha256"]);self.assertEqual(hashlib.sha256(row["c_text"].encode()).hexdigest(),row["c_sha256"]);self.assertEqual(normalize_shell(row["p_text"]),normalize_shell(row["c_text"]));self.assertEqual(row["trajectory_steps"],len(row["phases"]));self.assertGreaterEqual(row["token_ratio_c_over_p"],.9);self.assertLessEqual(row["token_ratio_c_over_p"],1.1)

    def test_complete_frozen_prompt_shell_parity(self):
        for row in self.experiences:
            self.assertEqual(prompt_shell(row["p_text"]),prompt_shell(row["c_text"]))

    def test_c_forbidden_labels_and_index_demo_absent(self):
        forbidden=("retrieved","permuted","control condition","sham","replay-verified","zero-based","admissible commands","source:","source cookbook")
        self.assertTrue(all(not any(term in row["c_text"].lower() for term in forbidden) for row in self.experiences))

    def test_materials_are_deterministic_for_sample(self):
        tokenizer=AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B",local_files_only=True);count=lambda text:len(tokenizer.encode(text,add_special_tokens=False));sources={int(r["seed"]):r for r in read_jsonl(ROOT/"materials/selected_sources.jsonl")}
        for stored in self.experiences[::103]:
            pair=render_c_matched(sources[int(stored["source_seed"])],count);self.assertEqual(pair.p_text,stored["p_text"]);self.assertEqual(pair.c_text,stored["c_text"])

    def test_pc_share_source_per_target(self):
        public={r["run_id"]:r for r in self.public};by_target={}
        for binding in self.bindings:by_target.setdefault(public[binding["run_id"]]["target_id"],set()).add(binding["source_seed"])
        self.assertTrue(all(len(value)==1 for value in by_target.values()))

    def test_target_level_analysis_not_episode_pseudoreplication(self):
        rows=[]
        for target in ("a","b"):
            for condition,outcomes in (("P",[1,0]),("C",[0,0])):
                for result in outcomes:rows.append({"target_id":target,"condition":condition,"terminal_success":result,"technical_failure":False})
        means=target_condition_means(rows);self.assertEqual(means["a"]["P"],.5);result=analyze(rows);self.assertEqual(result["targets"],2);self.assertAlmostEqual(result["risk_difference"],.5)

    def test_episode_adapter_injects_p_or_c_without_provider(self):
        pair=self.experiences[0];target=read_jsonl(ROOT/"materials/selected_targets.jsonl")[0]
        original=adapter.phase4_runner.run_phase4_episode
        original_context=adapter.phase4_runner.target_role_map
        original_experience=adapter.phase4_runner.expected_experience_v0_3
        original_policy=adapter.phase4_runner.Phase4OpenAICompatiblePolicy
        try:
            with tempfile.TemporaryDirectory() as directory:
                def fake_runner(args):
                    experience=adapter.phase4_runner.expected_experience_v0_3("raw",None,{})
                    self.assertEqual(experience,pair["c_text"])
                    self.assertIn(str(target["recipe_text"]).strip(),adapter.phase4_runner.target_role_map(None))
                    path=Path(directory)/f"{args.run_id}.json"
                    payload={"schema_version":"study3_v3_2_episode_v1","experience":{"content":experience,"interface":{}},"experimental_design":{},"software":{}}
                    path.write_text(json.dumps(payload),encoding="utf-8")
                    return path,payload
                adapter.phase4_runner.run_phase4_episode=fake_runner
                args=argparse.Namespace(condition="C",experience_pairs=ROOT/"materials/experience_pairs.jsonl",source_seed=pair["source_seed"],inventory=ROOT/"materials/combined_inventory.jsonl",seed=target["seed"],config=ROOT/"config/model_v1.yaml",interface_config=ROOT/"config/experience_interface_v1.yaml",output_dir=Path(directory),max_steps=50,game_name="cookingworld",game_fold="test",game_params="numLocations=3,numIngredients=2,numDistractorItems=0,includeDoors=0,limitInventorySize=0",api_key_source="unused",pair_id=target["task_id"],repetition=1,manifest_record={},run_id="adapter-mock",confirmatory_use="unit_test")
                _,payload=adapter.run_episode(args)
                self.assertEqual(payload["experience"]["content"],pair["c_text"])
                self.assertEqual(payload["experience"]["sha256"],pair["c_sha256"])
                self.assertFalse(payload["experience"]["interface"]["block_empty"])
                self.assertEqual(payload["schema_version"],"study3_v3_2_episode_v1")
                self.assertEqual(payload["protocol_control_schema_version"],"protocol_control_pc_episode_v1")
        finally:
            adapter.phase4_runner.run_phase4_episode=original
            self.assertIs(adapter.phase4_runner.target_role_map,original_context)
            self.assertIs(adapter.phase4_runner.expected_experience_v0_3,original_experience)
            self.assertIs(adapter.phase4_runner.Phase4OpenAICompatiblePolicy,original_policy)

    def test_tost_zero_is_equivalent_and_margin_is_not(self):
        self.assertTrue(tost(np.zeros(800))["equivalent"]);boundary=np.full(800,.05);self.assertFalse(tost(boundary)["equivalent"])

    def test_old_frozen_input_hashes_unchanged(self):
        report=read_json(ROOT/"reports/materials_preflight_report.json")
        for path,digest in report["old_input_hashes"].items():self.assertEqual(sha256_path(Path(path)),digest)

    def test_paid_execution_locked(self):
        design=read_json(ROOT/"config/design_v1.json");self.assertFalse(design["paid_execution_authorized"]);self.assertTrue((ROOT/"authorization/formal_stale_recovery_resume_authorization.json").exists())
        with self.assertRaises(PermissionError):_require_authorization("wrong acknowledgement","formal")

    def test_execute_initializes_ledger_before_workers(self):
        events=[]
        original_auth=execution._require_authorization
        original_init=execution.scheduler.initialize_or_reconcile
        original_metrics=execution.scheduler.ledger_metrics
        original_context=execution.mp.get_context
        class FakeProcess:
            exitcode=0
            def start(self):events.append("worker_start")
            def join(self):events.append("worker_join")
        class FakeContext:
            def Process(self,**kwargs):return FakeProcess()
        try:
            execution._require_authorization=lambda value,mode:events.append("authorized")
            execution.scheduler.initialize_or_reconcile=lambda spec:events.append("ledger_initialized")
            execution.scheduler.ledger_metrics=lambda spec:{"completed_records":0}
            execution.mp.get_context=lambda mode:FakeContext()
            result=execution.execute(execution.smoke_spec(),"test","smoke")
            self.assertEqual(events[:2],["authorized","ledger_initialized"])
            self.assertEqual(events.count("worker_start"),4)
            self.assertEqual(result["completed_records"],0)
        finally:
            execution._require_authorization=original_auth
            execution.scheduler.initialize_or_reconcile=original_init
            execution.scheduler.ledger_metrics=original_metrics
            execution.mp.get_context=original_context

    def test_record_acceptance_gate_stops_invalid_record(self):
        original=execution.scheduler.initialize_or_reconcile
        original_stop=execution.scheduler._stop_path
        try:
            with tempfile.TemporaryDirectory() as directory:
                stop=Path(directory)/"STOP_REQUESTED"
                execution.scheduler.initialize_or_reconcile=lambda spec,allow_live_claims=True:{"completed":{"bad":{"record_complete":False,"technical_failure":False}}}
                execution.scheduler._stop_path=lambda spec:stop
                with self.assertRaises(RuntimeError):_record_acceptance_gate(object())
                self.assertTrue(stop.exists())
        finally:
            execution.scheduler.initialize_or_reconcile=original
            execution.scheduler._stop_path=original_stop

    def test_protocol_record_complete_accepts_legal_extension_only(self):
        base={"schema_version":"publication_followup_phase4_raw_trajectory_v1","protocol_control_schema_version":"protocol_control_pc_episode_v1","run":{"run_id":"x","started_at_utc":"a","finished_at_utc":"b"},"trajectory":[],"llm":{},"experimental_design":{}}
        self.assertTrue(scheduler.protocol_record_complete(base))
        wrong=dict(base);wrong["protocol_control_schema_version"]="wrong"
        self.assertFalse(scheduler.protocol_record_complete(wrong))
        incomplete=json.loads(json.dumps(base));del incomplete["run"]["finished_at_utc"]
        self.assertFalse(scheduler.protocol_record_complete(incomplete))


if __name__=="__main__":unittest.main()
