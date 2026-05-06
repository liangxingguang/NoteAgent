# Phase 5: Wiki 知识网络 - 详细实施文档

## 一、实施目标

实现 Wiki 知识网络（Karpathy 范式），包括：
- 导入：从笔记提取实体、概念，建立关系
- 查询：查询相关知识
- 健康检查：识别孤立页面、断裂链接等

## 二、知识网络设计

### 数据模型

```python
@dataclass
class Entity:
    name: str
    description: str
    tags: List[str]
    linked_notes: List[str]
    created_at: datetime

@dataclass
class Concept:
    name: str
    definition: str
    related_concepts: List[str]
    linked_notes: List[str]
    created_at: datetime
```

### 目录结构

```
wiki_data/
└── wiki/
    ├── entities/       # 实体页面
    ├── concepts/       # 概念页面
    ├── comparisons/    # 对比页面
    └── queries/        # 查询历史
```

## 三、核心功能

### 1. 知识导入
- 扫描所有笔记
- 从关键词提取实体和概念
- 建立关系图
- 生成知识页面

### 2. 知识查询
- 按关键词检索
- 相关笔记推荐
- 概念关联查询

### 3. 健康检查
- 孤立页面检查
- 断裂链接检查
- 过时内容提醒

## 四、实施检查清单
- [ ] 数据模型（Entity, Concept）
- [ ] 知识导入功能
- [ ] 知识查询功能
- [ ] 健康检查功能
- [ ] 完整测试
