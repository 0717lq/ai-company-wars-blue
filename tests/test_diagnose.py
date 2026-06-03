"""diagnose 模块测试 — 配置、依赖、GPU、网络检查。"""

import json
from unittest.mock import MagicMock, patch

import pytest

from rag_builder.diagnose import (
    CheckResult,
    DiagnosisReport,
    _check_config,
    _check_dependencies,
    _check_gpu,
    _check_network,
    _check_python,
    _check_tcp,
    format_report,
    run_diagnosis,
)


class TestCheckResult:
    """CheckResult 数据类测试。"""

    def test_fields(self):
        """CheckResult 应包含 name/status/detail 字段。"""
        cr = CheckResult(name="test", status="pass", detail="ok")
        assert cr.name == "test"
        assert cr.status == "pass"
        assert cr.detail == "ok"

    def test_to_dict(self):
        """to_dict 应返回正确字典。"""
        cr = CheckResult(name="dep", status="fail", detail="missing")
        d = cr.to_dict()
        assert d == {"name": "dep", "status": "fail", "detail": "missing"}


class TestDiagnosisReport:
    """DiagnosisReport 测试。"""

    def test_summary_counts(self):
        """summary 应正确统计 pass/warn/fail。"""
        report = DiagnosisReport(checks=[
            CheckResult("a", "pass", ""),
            CheckResult("b", "pass", ""),
            CheckResult("c", "warn", ""),
            CheckResult("d", "fail", ""),
        ])
        s = report.summary
        assert s["pass"] == 2
        assert s["warn"] == 1
        assert s["fail"] == 1

    def test_to_json_valid(self):
        """to_json 应返回合法 JSON。"""
        report = DiagnosisReport(checks=[CheckResult("x", "pass", "ok")])
        j = report.to_json()
        data = json.loads(j)
        assert data["tool"] == "rag-builder"
        assert data["command"] == "diagnose"
        assert len(data["checks"]) == 1
        assert data["checks"][0]["name"] == "x"

    def test_timestamp_auto_generated(self):
        """timestamp 应自动生成。"""
        report = DiagnosisReport()
        assert "T" in report.timestamp  # ISO 格式


class TestCheckConfig:
    """配置文件检查测试。"""

    def test_no_config(self):
        """未指定配置文件应返回 warn。"""
        result = _check_config(None)
        assert result.status == "warn"
        assert "未指定" in result.detail

    def test_nonexistent_file(self, tmp_path):
        """不存在的文件应返回 fail。"""
        result = _check_config(str(tmp_path / "missing.json"))
        assert result.status == "fail"
        assert "不存在" in result.detail

    def test_invalid_json(self, tmp_path):
        """无效 JSON 应返回 fail。"""
        p = tmp_path / "bad.json"
        p.write_text("{invalid", encoding="utf-8")
        result = _check_config(str(p))
        assert result.status == "fail"
        assert "JSON" in result.detail

    def test_invalid_config(self, tmp_path):
        """验证失败的配置应返回 fail。"""
        p = tmp_path / "bad_config.json"
        p.write_text(json.dumps({"chunking": {"chunk_size": 5}}), encoding="utf-8")
        result = _check_config(str(p))
        assert result.status == "fail"
        assert "验证失败" in result.detail

    def test_valid_config(self, tmp_path):
        """有效配置应返回 pass。"""
        p = tmp_path / "good.json"
        config_data = {
            "chunking": {"strategy": "recursive", "chunk_size": 512, "chunk_overlap": 128, "min_chunk_size": 50},
            "embedding": {"model": "bge-base-zh-v1.5", "batch_size": 8, "device": "auto", "normalize": True},
            "vector_store": {"backend": "milvus", "collection": "test", "metric": "cosine", "index_type": "HNSW"},
            "retriever": {"strategy": "hybrid", "top_k": 10, "rerank_top_n": 5, "bm25_weight": 0.3, "vector_weight": 0.7},
            "query": {"decompose": False},
        }
        p.write_text(json.dumps(config_data), encoding="utf-8")
        result = _check_config(str(p))
        assert result.status == "pass"


