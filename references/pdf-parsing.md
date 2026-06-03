# PDF 解析方案对比

## 方案选型

| 方案 | 适用场景 | 安装 | 输出格式 |
|------|---------|------|---------|
| **pymupdf** | 简单 PDF，纯文本提取 | `pip install pymupdf` | 按页文本 |
| **marker-pdf** | 复杂排版，OCR 需求 | `pip install marker-pdf` | Markdown |
| **MinerU** | 学术论文，表格/公式 | Docker: `opendatalab/mineru` | content_list.json |
| **unstructured** | 通用文档 | `pip install unstructured` | 元素列表 |

## pymupdf 快速提取

```python
import fitz  # pymupdf

def extract_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({"text": text, "page": i + 1, "source": pdf_path})
    return pages
```

## MinerU Docker 解析（复杂 PDF）

```bash
docker run --rm --gpus all \
  -v /path/to/pdfs:/data \
  opendatalab/mineru:latest \
  mineru -p /data/file.pdf -o /data/output -b pipeline
```

content_list.json 结构：
```json
[
  {"type": "text", "text": "正文内容...", "page_idx": 0},
  {"type": "table", "table_body": "<html>...</html>", "page_idx": 1}
]
```

## Markdown/纯文本

```python
from pathlib import Path

def load_text_files(directory: str) -> list[dict]:
    docs = []
    for ext in ["*.md", "*.txt"]:
        for f in Path(directory).glob(f"**/{ext}"):
            text = f.read_text(encoding="utf-8", errors="ignore")
            docs.append({"text": text, "source": str(f)})
    return docs
```

## 表格特殊处理

表格不适合常规分块，应保持完整：

```python
def chunk_with_tables(content_list: list[dict], chunk_size: int = 512) -> list[dict]:
    chunks = []
    for item in content_list:
        if item.get("type") == "table":
            chunks.append({"text": item["table_body"], "type": "table", "page": item.get("page_idx")})
        else:
            text = item.get("text", "")
            for chunk_text in recursive_split(text, chunk_size):
                chunks.append({"text": chunk_text, "type": "text"})
    return chunks
```
