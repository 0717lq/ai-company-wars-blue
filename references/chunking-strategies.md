# 分块策略

## 策略对比

| 策略 | 原理 | 适用场景 | 推荐 |
|------|------|---------|------|
| **recursive** | 按段落→句子→字符递归切分 | 通用文本 | ⭐ 默认首选 |
| **semantic** | 语义相似度切分 | 主题跳跃多的文档 | 效果好但慢 |
| **by_title** | 按标题层级切分 | 结构化文档（Markdown） | 技术文档推荐 |
| **fixed_size** | 固定字符数切分 | 简单场景 | 不推荐 |

## Recursive 分块实现

```python
def recursive_split(text: str, chunk_size: int = 512, overlap: int = 128) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    separators = ["\n\n", "\n", "。", ".", " "]
    return _split_recursive(text, separators, chunk_size, overlap)

def _split_recursive(text, separators, chunk_size, overlap):
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    sep = separators[0]
    parts = text.split(sep)
    result, current = [], ""
    for part in parts:
        candidate = current + sep + part if current else part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                result.append(current)
            if len(part) > chunk_size:
                result.extend(_split_recursive(part, separators[1:], chunk_size, overlap))
            else:
                current = part
    if current:
        result.append(current)
    if overlap > 0 and len(result) > 1:
        overlapped = [result[0]]
        for i in range(1, len(result)):
            overlapped.append(result[i-1][-overlap:] + result[i])
        result = overlapped
    return result
```

## 分块参数经验值

| 文档类型 | chunk_size | chunk_overlap | 说明 |
|---------|-----------|---------------|------|
| 通用文本 | 512 | 128 | 默认值 |
| 技术文档 | 1024 | 256 | 代码块较长 |
| 法律/合同 | 256 | 64 | 精确条款匹配 |
| 学术论文 | 512 | 128 | 与通用相同 |
| 对话记录 | 384 | 128 | 保留对话上下文 |

## Overlap 原则

overlap = chunk_size 的 20-25%。过大 → chunk 高度重复 → 检索结果冗余 → 浪费 reranker 算力。