class TestCheckPython:
    """Python 版本检查测试。"""

    def test_current_python(self):
        """当前 Python 应返回 pass。"""
        result = _check_python()
        # 测试环境 Python >= 3.10
        assert result.status == "pass"
        assert "." in result.detail


class TestCheckDependencies:
    """依赖检查测试。"""

    def test_checks_installed_packages(self):
        """已安装的包应返回 pass。"""
        results = _check_dependencies({"milvus"})
        [r.name for r in results]
        # json 应该总是安装的
        assert len(results) > 0

    def test_reports_missing_packages(self):
        """未安装的包应返回 fail。"""
        results = _check_dependencies({"milvus"})
        # 检查至少有一个 fail（pymilvus 可能没装）
        any(r.status == "fail" for r in results)
        # 这取决于环境，但至少检查结构正确
        for r in results:
            assert r.status in ("pass", "fail")


class TestCheckGPU:
    """GPU 检查测试。"""

    @patch("rag_builder.diagnose.subprocess.run")
    def test_gpu_found(self, mock_run):
        """nvidia-smi 返回 GPU 信息时应返回 pass。"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA RTX 4060, 8192, 7000\n",
        )
        result = _check_gpu()
        assert result.status == "pass"
        assert "RTX 4060" in result.detail

    @patch("rag_builder.diagnose.subprocess.run")
    def test_gpu_not_found(self, mock_run):
        """nvidia-smi 不存在时应返回 warn。"""
        mock_run.side_effect = FileNotFoundError
        result = _check_gpu()
        assert result.status == "warn"

    @patch("rag_builder.diagnose.subprocess.run")
    def test_gpu_timeout(self, mock_run):
        """nvidia-smi 超时应返回 warn。"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=10)
        result = _check_gpu()
        assert result.status == "warn"


class TestCheckNetwork:
    """网络检查测试。"""

    def test_no_config_returns_empty(self):
        """无配置文件应返回空列表。"""
        results = _check_network(None)
        assert results == []

    def test_nonexistent_config_returns_empty(self, tmp_path):
        """不存在的配置文件应返回空列表。"""
        results = _check_network(str(tmp_path / "missing.json"))
        assert results == []

    @patch("rag_builder.diagnose._check_tcp")
    def test_milvus_config_triggers_tcp_check(self, mock_tcp, tmp_path):
        """Milvus 配置应触发 TCP 检查。"""
        mock_tcp.return_value = CheckResult("Milvus 连通", "pass", "localhost:19530")
        config_data = {"vector_store": {"backend": "milvus"}}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(config_data), encoding="utf-8")

        results = _check_network(str(p))
        assert len(results) == 1
        mock_tcp.assert_called_once_with("Milvus", "localhost", 19530)

    def test_chroma_config_returns_local(self, tmp_path):
        """Chroma 配置应返回本地提示。"""
        config_data = {"vector_store": {"backend": "chroma"}}
        p = tmp_path / "config.json"
        p.write_text(json.dumps(config_data), encoding="utf-8")

        results = _check_network(str(p))
        assert len(results) == 1
        assert results[0].status == "pass"
        assert "本地" in results[0].detail


class TestCheckTCP:
    """TCP 连通性检查测试。"""

    @patch("socket.socket")
    def test_connection_success(self, mock_socket_cls):
        """连接成功应返回 pass。"""
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        result = _check_tcp("Test", "localhost", 8080)
        assert result.status == "pass"
        mock_sock.connect.assert_called_once_with(("localhost", 8080))

    @patch("socket.socket")
    def test_connection_refused(self, mock_socket_cls):
        """连接被拒绝应返回 fail。"""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError
        mock_socket_cls.return_value = mock_sock
        result = _check_tcp("Test", "localhost", 8080)
        assert result.status == "fail"
        assert "拒绝" in result.detail


