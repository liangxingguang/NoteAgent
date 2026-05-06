# 基于Telegram（TG）的AI笔记自动收集系统功能设计文档（Python版）

# 1\. 文档概述

## 1\.1 文档目的

本文档基于《基于Telegram（TG）的AI笔记自动收集系统架构设计文档》，进一步细化系统功能，明确Python项目结构、各模块功能点、接口定义、功能约束及交互逻辑，为Python开发提供明确的功能指引，确保开发过程贴合需求、代码结构清晰、功能可落地。

## 1\.2 核心定位

本系统采用Python开发，核心实现「TG客户端发送内容→TG机器人接收→第三方AI总结→Obsidian自动入库」的全自动化链路，聚焦个人使用场景，兼顾易用性、稳定性和可扩展性，无需人工干预，实现个人知识库的自动化收集与整理。

## 1\.3 适用范围

本文档适用于本系统的Python开发人员、测试人员及运维人员，作为开发编码、功能测试、系统部署的核心依据；文档内容严格对应架构设计文档的分层逻辑，不新增架构外功能，仅细化各层功能实现细节。

## 1\.4 技术栈说明

本项目采用Python 3\.8\+开发，核心技术栈如下，确保轻量、易维护、可落地：

- 核心框架：python\-telegram\-bot（TG机器人接入与消息处理）

- 请求库：requests（调用第三方大模型API、TG API）

- 文件解析：PyPDF2（PDF文本提取）、python\-docx（Word文本提取）

- 配置管理：python\-dotenv（环境变量管理，避免硬编码）

- 后台常驻：Linux systemd（进程守护，开机自启、断线重连）

- 日志管理：logging（Python内置日志模块，记录系统运行状态）

# 2\. 项目结构设计（Python版）

项目采用模块化设计，严格对应架构设计文档的分层逻辑，结构清晰、松耦合，便于开发、测试和维护，具体项目目录结构如下（按功能模块划分）：

```plain text
tg_ai_note_bot/                  # 项目根目录
├── config/                      # 配置模块（对应基础设施层-配置管理）
│   ├── __init__.py              # 模块初始化
│   └── config.py                # 配置加载（环境变量、常量定义）
├── tg_access/                   # TG接入模块（对应接入层）
│   ├── __init__.py              # 模块初始化
│   ├── bot_handler.py           # TG机器人实例化、消息监听、反馈
│   ├── message_parser.py        # 消息解析（区分文本/文件，提取核心信息）
│   └── permission_checker.py    # 权限校验（合法用户校验）
├── business/                    # 业务逻辑模块（对应业务逻辑层）
│   ├── __init__.py              # 模块初始化
│   ├── file_processor.py        # 文件处理（下载、文本提取、临时文件清理）
│   ├── ai_summarizer.py         # AI总结（调用第三方大模型，生成Obsidian笔记）
│   ├── obsidian_writer.py       # Obsidian入库（生成笔记、写入本地目录）
│   └── exception_handler.py     # 异常处理（捕获全链路异常，记录日志）
├── storage/                     # 存储模块（对应数据存储层）
│   ├── __init__.py              # 模块初始化
│   ├── temp_manager.py          # 临时文件管理（创建、清理）
│   └── log_manager.py           # 日志管理（日志配置、记录）
├── utils/                       # 工具模块（通用工具函数）
│   ├── __init__.py              # 模块初始化
│   ├── file_utils.py            # 文件操作工具（格式判断、大小校验）
│   ├── text_utils.py            # 文本处理工具（截断、去重、哈希生成）
│   └── api_utils.py             # API调用工具（请求封装、超时处理）
├── .env                         # 环境变量配置文件（不提交代码，本地配置）
├── .env.example                 # 环境变量示例文件（提示配置项）
├── requirements.txt             # 项目依赖库清单
├── main.py                      # 项目入口文件（启动机器人、初始化各模块）
└── README.md                    # 项目说明文档（部署步骤、注意事项）
```

## 2\.1 各目录核心职责说明

- config/：统一管理系统配置，加载\.env环境变量（TG Token、AI API Key、Obsidian路径等），定义系统常量（文件大小限制、文本截断长度等），避免硬编码，提升可维护性。

