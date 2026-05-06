# Phase 3: 索引管理 - 详细实施文档

## 一、实施目标

实现全局索引管理，自动更新 `index.md` 和生成统计信息！

## 二、IndexManager 核心功能

| 功能 | 说明 |
|------|------|
| **扫描笔记** | 扫描 structured/ 下的所有笔记 |
| **生成索引** | 自动更新 index.md |
| **分类统计** | 按技术类、想法类、学习类、日常类统计数量 |
| **时间线** | 生成笔记时间线 |
| **关键词统计** | 热门关键词展示 |

## 三、IndexManager 设计

```python
class IndexManager:
    def __init__(self, path_manager: WikiPathManager):
        pass
    def scan_notes(self) -> list[StructuredNote]:
        # 扫描笔记
        pass
    def generate_index(self, notes: list[StructuredNote]) -> str:
        # 生成 Markdown 索引
        pass
    def update_index(self):
        # 更新 index.md
        pass
```

## 四、index.md 格式

```markdown
# Wiki 索引

## 统计

- 总笔记数: 15
- 技术类: 8
- 想法类: 3
- 学习类: 2
- 日常类: 2

## 分类索引

### 技术类
- [标题1](技术类/20260503_xxx.md)
- [标题2](技术类/20260503_yyy.md)

## 时间线

- 2026-05-03: [标题1](...), [标题2](...)

## 热门关键词
- Python (5)
- 学习 (3)
- 思考 (2)
```

## 五、实施检查清单

- [ ] IndexManager 基础类
- [ ] 扫描笔记功能
- [ ] 统计功能（分类、时间线）
- [ ] index.md 生成
- [ ] 测试
