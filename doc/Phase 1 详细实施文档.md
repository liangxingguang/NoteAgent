# Phase 1: 基础框架 - 详细实施文档

## 一、实施目标

Phase 1 是 LLM Wiki 功能的基础，旨在搭建核心目录结构和配置体系，为后续功能开发奠定坚实基础。

**核心交付物**：
1. LLM Wiki 核心目录结构（按日归档）
2. 配置体系设计和核心配置文件
3. Wiki 模块基础类

## 二、目录结构创建

### 2.1 目标目录结构

```
wiki/                                  # LLM Wiki 根目录
├── SCHEMA.md                         # 规则定义文档
├── index.md                          # 全局索引文档
├── log.md                            # 操作日志文档
├── raw/                              # 原始存档目录（按日归档）
│   ├── auto/                        # 自动收集内容
│   │   └── placeholder.md
│   └── manual/                      # 人工手写笔记
│       └── placeholder.md
├── structured/                       # 结构化精加工目录
│   ├── 技术类/
│   │   └── placeholder.md
│   ├── 想法类/
│   │   └── placeholder.md
│   ├── 学习类/
│   │   └── placeholder.md
│   └── 日常类/
│       └── placeholder.md
└── wiki/                            # Wiki 知识网络
    ├── entities/
    │   └── placeholder.md
    ├── concepts/
    │   └── placeholder.md
    ├── comparisons/
    │   └── placeholder.md
    └── queries/
        └── placeholder.md
```

### 2.2 创建步骤

#### 步骤 1: 创建 wiki/ 根目录及所有子目录

```bash
mkdir -p wiki/raw/auto wiki/raw/manual
mkdir -p wiki/structured/技术类 wiki/structured/想法类 wiki/structured/学习类 wiki/structured/日常类
mkdir -p wiki/wiki/entities wiki/wiki/concepts wiki/wiki/comparisons wiki/wiki/queries
```

#### 步骤 2: 创建占位符文件

为确保 Git 跟踪空目录，在每个目录中创建 `.gitkeep` 或 `placeholder.md` 文件。

#### 步骤 3: 创建 SCHEMA.md

SCHEMA.md 是 Wiki 模块的操作手册，定义内容加工、分类、索引的统一规则。

#### 步骤 4: 创建 index.md

index.md 是全局索引文档，包含内容导航和统计信息。

#### 步骤 5: 创建 log.md

log.md 是操作日志文档，仅追加不修改。

## 三、配置体系设计

### 3.1 配置维度

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| enabled | 功能开关 | false |
| wiki_root | Wiki 根目录 | wiki/ |
| archive_strategy | 归档策略 | daily |
| llm_api_key | LLM API 密钥 | - |
| llm_model | LLM 模型名称 | qwen-turbo |
| llm_base_url | LLM API 地址 | - |
| auto_process | 是否自动精加工 | true |
| auto_import_wiki | 是否自动导入 Wiki | false |
| file_monitor_enabled | 是否启用文件监控 | true |
| file_monitor_interval | 监控间隔（秒） | 5 |
| health_check_interval | 健康检查周期（天） | 7 |

### 3.2 配置文件

#### wiki_config.py

创建 `config/wiki_config.py`，定义 WikiConfig 类：

```python
@dataclass
class WikiConfig:
    """LLM Wiki 配置"""
    enabled: bool = False
    wiki_root: str = "wiki/"
    archive_strategy: str = "daily"  # daily or monthly

    llm_api_key: str = ""
    llm_model: str = "qwen-turbo"
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_retry_times: int = 3

    auto_process: bool = True
    auto_import_wiki: bool = False

    file_monitor_enabled: bool = True
    file_monitor_interval: int = 5

    health_check_interval: int = 7
```

### 3.3 环境变量

| 环境变量 | 说明 |
|----------|------|
| WIKI_ENABLED | 功能开关 |
| WIKI_ROOT | Wiki 根目录 |
| WIKI_ARCHIVE_STRATEGY | 归档策略 |
| WIKI_LLM_API_KEY | LLM API 密钥 |
| WIKI_LLM_MODEL | LLM 模型 |
| WIKI_LLM_BASE_URL | LLM API 地址 |

## 四、Wiki 模块基础类

### 4.1 模块结构

```
wiki/
├── __init__.py
├── config.py           # 配置类
├── schema.py           # SCHEMA.md 定义
├── index_manager.py    # 索引管理器
├── path_utils.py       # 路径工具（按日归档）
└── wiki.py             # Wiki 主模块
```

### 4.2 核心类

#### WikiPathManager

负责生成按日归档路径的工具类：