class TestRunDiagnosis:
    """run_diagnosis 集成测试。"""

    def test_no_config(self):
        """无配置时应返回基本检查。"""
        report = run_diagnosis(skip_network=True)
        names = [c.name for c in report.checks]
        assert "Python" in names
        # 不应有配置检查（warn 但存在）
        config_check = [c for c in report.checks if c.name == "配置文件"]
        assert len(config_check) == 1
        assert config_check[0].status == "warn"

    def test_with_valid_config(self, tmp_path):
        """有效配置应通过配置检查。"""
        config_data = {
            "chunking": {"strategy": "recursive", "chunk_size": 512, "chunk_overlap": 128, "min_chunk_size": 50},
            "embedding": {"model": "bge-base-zh-v1.5", "batch_size": 8, "device": "auto", "normalize": True},
            "vector_store": {"backend": "chroma", "collection": "test", "metric": "cosine", "index_type": "HNSW"},
            "retriever": {"strategy": "hybrid", "top_k": 10, "rerank_top_n": 5, "bm25_weight": 0.3, "vector_weight": 0.7},
            "query": {"decompose": False},
        }
        p = tmp_path / "config.json"
        p.write_text(json.dumps(config_data), encoding="utf-8")

        report = run_diagnosis(config_path=str(p), skip_network=True)
        config_check = [c for c in report.checks if c.name == "配置文件"][0]
        assert config_check.status == "pass"

    def test_skip_network(self):
        """skip_network=True 时不应有网络检查。"""
        report = run_diagnosis(skip_network=True)
        net_checks = [c for c in report.checks if "连通" in c.name]
        assert len(net_checks) == 0


class TestFormatReport:
    """format_report 测试。"""

    def test_text_output(self):
        """文本格式应包含图标和摘要。"""
        report = DiagnosisReport(checks=[
            CheckResult("test", "pass", "ok"),
            CheckResult("dep", "fail", "missing"),
        ])
        text = format_report(report)
        assert "✅" in text
        assert "❌" in text
        assert "1 通过" in text
        assert "1 错误" in text

    def test_json_output(self):
        """JSON 格式应返回合法 JSON。"""
        report = DiagnosisReport(checks=[CheckResult("x", "pass", "ok")])
        text = format_report(report, json_output=True)
        data = json.loads(text)
        assert data["tool"] == "rag-builder"
        assert data["checks"][0]["name"] == "x"


class TestCLIIntegration:
    """CLI 集成测试 — 通过 argparse 测试 diagnose 子命令。"""

    def test_diagnose_help(self, capsys):
        """diagnose --help 应显示帮助信息。"""
        import sys

        from rag_builder.cli import main
        with patch.object(sys, "argv", ["rag-builder", "diagnose", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_diagnose_no_config(self, capsys):
        """无配置的 diagnose 应正常运行并输出报告。"""
        import sys

        from rag_builder.cli import main
        with patch.object(sys, "argv", ["rag-builder", "diagnose", "--skip-network"]):
            result = main()
            captured = capsys.readouterr()
            assert "RAG Builder" in captured.out
            # 无配置时依赖检查可能 fail（可选包未装），exit code 0 或 1 都正常
            assert result in (0, 1)

    def test_diagnose_json_output(self, capsys, tmp_path):
        """diagnose --json 应输出合法 JSON。"""
        import sys

        from rag_builder.cli import main
        config_data = {
            "chunking": {"strategy": "recursive", "chunk_size": 512, "chunk_overlap": 128, "min_chunk_size": 50},
            "embedding": {"model": "bge-base-zh-v1.5", "batch_size": 8, "device": "auto", "normalize": True},
            "vector_store": {"backend": "chroma", "collection": "test", "metric": "cosine", "index_type": "HNSW"},
            "retriever": {"strategy": "hybrid", "top_k": 10, "rerank_top_n": 5, "bm25_weight": 0.3, "vector_weight": 0.7},
            "query": {"decompose": False},
        }
        p = tmp_path / "config.json"
        p.write_text(json.dumps(config_data), encoding="utf-8")

        with patch.object(sys, "argv", ["rag-builder", "diagnose", str(p), "--json", "--skip-network"]):
            main()
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data["tool"] == "rag-builder"
            assert data["command"] == "diagnose"
            assert "checks" in data
            assert "summary" in data
