# Phase 4: 文件监控 - 详细实施文档

## 一、实施目标

实现文件监控，自动检测 `raw/manual/` 下的新文件/改动，触发完整流程！
- 监控：检测新文件/修改
- 触发：调用 Pipeline 加工
- 更新：自动更新索引

## 二、FileWatcher 设计

```python
class FileWatcher:
    def __init__(self, path_manager: WikiPathManager, config: WikiConfig):
        pass
    def start(self):
        # 后台监控
        pass
    def process_new_file(self, file_path: str):
        # 处理新文件
        pass
```

## 三、完整工作流

```
新文件/改动 → FileWatcher 检测 →
→ Pipeline 加工 → NoteSaver 保存 → IndexManager 更新索引 → 完成
```

## 四、实施检查清单

- [ ] FileWatcher 基础类
- [ ] 文件监控（新文件/修改）
- [ ] 完整工作流集成
- [ ] 测试
