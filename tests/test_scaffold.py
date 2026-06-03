"""Tests for rag_builder.scaffold — 项目骨架生成测试。"""

import json

from rag_builder.config_schema import ChunkingConfig, EmbeddingConfig, RAGConfig
from rag_builder.scaffold import scaffold_project


class TestScaffoldProject:
    """项目骨架生成测试。"""

    def test_generates_all_files(self, tmp_path):
        """应生成所有必要的文件。"""
        config = RAGConfig()
        files = scaffold_project(config, str(tmp_path), "test-rag")

        expected_files = {"ingest.py", "query.py", "config.py", "README.md",
                          "requirements.txt", "rag_config.json"}
        assert set(files.keys()) == expected_files, (
            f"应生成 {expected_files}，实际: {set(files.keys())}"
        )

    def test_creates_project_directory(self, tmp_path):
        """应在输出目录下创建项目子目录。"""
        config = RAGConfig()
        scaffold_project(config, str(tmp_path), "my-project")

        project_dir = tmp_path / "my-project"
        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_ingest_contains_chunk_size(self, tmp_path):
        """生成的 ingest.py 应包含配置的 chunk_size。"""
        config = RAGConfig(chunking=ChunkingConfig(chunk_size=1024))
        files = scaffold_project(config, str(tmp_path), "test-rag")

        assert "1024" in files["ingest.py"], "ingest.py 应包含 chunk_size=1024"

    def test_config_contains_embedding_model(self, tmp_path):
        """生成的 config.py 应包含配置的嵌入模型名。"""
        config = RAGConfig(embedding=EmbeddingConfig(model="bge-m3"))
        files = scaffold_project(config, str(tmp_path), "test-rag")

        assert "bge-m3" in files["config.py"], "config.py 应包含 bge-m3"

    def test_readme_contains_project_name(self, tmp_path):
        """生成的 README.md 应包含项目名称。"""
        config = RAGConfig()
        files = scaffold_project(config, str(tmp_path), "awesome-rag")

        assert "awesome-rag" in files["README.md"], "README.md 应包含项目名"

    def test_rag_config_json_is_valid_json(self, tmp_path):
        """生成的 rag_config.json 应是合法 JSON。"""
        config = RAGConfig()
        files = scaffold_project(config, str(tmp_path), "test-rag")

        data = json.loads(files["rag_config.json"])
        assert "chunking" in data
        assert "embedding" in data
        assert "vector_store" in data
        assert "retriever" in data
        assert "query" in data

    def test_ingest_py_is_valid_python(self, tmp_path):
        """生成的 ingest.py 应是合法 Python。"""
        config = RAGConfig()
        files = scaffold_project(config, str(tmp_path), "test-rag")

        # compile 验证语法
        compile(files["ingest.py"], "ingest.py", "exec")

    def test_query_py_is_valid_python(self, tmp_path):
        """生成的 query.py 应是合法 Python。"""
        config = RAGConfig()
        files = scaffold_project(config, str(tmp_path), "test-rag")

        compile(files["query.py"], "query.py", "exec")

    def test_config_py_is_valid_python(self, tmp_path):
        """生成的 config.py 应是合法 Python。"""
        config = RAGConfig()
        files = scaffold_project(config, str(tmp_path), "test-rag")

        compile(files["config.py"], "config.py", "exec")

    def test_custom_config_values_appear_in_output(self, tmp_path):
        """自定义配置值应出现在生成的文件中。"""
        config = RAGConfig(
            chunking=ChunkingConfig(chunk_size=256, chunk_overlap=32, min_chunk_size=20),
        )
        files = scaffold_project(config, str(tmp_path), "test-rag")

        # ingest.py 应包含自定义值
        assert "256" in files["ingest.py"]
        assert "32" in files["ingest.py"]
        assert "20" in files["ingest.py"]

    def test_files_written_to_disk(self, tmp_path):
        """生成的文件应实际写入磁盘。"""
        config = RAGConfig()
        scaffold_project(config, str(tmp_path), "test-rag")

        project_dir = tmp_path / "test-rag"
        assert (project_dir / "ingest.py").exists()
        assert (project_dir / "query.py").exists()
        assert (project_dir / "config.py").exists()
        assert (project_dir / "README.md").exists()
        assert (project_dir / "requirements.txt").exists()
        assert (project_dir / "rag_config.json").exists()

    def test_nonexistent_parent_dir_created(self, tmp_path):
        """输出目录不存在时应自动创建。"""
        config = RAGConfig()
        deep_path = tmp_path / "a" / "b" / "c"
        scaffold_project(config, str(deep_path), "test-rag")

        assert (deep_path / "test-rag" / "ingest.py").exists()
