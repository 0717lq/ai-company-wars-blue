"""RAG Builder 健康检查 — 一键诊断配置、依赖、GPU 和网络连通性。

用法:
    from rag_builder.diagnose import run_diagnosis
    report = run_diagnosis("rag_config.json")
    print(format_report(report))
    print(format_report(report, json_output=True))
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    """单项检查结果。"""

    name: str
    status: str  # "pass", "warn", "fail"
    detail: str

    def to_dict(self) -> dict[str, str]:
        """序列化为字典。"""
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass
class DiagnosisReport:
    """诊断报告。"""

    checks: list[CheckResult] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def summary(self) -> dict[str, int]:
        """统计 pass/warn/fail 数量。"""
        counts = {"pass": 0, "warn": 0, "fail": 0}
        for c in self.checks:
            if c.status in counts:
                counts[c.status] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """序列化为完整字典。"""
        return {
            "tool": "rag-builder",
            "command": "diagnose",
            "timestamp": self.timestamp,
            "checks": [c.to_dict() for c in self.checks],
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """序列化为 JSON 字符串。"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# 需要检测的依赖包及其对应的 pip extra
DEPENDENCY_MAP: dict[str, dict[str, str]] = {
    "sentence_transformers": {"pip": "sentence-transformers", "extra": "st"},
    "openai": {"pip": "openai", "extra": "openai"},
    "pymilvus": {"pip": "pymilvus", "extra": "milvus"},
    "chromadb": {"pip": "chromadb", "extra": "chromadb"},
    "pymupdf": {"pip": "pymupdf", "extra": "pdf"},
    "rank_bm25": {"pip": "rank-bm25", "extra": "bm25"},
    "jieba": {"pip": "jieba", "extra": "bm25"},
}


def _check_config(config_path: str | None) -> CheckResult:
    """检查配置文件有效性。"""
    if not config_path:
        return CheckResult("配置文件", "warn", "未指定配置文件")

    path = Path(config_path)
    if not path.exists():
        return CheckResult("配置文件", "fail", f"文件不存在: {config_path}")

    try:
        import json as json_mod

        with open(path, encoding="utf-8") as f:
            data = json_mod.load(f)
    except json.JSONDecodeError as e:
        return CheckResult("配置文件", "fail", f"JSON 解析失败: {e}")

    try:
        from .config_schema import RAGConfig

        config = RAGConfig.from_dict(data)
    except Exception as e:
        return CheckResult("配置文件", "fail", f"配置解析失败: {e}")

    errors = config.validate()
    if errors:
        return CheckResult("配置文件", "fail", f"验证失败 ({len(errors)} 个问题): {'; '.join(errors)}")

    return CheckResult("配置文件", "pass", "有效")


def _check_python() -> CheckResult:
    """检查 Python 版本。"""
    ver = sys.version.split()[0]
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 10:
        return CheckResult("Python", "pass", ver)
    return CheckResult("Python", "warn", f"{ver}（建议 >= 3.10）")


def _check_dependencies(required_backends: set[str] | None = None) -> list[CheckResult]:
    """检查依赖包是否安装。"""
    results = []

    # 确定需要检查哪些依赖
    needed = set(DEPENDENCY_MAP.keys())
    if required_backends:
        # 只检查配置中用到的后端相关依赖
        filtered = set()
        if "milvus" in required_backends:
            filtered.add("pymilvus")
        if "chroma" in required_backends:
            filtered.add("chromadb")
        # embedding 和 bm25 总是检查
        filtered.update({"sentence_transformers", "openai", "rank_bm25", "jieba"})
        # pdf 也检查
        filtered.add("pymupdf")
        needed = filtered

    for module_name, info in DEPENDENCY_MAP.items():
        if module_name not in needed:
            continue
        pip_name = info["pip"]
        extra = info["extra"]
        try:
            # 尝试获取版本号
            ver = pkg_version(pip_name)
            results.append(CheckResult(pip_name, "pass", f"{ver}"))
        except Exception:
            # 包未安装
            results.append(
                CheckResult(pip_name, "fail", f"未安装（pip install rag-builder[{extra}]）")
            )

    return results