```python
class WikiPathManager:
    def __init__(self, wiki_root: str, archive_strategy: str = "daily"):
        self.wiki_root = wiki_root
        self.archive_strategy = archive_strategy

    def get_raw_auto_path(self, date: datetime = None) -> str:
        """获取自动收集内容的按日归档路径"""
        if self.archive_strategy == "daily":
            return self._get_daily_path("raw/auto", date)
        else:
            return self._get_monthly_path("raw/auto", date)

    def get_raw_manual_path(self, date: datetime = None) -> str:
        """获取人工手写笔记的按日归档路径"""
        if self.archive_strategy == "daily":
            return self._get_daily_path("raw/manual", date)
        else:
            return self._get_monthly_path("raw/manual", date)

    def _get_daily_path(self, prefix: str, date: datetime = None) -> str:
        """按日归档路径: prefix/YYYY/MM/DD/"""
        if date is None:
            date = datetime.now()
        return f"{prefix}/{date.year}/{date.month:02d}/{date.day:02d}/"

    def _get_monthly_path(self, prefix: str, date: datetime = None) -> str:
        """按月归档路径: prefix/YYYY/MM/"""
        if date is None:
            date = datetime.now()
        return f"{prefix}/{date.year}/{date.month:02d}/"
```

## 五、实施检查清单

### 5.1 目录结构

- [ ] wiki/ 根目录创建完成
- [ ] raw/auto/ 和 raw/manual/ 子目录创建完成
- [ ] structured/ 下四个分类目录创建完成
- [ ] wiki/wiki/ 下四个子目录创建完成
- [ ] 所有空目录包含占位符文件

### 5.2 配置文件

- [ ] WikiConfig 类定义完成
- [ ] 配置加载逻辑实现完成
- [ ] 环境变量支持实现完成

### 5.3 基础类

- [ ] WikiPathManager 类实现完成
- [ ] 按日归档路径生成正确
- [ ] 按月归档路径生成正确（兼容）

### 5.4 文档

- [ ] SCHEMA.md 创建完成
- [ ] index.md 创建完成
- [ ] log.md 创建完成

## 六、测试验证

### 6.1 目录结构测试

```python
def test_wiki_directory_structure():
    """测试 Wiki 目录结构是否正确创建"""
    assert os.path.exists("wiki/")
    assert os.path.exists("wiki/raw/auto/")
    assert os.path.exists("wiki/raw/manual/")
    assert os.path.exists("wiki/structured/技术类/")
    assert os.path.exists("wiki/structured/想法类/")
    assert os.path.exists("wiki/structured/学习类/")
    assert os.path.exists("wiki/structured/日常类/")
    assert os.path.exists("wiki/wiki/entities/")
    assert os.path.exists("wiki/wiki/concepts/")
    assert os.path.exists("wiki/wiki/comparisons/")
    assert os.path.exists("wiki/wiki/queries/")
```

### 6.2 路径生成测试

```python
def test_daily_archive_path():
    """测试按日归档路径生成"""
    from wiki.path_utils import WikiPathManager

    manager = WikiPathManager("wiki/", "daily")
    path = manager.get_raw_auto_path(datetime(2026, 5, 3))
    assert path == "raw/auto/2026/05/03/"

def test_monthly_archive_path():
    """测试按月归档路径生成"""
    from wiki.path_utils import WikiPathManager

    manager = WikiPathManager("wiki/", "monthly")
    path = manager.get_raw_auto_path(datetime(2026, 5, 3))
    assert path == "raw/auto/2026/05/"
```

## 七、预估工作量

| 任务 | 预估时间 |
|------|----------|
| 创建目录结构 | 10 分钟 |
| 创建占位符文件 | 5 分钟 |
| 实现 WikiConfig 配置类 | 20 分钟 |
| 实现 WikiPathManager | 15 分钟 |
| 创建 SCHEMA.md | 15 分钟 |
| 创建 index.md | 5 分钟 |
| 创建 log.md | 5 分钟 |
| 单元测试 | 15 分钟 |
| **总计** | **约 90 分钟** |

## 八、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 目录权限问题 | 高 | 预先检查并创建必要目录 |
| 配置加载失败 | 中 | 提供合理的默认值 |
| 按日归档路径格式不一致 | 中 | WikiPathManager 统一管理 |

## 九、后续阶段依赖

Phase 1 是所有后续阶段的基础：

- **Phase 2**: 依赖 WikiConfig 和 WikiPathManager
- **Phase 3**: 依赖 index.md 和 index_manager.py
- **Phase 4**: 依赖 raw/manual/ 目录和文件监控
- **Phase 5**: 依赖 wiki/wiki/ 目录结构
- **Phase 6**: 依赖所有模块正常工作