- tg\_access/：负责与TG官方API对接，实现机器人实例化、消息监听、消息解析和权限校验，是系统与TG平台的核心交互入口。

- business/：系统核心业务逻辑模块，串联接入层、存储层和第三方服务，实现文件处理、AI总结、Obsidian入库及异常处理，是系统功能的核心实现层。

- storage/：负责临时文件管理和日志管理，确保临时文件及时清理、日志规范记录，支撑系统稳定运行。

- utils/：提供通用工具函数，供各模块调用，减少代码冗余，提升开发效率（如文件格式判断、文本哈希生成、API请求封装等）。

- 根目录文件：项目入口（main\.py）、依赖清单（requirements\.txt）、环境变量配置（\.env）及项目说明（README\.md），是项目部署和启动的核心文件。

# 3\. 详细功能设计（按模块划分）

## 3\.1 配置模块（config/）

### 3\.1\.1 功能定位

统一加载和管理系统所有配置，提供配置访问接口，确保各模块配置统一、可修改，避免硬编码带来的维护成本。

### 3\.1\.2 核心功能点

1. 环境变量加载：通过python\-dotenv加载\.env文件中的环境变量，包括TG机器人配置、第三方AI配置、Obsidian配置、权限配置等。

2. 常量定义：定义系统固定常量，如文件大小限制（MAX\_FILE\_SIZE=50\*1024\*1024，即50MB）、文本截断长度（MAX\_TEXT\_LENGTH=5000）、日志存储路径等。

3. 配置提供：对外提供统一的配置访问接口，供其他模块调用（如获取TG Token、AI API Key、合法用户ID等）。

4. 配置校验：启动时校验核心配置是否缺失（如TG Token、AI API Key），若缺失则报错并终止程序，避免运行时异常。

### 3\.1\.3 核心接口（config\.py）

- load\_config\(\)：加载\.env环境变量，初始化配置字典，返回配置对象。