def _check_gpu() -> CheckResult:
    """检查 GPU 可用性和显存。"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return CheckResult("GPU", "warn", "nvidia-smi 执行失败")

        line = result.stdout.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            name = parts[0]
            total_mb = float(parts[1])
            free_mb = float(parts[2])
            total_gb = total_mb / 1024
            free_gb = free_mb / 1024
            return CheckResult(
                "GPU",
                "pass",
                f"{name} ({total_gb:.1f} GB, 空闲 {free_gb:.1f} GB)",
            )
        return CheckResult("GPU", "warn", f"nvidia-smi 输出格式异常: {line}")

    except FileNotFoundError:
        return CheckResult("GPU", "warn", "nvidia-smi 未找到（无 GPU 或未安装驱动）")
    except subprocess.TimeoutExpired:
        return CheckResult("GPU", "warn", "nvidia-smi 超时")
    except Exception as e:
        return CheckResult("GPU", "warn", f"GPU 检测异常: {e}")


def _check_gpu_vram(config_path: str | None) -> CheckResult:
    """检查 GPU 显存是否满足配置需求。"""
    if not config_path:
        return CheckResult("显存估算", "skip", "无配置文件")

    path = Path(config_path)
    if not path.exists():
        return CheckResult("显存估算", "skip", "配置文件不存在")

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        from .config_schema import RAGConfig, estimate_gpu_vram

        config = RAGConfig.from_dict(data)
        vram = estimate_gpu_vram(config)
        required = vram["total"]

        # 获取实际 GPU 显存
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return CheckResult("显存估算", "warn", f"需要 {required:.1f} GB（无法检测实际显存）")

        free_mb = float(result.stdout.strip().split("\n")[0].strip())
        free_gb = free_mb / 1024

        if required > free_gb:
            return CheckResult(
                "显存估算", "fail", f"需要 {required:.1f} GB，仅剩 {free_gb:.1f} GB"
            )
        elif required > free_gb * 0.8:
            return CheckResult(
                "显存估算", "warn", f"需要 {required:.1f} GB（剩余 {free_gb:.1f} GB，较紧张）"
            )
        return CheckResult(
            "显存估算", "pass", f"需要 {required:.1f} GB（剩余 {free_gb:.1f} GB 可用）"
        )
    except Exception as e:
        return CheckResult("显存估算", "warn", f"估算失败: {e}")


def _check_network(config_path: str | None) -> list[CheckResult]:
    """检查网络连通性（如果配置了远程 API）。"""
    results = []

    if not config_path:
        return results

    path = Path(config_path)
    if not path.exists():
        return results

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return results

    # 检查 embedding 是否使用 API
    embedding_model = data.get("embedding", {}).get("model", "")
    api_models = {"text-embedding-3-small", "text-embedding-3-large"}
    if embedding_model in api_models:
        # 检查 OpenAI API 连通性
        results.append(_check_url("OpenAI API", "https://api.openai.com/v1/models"))

    # 检查 Milvus 连通性
    backend = data.get("vector_store", {}).get("backend", "")
    if backend == "milvus":
        results.append(_check_tcp("Milvus", "localhost", 19530))

    # 检查 Chroma（通常是本地的）
    if backend == "chroma":
        results.append(CheckResult("Chroma", "pass", "本地数据库，无需网络"))

    return results


def _check_url(name: str, url: str) -> CheckResult:
    """检查 URL 连通性。"""
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=5)
        return CheckResult(f"{name} 连通", "pass", url)
    except urllib.error.HTTPError as e:
        # 4xx/5xx 也算连通（服务器有响应）
        if e.code < 500:
            return CheckResult(f"{name} 连通", "pass", f"{url} (HTTP {e.code})")
        return CheckResult(f"{name} 连通", "warn", f"{url} (HTTP {e.code})")
    except urllib.error.URLError as e:
        return CheckResult(f"{name} 连通", "fail", f"无法连接: {e.reason}")
    except Exception as e:
        return CheckResult(f"{name} 连通", "fail", f"连接失败: {e}")


def _check_tcp(name: str, host: str, port: int) -> CheckResult:
    """检查 TCP 连通性。"""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.close()
        return CheckResult(f"{name} 连通", "pass", f"{host}:{port}")
    except TimeoutError:
        return CheckResult(f"{name} 连通", "fail", f"{host}:{port} 超时")
    except ConnectionRefusedError:
        return CheckResult(f"{name} 连通", "fail", f"{host}:{port} 连接被拒绝（服务未启动？）")
    except Exception as e:
        return CheckResult(f"{name} 连通", "fail", f"{host}:{port} {e}")


def run_diagnosis(
    config_path: str | None = None,
    skip_network: bool = False,
) -> DiagnosisReport:
    """运行完整诊断。

    Args:
        config_path: 配置文件路径（可选）
        skip_network: 是否跳过网络检测

    Returns:
        DiagnosisReport 实例
    """
    report = DiagnosisReport()

    # 1. 配置检查
    config_check = _check_config(config_path)
    report.checks.append(config_check)

    # 2. Python 版本
    report.checks.append(_check_python())

    # 3. 依赖检查
    # 从配置中提取需要的后端
    required_backends: set[str] | None = None
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            backend = data.get("vector_store", {}).get("backend", "")
            if backend:
                required_backends = {backend}
        except Exception:
            pass

    dep_checks = _check_dependencies(required_backends)
    report.checks.extend(dep_checks)

    # 4. GPU 检查
    report.checks.append(_check_gpu())

    # 5. 显存估算
    report.checks.append(_check_gpu_vram(config_path))

    # 6. 网络检查
    if not skip_network:
        net_checks = _check_network(config_path)
        report.checks.extend(net_checks)

    return report


def format_report(report: DiagnosisReport, json_output: bool = False) -> str:
    """格式化诊断报告。

    Args:
        report: 诊断报告
        json_output: 是否输出 JSON 格式

    Returns:
        格式化后的字符串
    """
    if json_output:
        return report.to_json()

    # 状态图标映射
    icons = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "skip": "⏭️ "}

    lines = []
    lines.append("🔍 RAG Builder 健康检查")
    lines.append("━" * 24)

    for check in report.checks:
        icon = icons.get(check.status, "❓")
        lines.append(f"{icon} {check.name}: {check.detail}")

    lines.append("━" * 24)

    summary = report.summary
    parts = []
    if summary["pass"]:
        parts.append(f"{summary['pass']} 通过")
    if summary["warn"]:
        parts.append(f"{summary['warn']} 警告")
    if summary["fail"]:
        parts.append(f"{summary['fail']} 错误")
    lines.append(f"结果: {', '.join(parts)}")

    return "\n".join(lines)
