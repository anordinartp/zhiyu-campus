# 知屿校园 · 校园信息智能平台

> 软件工程课程设计 —— 从需求分析、建模、数据库设计到实现与测试的完整闭环。

## 这是什么

一个面向校园的轻量社区平台：聊天室、博客、统一检索、AI 内容处理与人工审核。

**特点**：报告里的每一张图、每一张表，在代码里都能找到对应实现。

| 报告章节 | 代码位置 |
|---|---|
| 第 6 章 数据库设计（19 张表、30 条外键） | `schema.sql` |
| 第 7 章 体系结构与接口（23 个接口） | `software/campus/src/main/java` |
| 第 8 章 类图 / 状态图 / 三个算法 | `chat`、`blog`、`ai`、`search` 包 |
| 第 9 章 测试（32 条用例） | `software/run_tests.ps1` |

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Spring Boot 4.1.2 · Java 21（虚拟线程）· MyBatis-Plus 3.5.18 |
| 数据库 | MySQL 8.0（19 表 / 30 外键 / 1 CHECK） |
| 前端 | Vue 3.5 + Element Plus（免构建，随 jar 发布） |
| 接口文档 | Springdoc OpenAPI（`/doc.html`） |
| 测试 | 自研脚本，32 条用例覆盖功能与边界 |

## 目录结构

```
.
├── schema.sql                    建库脚本（含种子数据）
├── 知屿校园-...-第6轮修订.docx     实验报告（46 页，9 章）
├── 图1..图11 / 附图1..4           建模图件（vsdx / png / pdf）
├── _build/                        报告与图件的生成脚本（Python + Visio COM）
├── software/
│   ├── start-mysql.ps1            启动独立 MySQL 实例（3307）
│   ├── run_tests.ps1              测试执行脚本
│   └── campus/                    Spring Boot 工程
└── 开发流程.md / 上传到GitHub.md    协作与部署说明
```

## 快速开始

### 1. 准备数据库

```bash
mysql -u root -p < schema.sql
```

> 脚本里库名写死为 `zhiyu_campus`。若你的 MySQL 不在 3307 端口，
> 改 `software/campus/src/main/resources/application.yml` 的连接串即可。

### 2. 启动服务

```bash
cd software/campus
./mvnw package -DskipTests        # Windows: mvnw.cmd
java -jar target/campus-0.0.1-SNAPSHOT.jar
```

### 3. 打开

- 前端：http://127.0.0.1:8080
- 接口文档：http://127.0.0.1:8080/doc.html

### 4. 登录账号

| 账号 | 口令 | 角色 | 能做什么 |
|---|---|---|---|
| `admin` | `admin1234` | 管理员 | 全部功能 + 审核台 + 热度重算 |
| `20230001` | `abc12345` | 学生 | 普通社区功能 |
| `demo2023` | `demo1234` | 学生 | 演示用 |

## 功能一览

| 模块 | 接口 | 说明 |
|---|---|---|
| 认证 | `POST /auth/register` `/auth/login` `/auth/refresh` | JWT，访问令牌 2 小时，连续 5 次失败锁定 10 分钟 |
| 聊天室 | `/rooms*` `/rooms/{id}/messages` | 房间、成员、禁言、游标分页消息 |
| 博客 | `/posts*` | 发帖、回帖、点赞、收藏（均幂等） |
| 检索 | `GET /search` | `score = 0.5×相关度 + 0.3×热度 + 0.2×偏好` |
| AI | `GET /posts/{id}/ai-result` | 摘要、情感、自动打标、违规置信度 |
| 智能体 | `POST /agent/chat` `/agent/info` | 总 agent 路由到聊天室/帖子/搜索三个子 agent |
| 审核 | `/admin/review/*` | 待审列表、通过、删除、24 小时内撤销 |
| 行为 | `POST /behaviors` | 浏览/停留/点赞等埋点，供偏好计算 |

## AI 智能体（总 agent + 三个子 agent）

`POST /api/v1/agent/chat` 用一句话就能驱动整个系统：

```json
{ "message": "在考研自习室说：大家好" }
```

返回里包含 `agent`（谁处理的）、`action`（做了什么）、`reply`（自然语言回复）、
`trace`（路由过程：`router:rules->chat | model:local-rules`）。

| 子 agent | 能做的事 | 示例 |
|---|---|---|
| `chat` | 查房间、加入、发消息、看记录 | 「有哪些聊天室」「在考研自习室说：你好」 |
| `post` | 浏览、发帖、回帖 | 「看看最新帖子」「发帖 标题：xxx 内容：yyy」 |
| `search` | 关键词检索并解释排序 | 「帮我搜一下高数」 |

**路由方式**：配置了模型密钥就让模型判断意图，否则用关键词规则兜底。
两种方式下，真正的动作都由子 agent 调用已有业务服务完成，**模型不直接碰数据库**。

### 接入真实模型（OpenAI 兼容接口）

默认关闭。设置环境变量后重启即可，代码不用改：

```powershell
$env:AI_ENABLED = "true"
$env:AI_API_KEY = "sk-你的密钥"
$env:AI_BASE_URL = "https://api.deepseek.com/v1"   # 通义、Moonshot 等同理
$env:AI_MODEL    = "deepseek-chat"
java -jar target/campus-0.0.1-SNAPSHOT.jar
```

调用 `/api/v1/agent/info` 可以看到当前用的是模型还是本地规则：

```json
{ "llmAvailable": true, "model": "deepseek-chat", "subAgents": ["chat","post","search"] }
```

> 模型不可用（超时、401、限流）时会自动降级到规则路由，不会让接口报错。

## 测试

```bash
powershell -File software/run_tests.ps1
```

**最近一次结果：32 条用例，通过 29、部分通过 1、未通过 0、未覆盖 2（通过率 90.6%）。**

## 已知限制

| 项 | 说明 |
|---|---|
| 大模型 | 当前为本地规则实现（`AiModelClient`），替换该类即可接入真实模型 |
| 检索 | 基于数据库查询，未接入独立检索引擎，无降级路径 |
| 性能 | 未做压测，表 31 的 P95 / 并发指标待验证 |
| 单元测试 | 只有接口级测试，无 JUnit 覆盖率统计 |
| 二期功能 | 举报（UC-13）未实现，接口返回 404 |

## 分支约定

- `main` 始终保持可演示状态
- 每个改动开 `feature/xxx` 分支，测试通过后合并
- 演示前打标签：`git tag -a v1.0.0 -m "答辩版"`

详见 [开发流程.md](开发流程.md)。