- get\_config\(key\)：根据key获取对应的配置值（如get\_config\(\&\#34;TG\_BOT\_TOKEN\&\#34;\)）。

- validate\_config\(\)：校验核心配置是否齐全，若缺失则抛出异常。

## 3\.2 TG接入模块（tg\_access/）

### 3\.2\.1 功能定位

实现与TG官方API的对接，负责机器人的启动、消息监听、消息解析、权限校验和消息反馈，是系统与用户交互的核心入口，对应架构设计中的接入层。

### 3\.2\.2 子模块功能设计

#### 3\.2\.2\.1 机器人处理模块（bot\_handler\.py）

1. 机器人实例化：使用python\-telegram\-bot库，通过TG Token初始化机器人实例，配置消息处理器。

2. 消息监听：采用Polling模式（无需公网IP/域名），实时监听用户发送的所有消息，触发对应的消息处理逻辑。

3. 消息反馈：向用户发送处理结果（入库成功提示、失败原因、文件校验提示等），支持文本消息反馈。

4. 机器人启动/停止：提供机器人启动、停止接口，配合main\.py实现程序入口，支持后台常驻。

#### 3\.2\.2\.2 消息解析模块（message\_parser\.py）

1. 消息类型判断：解析TG消息对象，区分文本消息、链接消息、文件消息（PDF/Word/TXT），返回消息类型及核心信息。

2. 文本/链接提取：从文本消息中提取纯文本内容、链接信息，去除无关符号（如TG消息中的格式符号）。

3. 文件信息提取：从文件消息中提取文件名称、文件大小、文件格式、文件ID（file\_id），为文件下载提供基础信息。

4. 消息预处理：对提取的文本/文件信息进行初步清洗（如去除空格、换行符），便于后续业务逻辑处理。

#### 3\.2\.2\.3 权限校验模块（permission\_checker\.py）

1. 合法用户校验：获取发送消息的用户ID，与配置中的ALLOWED\_USER\_ID进行比对，判断是否为合法用户。

2. 权限拦截：对非法用户的消息进行拦截，不执行后续业务逻辑，同时向用户发送无权限提示。

3. 权限配置：支持单个合法用户配置，后续可扩展为多用户权限管理（如管理员、普通用户）。

### 3\.2\.3 核心接口

- bot\_handler\.py：init\_bot\(\)（初始化机器人）、start\_bot\(\)（启动机器人）、send\_feedback\(chat\_id, message\)（发送反馈消息）。

- message\_parser\.py：parse\_message\(message\)（解析消息，返回消息类型及核心信息）、extract\_file\_info\(file\_message\)（提取文件信息）。

- permission\_checker\.py：check\_permission\(user\_id\)（校验用户权限，返回布尔值）。

## 3\.3 业务逻辑模块（business/）

### 3\.3\.1 功能定位

系统核心业务逻辑实现层，串联TG接入层、存储层及第三方大模型服务，实现文件处理、AI总结、Obsidian入库及异常处理，对应架构设计中的业务逻辑层。

### 3\.3\.2 子模块功能设计

#### 3\.3\.2\.1 文件处理模块（file\_processor\.py）

1. 文件校验：根据配置的文件大小限制（50MB）和格式限制（PDF/Word/TXT），校验用户发送的文件是否符合要求，不符合则触发异常。

2. 文件下载：通过TG API（get\_file、download\_file），根据文件ID下载文件至服务器临时目录，返回文件本地路径。

3. 文本提取：根据文件格式，调用对应的解析库提取文本内容（PDF用PyPDF2、Word用python\-docx、TXT直接读取）。

4. 文本截断：若提取的文本长度超过配置的MAX\_TEXT\_LENGTH（5000字），自动截断，避免AI API请求超限。

5. 临时文件清理：文件处理完成后（无论成功/失败），自动删除临时目录中的文件，释放服务器空间。

#### 3\.3\.2\.2 AI总结模块（ai\_summarizer\.py）

1. 提示词构造：根据文本内容（文本/文件提取结果），构造符合Obsidian笔记格式的提示词（包含标题、摘要、关键词、正文的模板要求）。

2. 第三方AI调用：调用第三方大模型API（通义千问/GPT\-3\.5等），传入提示词和文本内容，设置超时时间（30秒），避免请求阻塞。

3. 总结结果校验：接收AI返回的总结结果，校验结果格式是否符合Obsidian笔记要求，若不符合则进行格式修正。

4. 模型切换（可扩展）：支持多第三方模型切换，根据配置中的模型类型，调用对应的API，提升灵活性。

#### 3\.3\.2\.3 Obsidian入库模块（obsidian\_writer\.py）

1. 文件名生成：根据文本内容的哈希值\+时间戳，生成唯一的Markdown文件名（如“TG收集\_20240520\-153000\_abc123\.md”），避免文件重复。

2. 笔记写入：将AI总结后的内容，写入Obsidian知识库目录（配置中的OBSIDIAN\_DIR），确保文件编码为UTF\-8，适配Obsidian客户端。

3. 目录校验：写入前校验Obsidian目录是否存在、是否具备可读写权限，若不存在则自动创建目录，若权限不足则触发异常。

4. 入库记录：记录笔记入库信息（文件名、入库时间、来源内容），便于后续追溯。

#### 3\.3\.2\.4 异常处理模块（exception\_handler\.py）

1. 异常捕获：捕获全链路异常，包括TG API调用异常、文件下载异常、文件解析异常、AI API调用异常、Obsidian入库异常等。

2. 异常分类：将异常分为可恢复异常（如网络波动导致的API调用失败）和不可恢复异常（如配置缺失、权限不足），分别处理。

3. 日志记录：将异常信息（异常类型、异常信息、发生时间、触发模块）记录至日志文件，便于问题排查。

4. 异常反馈：将可恢复异常的处理建议、不可恢复异常的原因，通过TG机器人反馈给用户，提升用户体验。

### 3\.3\.3 核心接口

- file\_processor\.py：process\_file\(file\_info\)（处理文件，返回提取的文本内容）、clean\_temp\_file\(file\_path\)（清理临时文件）。

- ai\_summarizer\.py：summarize\(content, title\)（调用AI总结，返回标准化笔记内容）。

- obsidian\_writer\.py：write\_note\(content\)（写入Obsidian笔记，返回文件名）、generate\_filename\(content\)（生成唯一文件名）。

- exception\_handler\.py：handle\_exception\(exception, module\)（处理异常，记录日志并反馈用户）。

## 3\.4 存储模块（storage/）

### 3\.4\.1 功能定位

负责系统数据的持久化存储和资源管理，包括临时文件管理和日志管理，对应架构设计中的数据存储层，保障系统稳定运行。

### 3\.4\.2 子模块功能设计

#### 3\.4\.2\.1 临时文件管理模块（temp\_manager\.py）

1. 临时目录创建：初始化系统时，创建临时文件目录（如\./temp\_files），若目录已存在则跳过。

2. 临时文件管理：记录临时文件的路径和创建时间，便于后续清理。

3. 自动清理：支持定时清理（可配置清理周期，如每天凌晨），删除过期临时文件（如创建时间超过24小时的文件），避免空间溢出。

4. 手动清理：提供手动清理接口，供其他模块调用（如文件处理完成后立即清理）。

#### 3\.4\.2\.2 日志管理模块（log\_manager\.py）

1. 日志配置：配置日志格式（时间、模块、日志级别、日志内容）、日志存储路径（如\./logs）、日志滚动规则（按日期滚动，单个日志文件最大10MB）。

2. 日志记录：提供不同级别的日志记录接口（DEBUG、INFO、WARNING、ERROR、CRITICAL），各模块根据需求调用。

3. 日志分级：
        

    - DEBUG：记录系统运行细节（如机器人启动、消息接收、API调用请求），用于开发调试。

    - INFO：记录系统正常运行状态（如入库成功、文件处理完成），用于日常运维。

    - WARNING：记录潜在风险（如文件过大、文本截断），不影响系统运行，但需关注。

    - ERROR：记录系统异常（如API调用失败、入库失败），影响单个功能执行，不影响整体运行。

    - CRITICAL：记录严重异常（如配置缺失、机器人启动失败），影响系统整体运行，需立即处理。

4. 日志查看：支持日志文件按日期命名，便于按时间范围查看日志，排查问题。

### 3\.4\.3 核心接口

- temp\_manager\.py：init\_temp\_dir\(\)（初始化临时目录）、clean\_expired\_temp\_files\(\)（清理过期临时文件）、delete\_temp\_file\(file\_path\)（删除指定临时文件）。

- log\_manager\.py：init\_logger\(\)（初始化日志配置）、log\_debug\(module, message\)（记录DEBUG日志）、log\_error\(module, message\)（记录ERROR日志）等。

## 3\.5 工具模块（utils/）

### 3\.5\.1 功能定位

提供通用工具函数，供各模块调用，减少代码冗余，提升开发效率，统一工具类实现，便于维护和扩展。

### 3\.5\.2 子模块功能设计

#### 3\.5\.2\.1 文件操作工具（file\_utils\.py）

1. 文件格式判断：根据文件后缀，判断文件是否为支持的格式（PDF/Word/TXT），返回布尔值。

2. 文件大小校验：根据文件大小，判断是否超过配置的最大限制，返回布尔值。

3. 目录权限校验：校验指定目录是否具备可读写权限，返回布尔值。

4. 文件哈希生成：根据文件内容或文本内容，生成MD5哈希值，用于生成唯一文件名。

#### 3\.5\.2\.2 文本处理工具（text\_utils\.py）

1. 文本截断：将过长的文本按指定长度截断，保留核心内容，避免API请求超限。

2. 文本清洗：去除文本中的无关符号（如换行符、空格、特殊符号），优化文本质量。

3. 关键词提取（简单版）：从文本中提取核心关键词（基于字符串频率），辅助AI总结。

4. 时间戳生成：生成指定格式的时间戳（如“20240520\-153000”），用于文件名和日志记录。

#### 3\.5\.2\.3 API调用工具（api\_utils\.py）

1. 请求封装：封装requests库的GET/POST请求，统一处理请求头、超时时间、异常捕获，减少重复代码。

2. API响应解析：解析第三方API返回的JSON响应，提取核心数据，处理响应异常（如返回码非200）。

3. 重试机制：对可恢复的API调用失败（如网络波动），实现自动重试（最多3次），提升API调用成功率。

### 3\.5\.3 核心接口

- file\_utils\.py：is\_supported\_file\(file\_name\)（判断文件格式是否支持）、check\_file\_size\(file\_size\)（校验文件大小）、get\_file\_hash\(file\_path\)（生成文件哈希）。

- text\_utils\.py：truncate\_text\(text, max\_length\)（文本截断）、clean\_text\(text\)（文本清洗）、generate\_timestamp\(\)（生成时间戳）。

- api\_utils\.py：send\_post\_request\(url, headers, data, timeout=30\)（发送POST请求）、send\_get\_request\(url, headers, params, timeout=30\)（发送GET请求）。

## 3\.6 项目入口模块（main\.py）

### 3\.6\.1 功能定位

项目核心入口，负责初始化各模块、启动机器人、监听系统信号，实现系统的整体启动和运行。

### 3\.6\.2 核心功能点

1. 模块初始化：按顺序初始化配置模块、日志模块、临时文件模块、TG机器人模块，确保各模块正常加载。

2. 机器人启动：调用tg\_access模块的start\_bot\(\)方法，启动TG机器人，开始监听消息。

3. 信号监听：监听Linux系统信号（如SIGINT、SIGTERM），实现机器人的优雅停止（停止消息监听、清理临时文件、记录日志）。

4. 异常捕获：捕获项目启动过程中的全局异常，记录日志并退出程序，避免异常导致程序崩溃。

# 4\. 核心业务流程功能拆解（对应架构流程）

结合架构设计文档的核心流程，将「用户发送内容→机器人接收→AI总结→入库反馈」的全链路，拆解为具体的功能步骤，明确各模块的交互逻辑：

## 4\.1 文本/链接处理流程

1. 用户操作：用户通过TG客户端，向机器人发送纯文本或链接。

2. 消息接收：tg\_access\.bot\_handler监听消息，触发消息处理逻辑。

3. 权限校验：tg\_access\.permission\_checker校验用户ID，若为非法用户，发送无权限反馈，流程终止。

4. 消息解析：tg\_access\.message\_parser解析消息，提取纯文本/链接内容，进行预处理。

5. AI总结：business\.ai\_summarizer调用第三方大模型，传入文本内容，生成Obsidian标准化笔记。

6. Obsidian入库：business\.obsidian\_writer生成唯一文件名，将笔记写入Obsidian目录。

7. 结果反馈：tg\_access\.bot\_handler向用户发送入库成功提示（含文件名）。

8. 日志记录：storage\.log\_manager记录整个流程的INFO日志，包括消息内容、入库文件名。

## 4\.2 文件处理流程

1. 用户操作：用户通过TG客户端，向机器人发送PDF/Word/TXT文件。

2. 消息接收：tg\_access\.bot\_handler监听消息，触发消息处理逻辑。

3. 权限校验：tg\_access\.permission\_checker校验用户ID，非法用户则反馈并终止流程。

4. 消息解析：tg\_access\.message\_parser解析文件消息，提取文件名称、大小、格式、file\_id。

5. 文件校验：business\.file\_processor校验文件大小（≤50MB）和格式（支持的类型），不符合则反馈并终止流程。

6. 文件下载：business\.file\_processor通过TG API下载文件至临时目录，记录临时文件路径。

7. 文本提取：business\.file\_processor提取文件中的文本内容，过长则自动截断。

8. AI总结：business\.ai\_summarizer调用第三方大模型，传入提取的文本，生成标准化笔记。

9. Obsidian入库：business\.obsidian\_writer将笔记写入Obsidian目录，生成唯一文件名。

10. 临时文件清理：business\.file\_processor调用storage\.temp\_manager，删除临时文件。

11. 结果反馈：tg\_access\.bot\_handler向用户发送处理成功提示（含文件名）。

12. 日志记录：storage\.log\_manager记录流程日志，包括文件信息、入库结果。

## 4\.3 异常处理流程

1. 异常触发：在上述任意流程中，若出现异常（如API调用失败、文件解析失败、入库失败），触发business\.exception\_handler。

2. 异常捕获：exception\_handler捕获异常，记录ERROR日志（异常类型、原因、触发模块）。

3. 异常处理：根据异常类型，判断是否可恢复（如网络波动则重试，配置缺失则终止）。

4. 用户反馈：向用户发送异常提示，告知失败原因（如“文件下载失败，请重试”）。

5. 资源清理：若异常发生在文件处理环节，自动清理临时文件，避免资源占用。

# 5\. 功能约束与限制

## 5\.1 功能约束

- 文件支持：仅支持PDF、Word（docx）、TXT三种格式，不支持图片、视频、压缩包等其他格式；文件大小≤50MB（TG官方Bot API限制）。

- 文本限制：提取的文件文本超过5000字将自动截断，避免AI API请求超限；纯文本消息无长度限制（TG官方限制内）。

- 权限限制：仅支持单个合法用户使用，后续可扩展多用户权限；非法用户无法触发任何业务逻辑。

- AI限制：依赖第三方大模型API，API失效、欠费或网络中断时，AI总结功能无法使用；总结结果受模型能力影响，可能需要手动微调。

- 网络限制：服务器需能访问TG官方API和第三方大模型API，国内服务器需科学上网；网络中断时，机器人无法接收/发送消息，网络恢复后自动重连。

## 5\.2 不支持的功能

- 不支持图片、视频、音频、压缩包等非文本类文件的处理（无OCR、字幕提取功能）。

- 不支持多机器人同时运行，仅部署单个TG机器人。

- 不支持Obsidian笔记的自动同步（需用户手动配置Git插件或其他同步工具）。

- 不支持敏感内容过滤（依赖第三方大模型自身的敏感内容过滤机制）。

- 不支持批量处理文件，仅支持单文件逐一处理。

# 6\. 可扩展功能设计

基于当前功能设计，预留以下可扩展功能，便于后续升级优化，贴合架构设计文档的可扩展性要求。以下为各可扩展功能的具体详细实现方案，严格对接现有Python项目结构，明确依赖技术、核心逻辑、实现步骤及关联模块，确保开发可落地、可复用。

## 6\.1 文件格式扩展：图片OCR识别与视频字幕提取

依赖技术：阿里云OCR API（或百度OCR API）、pytube（视频下载）、pysrt（字幕解析）、moviepy（视频处理，可选）。

核心实现逻辑：

- 新增OCR处理模块：在business模块下新增ocr\_processor\.py，封装OCR API调用逻辑，接收图片文件路径，返回识别后的文本内容。

- 图片处理适配：修改tg\_access/message\_parser\.py，新增图片消息类型判断，提取图片file\_id；修改business/file\_processor\.py，新增图片下载逻辑，下载至临时目录后调用ocr\_processor\.py提取文本。

- 视频字幕提取：在business模块下新增video\_processor\.py，通过pytube下载视频（或提取视频中的字幕文件），使用pysrt解析srt字幕文件，提取纯文本；若视频无内置字幕，可集成语音转文字API（如阿里云语音识别），先提取音频再转文字。

- 格式校验扩展：修改utils/file\_utils\.py的is\_supported\_file\(\)方法，新增图片格式（jpg、png、jpeg）、视频格式（mp4、mov）的判断逻辑。

关联模块：tg\_access/message\_parser\.py、business/file\_processor\.py、utils/file\_utils\.py，新增business/ocr\_processor\.py、business/video\_processor\.py。

注意事项：OCR API需申请API Key，配置至\.env文件；视频下载需考虑文件大小，建议新增视频大小限制（如≤200MB）；语音转文字需处理音频格式转换问题。

## 6\.2 AI模型扩展：多第三方模型切换

依赖技术：通义千问API、文心一言API、OpenAI API（GPT\-3\.5/4），requests库（已集成）。

核心实现逻辑：

- 配置扩展：修改config/config\.py，新增AI模型配置项（AI\_MODEL\_TYPE），支持配置“qwen”“ernie”“gpt”三种类型；在\.env文件中新增对应模型的API Key（如ERNIE\_API\_KEY、OPENAI\_API\_KEY）。

- AI调用封装：修改business/ai\_summarizer\.py，新增模型调用适配逻辑，根据配置的AI\_MODEL\_TYPE，调用对应模型的API；封装统一的AI调用接口，确保不同模型的返回结果格式统一（均适配Obsidian笔记模板）。

- 提示词适配：针对不同模型的特性，优化提示词模板（如GPT系列更适配简洁提示，文心一言更适配详细模板），在ai\_summarizer\.py中新增提示词模板字典，根据模型类型动态选择。

- 异常适配：新增不同模型API的异常处理逻辑，如OpenAI API的超时、额度不足异常，文心一言的请求频率限制异常，统一由exception\_handler\.py捕获处理。

关联模块：config/config\.py、business/ai\_summarizer\.py、business/exception\_handler\.py，修改\.env及\.env\.example文件。

注意事项：需分别申请各模型的API Key，注意不同模型的API调用格式、请求参数差异；可新增模型切换接口，支持通过TG消息动态切换模型（需权限校验）。

## 6\.3 多用户支持：权限分级管理

依赖技术：Python字典/JSON文件（存储用户信息），可选Redis（缓存用户权限）。

核心实现逻辑：

- 配置扩展：修改\.env文件，新增ALLOWED\_USERS配置（支持多个用户ID，用逗号分隔）；新增USER\_ROLES配置，区分管理员（admin）和普通用户（user），如“USER\_ROLES=123456:admin,789012:user”。

- 权限模块优化：修改tg\_access/permission\_checker\.py，新增用户角色校验逻辑，解析USER\_ROLES配置，存储用户ID与角色的映射关系；新增check\_role\(user\_id, role\)方法，用于校验用户是否具备指定角色权限。

- 功能权限划分：
        

    - 管理员权限：可发送任意格式文件、查看系统日志、切换AI模型、清理临时文件、添加/删除普通用户。

    - 普通用户权限：仅可发送支持格式的文件、文本/链接，查看自身入库的笔记记录。

- 用户管理接口：在tg\_access/bot\_handler\.py中新增管理员指令（如“/add\_user 789012”“/delete\_user 789012”“/view\_log”），触发对应的权限管理逻辑；新增用户身份反馈，用户发送消息后，机器人自动反馈当前用户角色及权限范围。

关联模块：tg\_access/permission\_checker\.py、tg\_access/bot\_handler\.py、config/config\.py，修改\.env及\.env\.example文件。

注意事项：用户ID需从TG获取（可通过@userinfobot获取）；管理员操作需增加二次确认逻辑，避免误操作；可新增用户配置文件（如user\_config\.json），持久化存储用户信息，避免重启后丢失。

## 6\.4 同步功能扩展：Obsidian笔记自动同步至Git仓库

依赖技术：GitPython（Git操作封装）、python\-dotenv（配置Git仓库信息）。

核心实现逻辑：

- 新增Git同步模块：在business模块下新增git\_sync\.py，封装Git仓库初始化、提交、推送逻辑。

- 配置扩展：修改config/config\.py，新增Git仓库配置项（GIT\_REPO\_URL、GIT\_USERNAME、GIT\_PASSWORD/GIT\_TOKEN），配置至\.env文件；新增同步频率配置（GIT\_SYNC\_INTERVAL，如30分钟）。

- 自动同步逻辑：在main\.py中新增定时任务（使用schedule库），按配置的同步频率，调用git\_sync\.py的sync\_notes\(\)方法，将Obsidian目录下的新增/修改笔记提交至Git仓库；也可在obsidian\_writer\.py的write\_note\(\)方法中新增钩子，笔记写入后立即触发同步。

- 同步异常处理：在git\_sync\.py中捕获Git操作异常（如仓库连接失败、认证失败、冲突），记录日志并通过TG机器人向管理员发送同步失败提示；支持手动触发同步（管理员指令“/sync\_notes”）。

关联模块：business/obsidian\_writer\.py、business/git\_sync\.py、config/config\.py、main\.py，修改\.env及\.env\.example文件。

注意事项：需确保服务器已安装Git，且配置Git用户信息；Git仓库需提前创建，且具备可读写权限；同步频率不宜过高，避免频繁提交占用资源。

## 6\.5 告警功能扩展：多渠道异常告警

依赖技术：钉钉机器人API、企业微信机器人API、smtplib（邮件发送）、requests库（已集成）。

核心实现逻辑：

- 新增告警模块：在business模块下新增alarm\_handler\.py，封装钉钉、企业微信、邮件三种告警方式的发送逻辑，提供统一的告警接口send\_alarm\(message, alarm\_type\)。

- 配置扩展：修改config/config\.py，新增告警配置项，如钉钉机器人WebHook（DINGTALK\_WEBHOOK）、企业微信机器人WebHook（WECHAT\_WEBHOOK）、邮件配置（SMTP\_SERVER、SMTP\_PORT、EMAIL\_USER、EMAIL\_PASSWORD、ALARM\_EMAIL），配置至\.env文件；新增告警级别配置（ALARM\_LEVEL，如ERROR、CRITICAL），仅触发指定级别的告警。

- 告警触发逻辑：修改business/exception\_handler\.py，在捕获ERROR、CRITICAL级异常时，调用alarm\_handler\.py的send\_alarm\(\)方法，发送告警消息（包含异常类型、触发模块、异常信息、发生时间）；可配置告警渠道（如仅钉钉、仅邮件，或多渠道同时发送）。

- 告警内容优化：告警消息格式统一，包含标题（如“TG AI笔记机器人异常告警”）、核心异常信息、排查建议（如“请检查AI API Key是否有效”）。

关联模块：business/exception\_handler\.py、business/alarm\_handler\.py、config/config\.py，修改\.env及\.env\.example文件。

注意事项：钉钉/企业微信机器人需提前创建，获取WebHook；邮件发送需开启SMTP服务（如QQ邮箱需开启授权码）；告警消息需控制频率，避免重复告警（如同一异常10分钟内仅发送一次）。

## 6\.6 大文件支持：突破TG Bot API 50MB限制

依赖技术：TG Local Bot API Server（本地部署）、python\-telegram\-bot库（适配本地API）、Docker（可选，简化本地API部署）。

核心实现逻辑：

- 本地API部署：在服务器上部署TG Local Bot API Server（可通过Docker部署，镜像为telegrammessenger/botapi），配置API服务器端口（如8081）、数据存储路径，关联TG机器人Token。

- 机器人适配：修改tg\_access/bot\_handler\.py，初始化机器人时，指定本地API服务器地址（如“http://localhost:8081”），替代TG官方API，实现大文件下载。

- 文件处理优化：修改business/file\_processor\.py，扩展文件大小限制（如MAX\_FILE\_SIZE=2\*1024\*1024\*1024，即2GB）；新增大文件分片下载逻辑（若文件超过100MB，采用分片下载，避免内存溢出）；修改utils/file\_utils\.py的check\_file\_size\(\)方法，适配新的大小限制。

- 资源优化：修改storage/temp\_manager\.py，新增大文件临时存储目录（如\./temp\_files/large），单独管理大文件；优化临时文件清理逻辑，优先清理大文件，避免服务器空间溢出。

关联模块：tg\_access/bot\_handler\.py、business/file\_processor\.py、utils/file\_utils\.py、storage/temp\_manager\.py。

注意事项：本地API服务器需占用一定的服务器资源（建议CPU≥2核、内存≥4GB）；需确保本地API服务器与TG官方服务器网络连通；大文件处理需优化性能，避免阻塞其他任务。

补充说明：所有可扩展功能均遵循“不破坏现有架构、不影响现有功能”的原则，新增模块与现有模块松耦合，可根据实际需求选择性开发；每个可扩展功能均提供完整的依赖说明、实现步骤和注意事项，开发人员可直接按照方案落地，无需额外设计。

# 7\. 总结

本文档基于架构设计文档，详细拆解了基于Python的TG AI笔记自动收集系统的功能实现，明确了项目结构、各模块功能点、接口定义、核心业务流程及功能约束，完全贴合「TG机器人\+第三方大模型\+Obsidian入库」的核心需求。

文档内容严格遵循模块化、松耦合的设计原则，Python项目结构清晰，各模块职责明确，可直接用于开发落地；同时预留了可扩展功能，便于后续根据需求升级优化。开发人员可按照本文档的功能设计，逐一实现各模块功能，确保系统稳定、易用、可维护。

> （注：文档部分内容可能由 AI 生成）
