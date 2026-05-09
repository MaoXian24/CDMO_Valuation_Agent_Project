# CDMO Valuation Agent — 操作手册（唯一入口）

> 按编号顺序从 A1 做到 A5，最后合并。Coze 三层结构：**Agent → 插件（Plugin）→ 工具（Tool）**。
> README 是英文，Python 代码和 Prompt 保持英文。只有这份操作手册是中文。

---

# 第 0 部分：动手前必读

## 0.1 你要准备的东西

- Coze 账号，能创建 Agent / Tool / Workflow
- 一个共用 WRDS 账号密码
- CDMO 行业报告 PDF（后面上传知识库用）
- 在 VS Code 里打开以下文件（按编号，后面省得找）：
  - `00_manual.md` — 本手册
  - `01_prompt_templates.md` — 所有 Prompt 模板
  - `02_coze_tool_fields.md` — 工具字段名和类型的对照表
  - `04_A1_wrds_financial_stmt.py` — A1 代码
  - `05_A2_forecast.py` — A2 代码
  - `06_A3_wrds_beta.py` — A3 代码
  - `07_A4_get_dcf.py` — A4 代码
  - `08_A5_chart_generator.py` — A5 代码
  - `10_example_input.txt` — 测试输入

## 0.2 基础概念

| 概念 | 解释 |
|------|------|
| Agent（智能体） | 角色。负责对话、决策、调用工具 |
| Plugin / Tool（插件/工具） | 实际干活的。抓数据、算 beta、折现都是它 |
| Workflow（工作流） | 把 A1→A2→A3→A4→A5 串成一条线 |
| Python 代码 | 插件的底层实现。你只负责复制粘贴 |

## 0.3 测试工具时怎么输入参数

**独立测试工具**：在 Coze 里打开工具，点 Test，Coze 自动弹出一个表单。你在表单的文本框里填值，点运行。**不需要在聊天框打字。**

**Orchestrator 对话**：通过主 Agent 对话时，直接在聊天框说人话（比如 "analyze 603259"），LLM 自动帮你填参数。这是 W10 课堂的做法。

## 0.4 层级结构和命名规则

Coze 里是三层结构：**Agent → 插件（Plugin）→ 工具（Tool）**。每一层都有独立的名称和描述。

### 操作流程（这个顺序不能错）

```
创建 Agent → 进入 Agent 编辑页
  → 添加插件（云侧插件 / IDE / Python 3）→ 进入插件编辑页
    → 在插件里添加工具 → 进入工具编辑页
      → 配置工具的 Input/Output 字段 + 粘贴代码
```

### Agent 层

| 字段 | 限制 | 说明 |
|------|------|------|
| Name | ≤ 50 英文字符 | 格式 `A{数字}_{功能}`，全英文下划线 |
| Description | ≤ 500 英文字符 | 告诉 LLM 这个 Agent 负责什么 |

### ⚠️ Prompt 中插入工具引用（{} 机制，课堂 W9 做法）

Agent 的 Prompt 必须告诉 LLM 它有哪些工具可用。在 Coze 的 Prompt 编辑框中：

1. 在 Prompt 正文中**需要调用工具的位置**输入 `{}`（不是只在结尾——LLM 需要在上下文中知道什么情况下用哪个工具）
2. Coze 自动弹出可用工具列表
3. 选择对应的工具，Coze 插入工具引用标记

示例——
```
You are A1 Agent. When the user provides company info including stkcd and year range,
call {} to retrieve financial data from WRDS.
```
在 `{}` 处选择 `WRDS_Condensed_Financial_Stmt`，Coze 会替换为工具引用。

如果 Prompt 中需要调用多个工具（如 Orchestrator），就在每个需要调用的位置分别 `{}` 插入对应工具。

**每个 Agent 的 Prompt 都要做这一步。**

### 插件（Plugin）层

插件是工具的外层容器。先在 Agent 里创建插件，进入插件编辑页后才能添加工具。

| 字段 | 限制 | 说明 |
|------|------|------|
| Name | 和工具名一致 | 插件名就填和工具名一样的值 |
| Description | ≤ 50 英文字符 | 一句话，以 `ACC102 Group 12 CDMO Agent -` 开头 |

### 工具（Tool）层

工具是真正执行 Python 代码的东西。在插件编辑页里点击「添加工具」创建。

| 字段 | 限制 | 说明 |
|------|------|------|
| Name | 必须和 .py 文件第 2 行 import 路径一致 | 名字不对直接 ModuleNotFoundError |
| Description | ≤ 300 英文字符 | 描述工具的功能，帮助 LLM 理解何时调用 |

| 工具 | 必须填的名称（Plugin 也填同名） |
|------|---------------------------|
| A1 | `WRDS_Condensed_Financial_Stmt` |
| A2 | `Forecast_Condensed_Statements` |
| A3 | `WRDS_Beta` |
| A4 | `Get_DCF` |
| A5 | `Chart_Generator` |

## 0.5 字段配置规则

- Coze 支持 6 种字段类型：**string, integer, number, object, array, boolean**
- `object` 类型**不需要用**——所有嵌套数据字段都用 `string`（代码已 `json.dumps()` 序列化）
- `array` 类型会弹出「子项目类型 / Item Type」选择框——`years` 和 `forecast_years` 选 `number` 即可
- 没有 `list` 类型（Coze 里用 `array`）
- 没有 `markdown string` 类型（Coze 里用 `string`）
- 每个字段除了填名称和类型，**还要填描述（Description）**——从 `02_coze_tool_fields.md` 的 English Description 列复制

## 0.6 Python 运行时、插件类型和图标

### 运行时选择
Coze 创建工具时有两种运行时：**Python 3** 或 **Node.js**。全部选 **Python 3**。这和课堂一致。

### 插件类型
全部工具都是 **云端插件（Cloud Plugin）**——代码在 Coze 云端服务器运行，在 Coze IDE 里编写。Coze 有三种插件类型：

| 类型 | 说明 | 我们选 |
|------|------|--------|
| 云端插件（Cloud） | 代码在 Coze 服务器上运行，在 Coze IDE 中创建 | ✅ 全部 5 个工具 |
| 端插件（Local） | 代码在你的设备上运行 | ❌ |
| MCP 插件 | 通过 MCP 协议连接外部服务 | ❌ |

创建每个工具时：选择 **「云侧插件 / Cloud Plugin」→「在 Coze IDE 中创建」→ 运行时选「Python 3」**。

### 每个工具的图标（Icon）用一句话描述

Coze 创建**插件**时可以设置图标（不是工具层）。用下面的一行英文描述作为图标文字（不是 emoji，是文字描述）：

| 工具 | 图标文字（Icon Description） |
|------|---------------------------|
| `WRDS_Condensed_Financial_Stmt` | `Financial statement retrieval icon` |
| `Forecast_Condensed_Statements` | `Forecast and projection icon` |
| `WRDS_Beta` | `Stock beta calculation icon` |
| `Get_DCF` | `DCF valuation model icon` |
| `Chart_Generator` | `Financial chart generation icon` |

### 依赖总览（每个工具的具体依赖见该节的「添加依赖包」步骤）

> ⚠️ 依赖在**粘贴代码之后**添加——顺序是：建字段 → 贴代码 → 加依赖 → 测试。

| 工具 | 依赖 |
|------|------|
| A1/A2/A3 | `numpy` `2.2.5` / `pandas` `2.2.3` / `wrds` `3.3.0` / `tabulate` `0.9.0` |
| A4 | `numpy` `2.2.5` / `pandas` `2.2.3` / `tabulate` `0.9.0`（无 wrds） |
| A5 | `numpy` `2.2.5` / `pandas` `2.2.3`（matplotlib 按需） |

> 不要求版本号就只填包名。Python 运行时选 **3.10**。

### import 必须写在 handler 里面
Coze 要求所有第三方包的 import 写在 `def handler()` 函数内部：

| ✅ 正确 | ❌ 错误 |
|---------|--------|
| `def handler(args):` | `import pandas as pd` |
| `    import pandas as pd` | `def handler(args):` |

### 粘贴代码前：删光 Coze 自动生成的模板
新建 Python 工具后，Coze 会在代码编辑器里自动生成一段模板代码（占位符）。**把它全删了再粘贴我们的代码**。步骤：
1. 在代码编辑器里 `Ctrl+A` 全选 → `Delete` 删光
2. 打开对应的 `.py` 文件 → `Ctrl+A` 全选 → `Ctrl+C`
3. 回到 Coze 编辑器 `Ctrl+V` → Save

我们的代码是完整独立的，从 `from runtime import Args` 到最后一行 `return`，不依赖任何自动生成的模板。

### A5 的 matplotlib
如果 A5 报 matplotlib 导入错，在依赖区搜索 `matplotlib` 添加。

---

> **课堂参考**：W10 Walkthrough 1 `WRDS_Condensed_Financial_Stmt`。课堂输出 BS+IS。
> **我们多了**：`years`、`bs_check`、`sales_growth`（历史增长率）、`other_ratios`（历史比率表）。

# 第 1 部分：A1 — 财务报表抓取

> 打开文件：`04_A1_wrds_financial_stmt.py`

## 1.1 创建 Agent

1. 登录 Coze → 项目空间 →「创建智能体 / Create Agent」。
2. Name：`A1_Financial_Data_Agent`。先不填其他，等插件和工具建完。
3. Create → 进入 Agent 编辑页。

## 1.2 在 Agent 里添加插件（Plugin）

1. Agent 编辑页 → 找到「插件 / Plugins」区 →「添加插件 / Add Plugin」。
2. 选择「云侧插件 / Cloud Plugin」→「在 Coze IDE 中创建」→ 运行时「Python 3」。
3. 插件编辑页打开后，填：

| 字段 | 值 |
|------|-----|
| Name | `WRDS_Condensed_Financial_Stmt` |
| Description | `ACC102 Group 12 CDMO Agent - WRDS financial stmt` |
| 图标 | `Financial statement retrieval icon` |

> ⚠️ 插件 Description 限制 50 英文字符，这里刚好 50 字符（含空格）。图标在创建插件时设置（不是工具）。

4. 点击创建，进入插件编辑页。

## 1.3 在插件里添加工具（Tool）

1. 插件编辑页 →「添加工具 / Add Tool」→「Python 工具」。
2. 工具编辑页打开后，填：

| 字段 | 值 |
|------|-----|
| Name | `WRDS_Condensed_Financial_Stmt` |
| Description | `Retrieve and standardize annual financial statements from WRDS CSMAR database for Chinese A-share companies. Returns condensed balance sheet, income statement, historical year-over-year revenue growth rates, and key financial ratios in Markdown format.` |

> 工具 Name 必须和代码第 2 行 import 路径一致。Description 限制 300 英文字符。工具没有图标——图标在插件层设置。

依赖区先不管。配置 Input / Output 字段：

### Input 字段（按顺序添加）

| Field Name | Type | Description (English) |
|-----------|------|-----------------------|
| `WRDS_username` | string | WRDS account username for database connection |
| `WRDS_pwd` | string | WRDS account password |
| `stkcd` | string | 6-digit CSMAR stock code, e.g. 603259 (no .SH suffix) |
| `start_year` | number | First year of historical data, e.g. 2019 |
| `end_year` | number | Last year of historical data, e.g. 2024 |
| `company_dict` | string | (Optional) JSON string for multi-company mode, e.g. "{'600519': 'Moutai'}". Leave empty for single-company use. |

### Output 字段

| Field Name | Type | Description (English) |
|-----------|------|-----------------------|
| `message` | string | Status message indicating success or failure |
| `years` | array | List of integer years retrieved（子项目类型选 `number`） |
| `balance_sheet` | string | Condensed balance sheet in Markdown table format |
| `income_statement` | string | Condensed income statement in Markdown table format |
| `bs_check` | string | JSON string of balance sheet identity check values, keyed by year |
| `sales_growth` | string | JSON string of historical year-over-year revenue growth rates, keyed by year |
| `other_ratios` | string | JSON string of historical financial ratios by year, nested dict |

保存字段 → 打开 `04_A1_wrds_financial_stmt.py` → 删光编辑器模板 → 粘贴 → Save 工具。

### 添加依赖包（粘贴代码后立刻做）

工具保存后，在编辑页找到「依赖 / Dependencies」区域，逐个搜索并添加：

| 包名 | 版本 |
|------|------|
| `numpy` | `2.2.5` |
| `pandas` | `2.2.3` |
| `wrds` | `3.3.0` |
| `tabulate` | `0.9.0` |

> 搜索不到就手动输入包名回车。不要求填版本号就只填包名。

## 1.4 先测试工具（通过后才回 Agent）

> ⚠️ **必须先测试**。工具跑通后再回 Agent 填 Prompt，否则出问题不知道是代码错还是 Agent 配置错。

点击工具页的「测试 / Test」。在弹出的 JSON 编辑器中**全选删除**，粘贴以下 JSON：

```json
{
  "WRDS_username": "maoxian24",
  "WRDS_pwd": "WRDS_maoxian102",
  "stkcd": "603259",
  "start_year": 2019,
  "end_year": 2024
}
```

点击 Run。期望返回：
| WRDS_username | `maoxian24` |
| WRDS_pwd | `WRDS_maoxian102` |
| stkcd | `603259` |
| start_year | `2019` |
| end_year | `2024` |

期望返回：
1. `balance_sheet` — 表格，含 `Cash and equivalent` / `Total assets` / `check` 等行
2. `income_statement` — 表格，含 `Total Revenue` / `Net profit` 等行
3. `bs_check` — 值接近 0.0
4. `years` — `[2019,2020,2021,2022,2023,2024]`
5. `sales_growth` — 字典，键为年份值为小数
6. `other_ratios` — 嵌套字典，含 `Cost of goods sold/Sales` 等

> 以上表格里的值可以直接复制粘贴到 Coze 表单。表单中 number 类型字段直接填数字（不加引号），string 类型字段按表格填。

失败排查：

| 现象 | 解决 |
|------|------|
| 空返回或连接失败 | 检查 WRDS 账号密码、Coze 沙箱是否允许外网 |
| stkcd not found | 写 `603259`，不要带 `.SH` |
| 表格全 0 | 改年份范围试 `2020-2024` |
| ModuleNotFoundError: pandas | import 没写在 handler 里面——确认你粘贴的代码开头是 `def handler` 而不是 `import pandas` |

## 1.5 测试通过后回到 Agent 填 Prompt

关闭工具/插件编辑页，回到 Agent 编辑页。

1. **粘贴 Prompt**：打开 `01_prompt_templates.md` → 找 `## A1: Data Intake and Cleaning Agent Prompt` → 复制 `"""..."""` 之间的英文 Prompt → 粘贴到 Agent 的 Prompt 编辑框。

2. **插入工具引用（{} 机制）**：粘贴 Prompt 后，找到 **Skill 1（Trigger Data Input Form）** 中的这一行：
   ```
   After your greeting, immediately call the WRDS_Condensed_Financial_Stmt plugin at {} to open the data input form.
   ```
   把光标放在 `{}` 位置上，Coze 会自动弹出一个「选择工具 / Select Tool」下拉列表 → 点击选择 **`WRDS_Condensed_Financial_Stmt`**。Coze 会用工具引用标记替换 `{}`。

   > 💡 这就是让 Coze 自动弹出交互式表单的关键——Agent 主动调 `{}`，Coze 检测到工具需要输入 → 自动弹表单。

   > ⚠️ 其他 Agent（A2–A4 和 Orchestrator）的 Prompt 也一样：在 Prompt 正文中需要调用工具的位置放 `{}`，然后选择对应工具。不是只在 Prompt 末尾加。

3. **保存 Agent**。Agent 的 Prompt + 工具引用配好之后，回到对话界面测试。

4. **设置开场白（Opening Greeting）**：在 Agent 编辑页找到「开场白 / Opening Greeting」字段，粘贴以下英文开场白：

   > Hello! I am A1 Agent, responsible for financial statement data retrieval. To begin, please provide the following information in JSON format:
   > - WRDS_username: your WRDS account username
   > - WRDS_pwd: your WRDS account password
   > - stkcd: 6-digit CSMAR stock code (e.g. "603259" for WuXi AppTec)
   > - start_year: first year of historical data (e.g. 2019)
   > - end_year: last year of historical data (e.g. 2024)

   This greeting auto-populates when the user opens the Agent — no need to type it manually.

---

## 变更日志（小节快速记录）

## A2 Bug 修复总结（2026-05-10）

A2 (`05_A2_forecast.py`) 经三轮调试最终通过，共修复 3 个 bug：

### Bug 1: `assumption_df.at[row, list]` → `unhashable type: 'list'`
- **行**：FCFF 段 8 处 `assumption_df.at['X/Sales', yrs_assumption].mean()`
- **原因**：pandas `.at` 仅支持标量标签，传入 `list`（如 `[2020,2021,2022,2023,2024]`）触发内部 hash 失败
- **修复**：全部改为 `.loc`

### Bug 2: `is_df.at[row, '2024']` → KeyError
- **行**：`mp_val = ... is_df.at[..., yh[-1]]`
- **原因**：`is_df` 列是 int（`2024`），`yh[-1]` 是 string（`'2024'`，来自 `.astype(str)`），类型不匹配
- **修复**：改用 `latest`（= `end_year`，int）

### Bug 3: `set(list(rev_hist.index)).union(forecast_years)` → numpy.int64/Python int 混合
- **行**：`all_years = sorted(set(list(rev_hist.index)).union(forecast_years))`
- **原因**：WRDS 返回的年份是 numpy.int64，`forecast_years` 是 Python int，`set()` 混合类型在 Coze 沙箱不稳定
- **修复**：`set(int(y) for y in rev_hist.index).union(int(y) for y in forecast_years)`

### 调试方法
- 将大 try 块拆为 6 个小块（`[step: bs_is]`, `[step: sales_forecast]`, `[step: assumption_table]`, `[step: scalars]`, `[step: fcff]`, `[step: fwd_bs_is]`），每个独立 catch 并返回步骤标签，快速定位错误行。

### 最终状态
- ✅ A1 通过（`yr = range(...)` 可行）
- ✅ A2 通过（`yr = list(range(...))` + `yr_int = [int(y) for y in yr]` 保底）
- ⏳ A3/A4/A5 待测试
- 2026-05-10 02:54: Fixed `is_get()`/`bs_get()` in `04_A1_wrds_financial_stmt.py` and `05_A2_forecast.py` — added `.reindex(yr, fill_value=0)` to handle missing years in WRDS data. Previously if user requested e.g. 2017-2024 but WRDS only had 2019-2024, downstream `[yr]` indexing would throw `KeyError: '[2017] not in index'`. Fallback branch also fixed to return a zero-filled Series indexed by all of `yr` instead of only `df_is.columns`. All 4 Python files pass syntax check. Zero new dependencies.
- 2026-05-10 02:14: Added semi-automated DCF assumption generation feature. Rewrote A4 Prompt (`01_prompt_templates.md`) — Skill 1 now auto-analyzes A1/A2/A3 data + CDMO knowledge base to generate smart default DCF assumptions in interactive JSON form; Skill 2 unchanged. Rewrote Orchestrator Step 4 with full semi-automated flow: auto-analyze → present editable form → user confirm/edit/paste JSON → priority rule (JSON override > field edit > LLM default) → run DCF. Updated manual: new §4.0 section explaining feature, §4.1 Description updated, §4.5 expanded with user operation guide, §6.1 Orchestrator Description updated. Zero Python code changes — works purely through LLM reasoning + existing Get_DCF plugin interface.
- 2026-05-10 01:51: Moved icon descriptions from Tool to Plugin sections for A1/A2/A3/A4/A5 — icons are set at Plugin level in Coze, not Tool level. Added missing A4 plugin icon (`DCF valuation model icon`). Fixed §0.6 icon guidance text. All 5 plugin sections now consistently show Name + Description + 图标.
- 2026-05-10 01:42: Global field rename: `username`→`WRDS_username`, `password`→`WRDS_pwd` across ALL files. Reordered so WRDS_username/WRDS_pwd always first in every input table. Removed legacy getattr fallbacks in A1/A2/A3 Python code. Updated: 04/05/06 .py files, 02_coze_tool_fields.md (A1/A2/A3), 00_manual.md (§§1.3/1.4/2.3/2.4/3.3/3.4), 01_prompt_templates.md (A1 Skill 1 + JSON example, A3 Skill 1), 10_example_input.txt. Syntax checks all pass.
- 2026-05-10 01:27: Full audit + fixes: (1) `02_coze_tool_fields.md` — fixed A4 `sensitivity` type from `object` to `string` (code returns `json.dumps()`), changed A1/A2/A3 `start_year`/`end_year` from `string` to `number` to match manual; (2) `01_prompt_templates.md` — aligned A1 Skill 1 `start_year`/`end_year` type annotation from string to number; (3) `00_manual.md` §1.3 — added `company_dict` optional field to A1 Input table; (4) `00_manual.md` A3 — added missing §3.3 heading to fix numbering gap (was §3.2→§3.4).
- 2026-05-10 01:08: Rewrote A2/A3/A4/Orchestrator prompts in `01_prompt_templates.md` to unified Role/Skills/Limitations format with inline `{}` plugin references. Updated manual §§2.5/3.5/4.5/6.1 with step-by-step `{}` insertion guides (find exact Skill line → click `{}` → select plugin). Added missing §3.5 for A3. Updated Orchestrator §6.1 with per-Step `{}` mapping table.
- 2026-05-10 01:06: Cleaned up orphaned fragment lines (leftover "填 Description" / "1.6 测试 Agent" duplicates) after changelog section in `00_manual.md`.
- 2026-05-10 01:01: Updated A1 prompt in `01_prompt_templates.md` to Role/Skills/Limitations format with JSON input collection and inline `{}` plugin reference in Skill 2. Updated manual §1.5 with step-by-step `{}` insertion instructions (find `{}` in Skill 2 → click → select plugin).
- 2026-05-10 00:51: Reverted A1 prompt in `01_prompt_templates.md` to original concise greeting/input-collection version at user's request (user wanted the Role/Skills example only as a reference).  


> **课堂参考**：W10 Walkthrough 2 `Forecast_Condensed_Statements`。课堂输出 sales_forecast、assumption_table、bs_forecast、is_forecast、fcff、FCFF_Stage_1、Rd、D、TaxRate、Cash_Latest、Minority_Latest。
> **我们多了**：`message`、`forecast_years`。**课堂有的我们全有**（含刚补齐的 forward projected BS/IS）。

# 第 2 部分：A2 — 预测和假设表

> 打开文件：`05_A2_forecast.py`

## 2.1 创建 Agent

「创建智能体」→ Name：`A2_Forecast_Agent` → Create。

## 2.2 添加插件

Agent 编辑页 →「插件」→「添加插件」→ 云侧 / IDE / Python 3。

| 字段 | 值 |
|------|-----|
| Name | `Forecast_Condensed_Statements` |
| Description | `ACC102 Group 12 CDMO Agent - Forecast stmts` |
| 图标 | `Forecast and projection icon` |

## 2.3 添加工具

插件编辑页 →「添加工具」→ Python 工具。

| 字段 | 值 |
|------|-----|
| Name | `Forecast_Condensed_Statements` |
| Description | `Build multi-year financial forecasts using user-provided revenue growth assumptions and historical ratios from WRDS. Generates sales forecasts, assumption tables, FCFF projections, and key valuation inputs for downstream DCF.` |

依赖区留空。

### Input 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `WRDS_username` | string | WRDS account username |
| `WRDS_pwd` | string | WRDS account password |
| `stkcd` | string | 6-digit CSMAR stock code |
| `start_year` | number | First historical year, e.g. 2019 |
| `end_year` | number | Last historical year, e.g. 2024 |
| `sales_growth` | string | JSON string dict, e.g. {"2025":0.10,"2026":0.09} |
| `dividends_payout_ratio` | string | JSON string dict, e.g. {"default":0.3} |
| `depreciation_rate` | string | JSON string dict, e.g. {"default":0.05} |
| `other_ratios` | string | JSON string dict, use {} for defaults |

### Output 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `message` | string | Status message |
| `sales_forecast` | string | Sales forecast table in Markdown |
| `assumption_table` | string | Assumption table in Markdown |
| `forecast_years` | array | List of forecast years（子项目类型选 `number`） |
| `bs_forecast` | string | Forward projected balance sheet in Markdown |
| `is_forecast` | string | Forward projected income statement in Markdown |
| `fcff_table` | string | FCFF breakdown table in Markdown |
| `FCFF_Stage_1` | string | JSON-encoded list of FCFF values for A4 |
| `Rd` | number | Cost of debt |
| `D` | number | Total debt |
| `TaxRate` | number | Effective tax rate |
| `Cash_Latest` | number | Most recent cash balance |
| `Minority_Latest` | number | Most recent minority interest |

保存字段 → 打开 `05_A2_forecast.py` → 删光模板 → 粘贴 → Save 工具。

### 添加依赖包

工具保存后，在依赖区添加：`numpy`(2.2.5)、`pandas`(2.2.3)、`wrds`(3.3.0)、`tabulate`(0.9.0)。

## 2.4 先测试工具（通过后才回 Agent）

> ⚠️ 必须先测试。工具跑通后再回 Agent 填 Prompt。

打开工具 → Test → 弹出 JSON 编辑器 → 全选删除 → 粘贴：

```json
{
  "WRDS_username": "maoxian24",
  "WRDS_pwd": "WRDS_maoxian102",
  "stkcd": "603259",
  "start_year": 2019,
  "end_year": 2024,
  "sales_growth": "{\"2025\":0.10,\"2026\":0.10,\"2027\":0.10}",
  "dividends_payout_ratio": "{\"default\":0.3}",
  "depreciation_rate": "{\"default\":0.05}",
  "other_ratios": "{}"
}
```

点击 Run。期望返回：
| WRDS_username | `maoxian24` |
| WRDS_pwd | `WRDS_maoxian102` |
| stkcd | `603259` |
| start_year | `2019` |
| end_year | `2024` |
| sales_growth | `{"2025":0.10,"2026":0.10,"2027":0.10}` |
| dividends_payout_ratio | `{"default":0.3}` |
| depreciation_rate | `{"default":0.05}` |
| other_ratios | `{}` |

> `other_ratios` 填 `{}` 表示不手动覆盖任何比率，全部使用历史平均值。`sales_growth` 等 JSON 字段复制时注意用英文双引号。

期望返回：`sales_forecast` / `assumption_table` / `fcff_table` / `FCFF_Stage_1` / `Rd` / `D` / `TaxRate` / `Cash_Latest` / `Minority_Latest` 共 11 项。

失败排查：

| 现象 | 解决 |
|------|------|
| must be a valid JSON object | 检查 sales_growth 等用英文双引号 `"`，不是中文 `""` |
| forecast_years 不对 | 取决于 end_year，end_year=2024 则预测年为 2025/2026/2027 |

## 2.5 测试通过后回到 Agent 填 Prompt

回到 Agent 编辑页 → Prompt 框粘贴 A2 Prompt（`01_prompt_templates.md` 中 `## A2: Financial Analysis Agent Prompt`）。

1. **粘贴 Prompt**：复制 `"""..."""` 之间的英文 Prompt → 粘贴到 Prompt 编辑框。
2. **插入工具引用**：找到 **Skill 1（Trigger Forecast Input Form）** 中的这一行：
   ```
   After your greeting, immediately call the Forecast_Condensed_Statements plugin at {} to open the forecast input form.
   ```
   光标放在 `{}` 上 → Coze 弹出下拉 → 选择 **`Forecast_Condensed_Statements`**。
3. Save Agent。

4. **设置开场白（Opening Greeting）**：在 Agent 编辑页找到「开场白 / Opening Greeting」字段，粘贴以下英文开场白：

   > Hello! I am A2 Agent, responsible for financial forecasting and ratio analysis. I will compute historical financial ratios, build multi-year forecasts, and project FCFF using the data retrieved by A1. Please provide your forecast assumptions when prompted (sales growth, payout ratio, depreciation rate).

---

> **课堂参考**：W10 Walkthrough 3 `WRDS_Beta`。课堂输出 beta、price。
> **我们多了**：`message`、`sample_size`。

# 第 3 部分：A3 — Beta 计算

> 打开文件：`06_A3_wrds_beta.py`

## 3.1 创建 Agent

| 字段 | 值 |
|------|-----|
| Name | `A3_Beta_Agent` |
| Description | `Estimates historical stock beta against the CSI 300 market index using monthly return data from WRDS. Returns beta coefficient, latest closing price, and sample size. Call this agent to obtain the cost of equity input required for DCF valuation.` |

Prompt：`01_prompt_templates.md` 中 `## A3: Beta Estimation Agent Prompt` → 复制 → 粘贴 → Save。

## 3.2 添加插件

> 云侧插件（Cloud Plugin），Coze IDE，Python 3。

| 字段 | 值 |
|------|-----|
| Name | `WRDS_Beta` |
| Description | `ACC102 Group 12 CDMO Agent - Calculate historical beta from WRDS stock and index prices` |
| 图标 | `Stock beta calculation icon` |

## 3.3 在插件里添加工具（Tool）

1. 插件编辑页 →「添加工具 / Add Tool」→「Python 工具」。
2. 工具编辑页打开后，填：

| 字段 | 值 |
|------|-----|
| Name | `WRDS_Beta` |
| Description | `Estimate historical stock beta against CSI 300 market index using monthly return data from WRDS. Returns beta coefficient, latest closing price, and sample size for cost of equity calculation.` |

依赖区先不管。配置 Input / Output 字段：

### Input 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `WRDS_username` | string | WRDS account username |
| `WRDS_pwd` | string | WRDS account password |
| `stkcd` | string | 6-digit CSMAR stock code |
| `start_year` | number | First year for beta estimation, e.g. 2019 |
| `end_year` | number | Last year for beta estimation, e.g. 2024 |

### Output 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `message` | string | Status message |
| `beta` | number | Historical beta vs CSI 300 |
| `price` | number | Latest closing price |
| `sample_size` | integer | Number of valid monthly return observations |

保存字段 → 打开 `06_A3_wrds_beta.py` → 删光模板 → 粘贴 → Save 工具。

### 添加依赖包

工具保存后，在依赖区添加：`numpy`(2.2.5)、`pandas`(2.2.3)、`wrds`(3.3.0)、`tabulate`(0.9.0)。

## 3.4 先测试工具（通过后才回 Agent）

> ⚠️ 必须先测试。

打开工具 → Test → 弹出 JSON 编辑器 → 全选删除 → 粘贴：

```json
{
  "WRDS_username": "maoxian24",
  "WRDS_pwd": "WRDS_maoxian102",
  "stkcd": "603259",
  "start_year": 2019,
  "end_year": 2024
}
```

点击 Run。期望返回：
| WRDS_username | `maoxian24` |
| WRDS_pwd | `WRDS_maoxian102` |
| stkcd | `603259` |
| start_year | `2019` |
| end_year | `2024` |

期望返回 beta（0.3~2.0）、price（正数）、sample_size（≥20）。

---

## 3.5 测试通过后回到 Agent 填 Prompt

回到 Agent 编辑页 → Prompt 框粘贴 A3 Prompt（`01_prompt_templates.md` 中 `## A3: Beta Estimation Agent Prompt`）。

1. **粘贴 Prompt**：复制 `"""..."""` 之间的英文 Prompt → 粘贴到 Prompt 编辑框。
2. **插入工具引用**：找到 **Skill 1（Trigger Beta Input Form）** 中的这一行：
   ```
   After your greeting, immediately call the WRDS_Beta plugin at {} to open the beta estimation input form.
   ```
   光标放在 `{}` 上 → Coze 弹出下拉 → 选择 **`WRDS_Beta`**。
3. Save Agent。

4. **设置开场白（Opening Greeting）**：在 Agent 编辑页找到「开场白 / Opening Greeting」字段，粘贴以下英文开场白：

   > Hello! I am A3 Agent, responsible for estimating the stock's historical beta and preparing cost of equity inputs. I will retrieve monthly return data from WRDS and calculate beta against the CSI 300 market index. Please provide the stock code and estimation window when prompted.

---

> **课堂参考**：W10 Walkthrough 4 `Get_DCF`。课堂输出 dcf、vps。
> **我们多了**：`wacc`、`sensitivity`。DCF 终值公式完全对齐课堂。

# 第 4 部分：A4 — DCF 估值（含半自动假设生成）

> 打开文件：`07_A4_get_dcf.py`

## 4.0 半自动化 DCF 假设生成（新功能）

A4 Agent 集成了**半自动化假设生成**能力：

1. **收到 A1/A2/A3 数据后**，Agent 自动分析：
   - 历史营收增速 → 建议 future growth rates
   - 盈利和效率比率 → 验证假设合理性
   - Beta + 市场数据 → 建议 Rf / E_Rm
   - 知识库 CDMO 行业基准 → 行业合理区间

2. **展示交互式表单**：Agent 生成一组带默认值的 JSON 表单，由三部分组成：
   - 📊 自动填入（来自 A2/A3，数据驱动）：`beta`、`current_price`、`FCFF_Stage_1`、`Rd`、`D`、`TaxRate`、`Cash_Latest`、`Minority_Latest`、`end_year`
   - 🤖 LLM 建议（可编辑）：`shares_outstanding`、`n_years_2nd_stage`、`growth_rate_2nd_stage`、`long_term_growth`、`Rf`、`E_Rm`

3. **用户三种操作**：
   - ✅ 点确认 → 直接用 LLM 生成的值
   - ✏️ 编辑表单字段 → 用户改的覆盖 LLM 建议
   - 📝 在下方 JSON 输入框粘贴覆盖 → 100% 用户数据

4. **优先级**：JSON 输入框 > 表单字段编辑 > LLM 自动生成。

> 这个功能不需要额外 Python 代码——A4 的 `Get_DCF` 工具接收的字段完全不变，区别仅在于**数值来源**是 LLM 分析还是用户手填。

## 4.1 创建 Agent

| 字段 | 值 |
|------|-----|
| Name | `A4_DCF_Agent` |
| Description | `Semi-automated DCF valuation agent for CDMO equities. Auto-analyzes historical data and knowledge base to suggest DCF assumptions in an editable interactive form. Runs multi-stage DCF only after user confirmation. Calculates WACC, enterprise value, equity value, and intrinsic value per share.` |

Prompt：`01_prompt_templates.md` 中 `## A4: DCF Valuation Agent Prompt` → 复制 → 粘贴 → Save。

## 4.2 添加插件

> 云侧插件（Cloud Plugin），Coze IDE，Python 3。

| 字段 | 值 |
|------|-----|
| Name | `Get_DCF` |
| Description | `ACC102 Group 12 CDMO Agent - Multi-stage FCFF DCF with WACC and value per share` |
| 图标 | `DCF valuation model icon` |

依赖区搜索并添加 `numpy`、`pandas`、`tabulate`（版本见 0.6 节表。A4 不需要 wrds）。

### Input 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `shares_outstanding` | number | Total shares outstanding |
| `current_price` | number | Current stock price for market cap |
| `n_years_2nd_stage` | number | Number of years in Stage 2 |
| `growth_rate_2nd_stage` | number | Growth rate during Stage 2, e.g. 0.04 |
| `long_term_growth` | number | Perpetual growth rate, e.g. 0.02 |
| `Rf` | number | Risk-free rate, e.g. 0.03 |
| `beta` | number | Stock beta from A3 |
| `E_Rm` | number | Expected market return, default 0.065 |
| `Rd` | number | Cost of debt |
| `D` | number | Total debt amount |
| `TaxRate` | number | Effective tax rate, e.g. 0.25 |
| `FCFF_Stage_1` | string | JSON string list, e.g. "[100,108,116,124]" |
| `end_year` | number | Last historical year |
| `Cash_Latest` | number | Most recent cash balance |
| `Minority_Latest` | number | Most recent minority interest |

### Output 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `dcf` | string | DCF valuation table in Markdown |
| `vps` | number | Intrinsic value per share |
| `wacc` | number | Weighted Average Cost of Capital |
| `sensitivity` | string | JSON string of sensitivity parameters: WACC, Re, terminal_growth |

保存字段 → 打开 `07_A4_get_dcf.py` → 删光模板 → 粘贴 → Save 工具。

### 添加依赖包

工具保存后，在依赖区添加：`numpy`(2.2.5)、`pandas`(2.2.3)、`tabulate`(0.9.0)。A4 不需要 wrds。

## 4.4 先测试工具（通过后才回 Agent）

> ⚠️ 必须先测试。

打开工具 → Test → 弹出 JSON 编辑器 → 全选删除 → 粘贴：

```json
{
  "shares_outstanding": 100,
  "current_price": 50,
  "n_years_2nd_stage": 3,
  "growth_rate_2nd_stage": 0.08,
  "long_term_growth": 0.03,
  "Rf": 0.03,
  "beta": 1.2,
  "E_Rm": 0.08,
  "Rd": 0.04,
  "D": 500,
  "TaxRate": 0.25,
  "FCFF_Stage_1": "[100,108,116,124]",
  "end_year": 2024,
  "Cash_Latest": 200,
  "Minority_Latest": 50
}
```

点击 Run。期望返回 dcf 表格、vps（正数）、wacc（约 0.07~0.09）。
| current_price | `50` |
| n_years_2nd_stage | `3` |
| growth_rate_2nd_stage | `0.08` |
| long_term_growth | `0.03` |
| Rf | `0.03` |
| beta | `1.2` |
| E_Rm | `0.08` |
| Rd | `0.04` |
| D | `500` |
| TaxRate | `0.25` |
| FCFF_Stage_1 | `"[100,108,116,124]"` |
| end_year | `2024` |
| Cash_Latest | `200` |
| Minority_Latest | `50` |

期望返回 dcf 表格、vps（正数）、wacc（约 0.07~0.09）。

失败排查：

| 现象 | 解决 |
|------|------|
| vps 负数 | D 太大或 long_term_growth >= WACC |
| must be a valid JSON list | FCFF_Stage_1 用英文双引号 |

## 4.5 测试通过后回到 Agent 填 Prompt

回到 Agent 编辑页 → Prompt 框粘贴 A4 Prompt（`01_prompt_templates.md` 中 `## A4: DCF Valuation Agent Prompt`）。

1. **粘贴 Prompt**：复制 `"""..."""` 之间的英文 Prompt → 粘贴到 Prompt 编辑框。
2. **插入工具引用**：A4 的 Prompt 中有 **两处 `{}`**：
   - **Skill 1**：找到 `immediately call the Get_DCF plugin at {} to open the DCF valuation input form` → 光标放 `{}` → 选择 **`Get_DCF`**
   - **Skill 2**：找到 `call the Get_DCF plugin at {} to perform multi-stage DCF valuation` → 光标放 `{}` → 选择 **`Get_DCF`**
   两个 `{}` 都选同一个工具 `Get_DCF`。第一个触发输入表单，第二个执行估值计算。
3. Save Agent。

4. **设置开场白（Opening Greeting）**：在 Agent 编辑页找到「开场白 / Opening Greeting」字段，粘贴以下英文开场白：

   > Hello! I am A4 Agent, responsible for DCF valuation. I will automatically analyze the historical data, beta estimate, and CDMO industry benchmarks to suggest a complete set of DCF assumptions. You can confirm my suggestions, edit individual values, or paste your own JSON to override. Valuation runs only after your explicit confirmation.

### 半自动 DCF 使用说明（用户操作流程）

当主流程跑到 A4 时，Agent 会：

1. **自动分析**并展示一组带默认值的 DCF 假设（JSON 格式）。
2. **展示交互式表单** — 用户可以：
   - ✅ 点确认 → 直接用 LLM 生成的默认值 → Agent 调 `Get_DCF` 算估值
   - ✏️ 直接在表单里编辑个别字段 → Agent 用合并值 → 调 `Get_DCF`
   - 📝 在下方 JSON 输入框粘贴覆盖 JSON → Agent 用用户值 → 调 `Get_DCF`
3. **优先级**：JSON 输入框有内容 > 表单字段编辑 > LLM 自动生成值。

> 这和 A1 填基础信息的方式一致——都有 JSON 输入框、都直接编辑表单。区别是 A4 会**先帮你填好**推荐值，你只需要确认或修改。不需要自己在对话框里手动输入然后删除重发。

---

> **课堂没有这个插件**——课堂要求在最终报告中包含图表，但没提供单独的图表工具代码。我们自己写了支持 5 种图表类型的通用插件。

# 第 5 部分：A5 — 图表生成

> 打开文件：`08_A5_chart_generator.py`

## 5.1 创建插件和工具

> A5 不需要单独 Agent。直接在项目主页创建插件，然后在插件里添加工具。

1. 项目主页 →「插件 / Plugins」→「创建插件」→ 云侧 / IDE / Python 3。

| 字段 | 值 |
|------|-----|
| Name | `Chart_Generator` |
| Description | `ACC102 Group 12 CDMO Agent - Chart Generator` |
| 图标 | `Financial chart generation icon` |

2. 进入插件编辑页 →「添加工具」→ Python 工具。

| 字段 | 值 |
|------|-----|
| Name | `Chart_Generator` |
| Description | `Generate publication-quality financial charts from valuation data. Supports line charts for trends, bar charts for peer comparison, pie charts for structure breakdowns, stacked bar charts for composition changes, and waterfall charts for bridge analysis.` |

依赖区搜索并添加 `numpy`、`pandas`。如果运行时报 matplotlib 错，再加 `matplotlib`。

### Input 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `chart_type` | string | Chart type: line / bar / pie / stacked_bar / waterfall |
| `chart_data` | string | JSON string with chart data |
| `title` | string | Chart title |
| `x_label` | string | X-axis label (empty for pie) |
| `y_label` | string | Y-axis label (empty for pie) |

### Output 字段

| Field Name | Type | Description |
|-----------|------|-------------|
| `message` | string | Status message |
| `chart_image` | string | Base64-encoded PNG image |

保存字段 → 打开 `08_A5_chart_generator.py` → 删光模板 → 粘贴 → Save 工具。

### 添加依赖包

工具保存后，在依赖区添加：`numpy`(2.2.5)、`pandas`(2.2.3)。报 matplotlib 错时再加 `matplotlib`(3.9.0)。

## 5.2 先测试工具

> A5 不需要 Agent，工具 Save 后直接点 Test。

**Test 1 — Line Chart (Revenue Trend)：**

| Field | Value |
|-------|-------|
| chart_type | `line` |
| chart_data | `{"labels":["2019","2020","2021","2022","2023","2024"],"series":[{"name":"Revenue","values":[100,120,140,155,170,190]}]}` |
| title | `Revenue Trend 2019-2024` |
| x_label | `Year` |
| y_label | `Revenue (100M CNY)` |

> chart_data 是 JSON 字符串。复制到 Coze 表单时整段粘贴，不要手动输入。

**Test 2 — Pie Chart (Cost Structure)：**

| Field | Value |
|-------|-------|
| chart_type | `pie` |
| chart_data | `{"labels":["COGS","SG&A","Admin","R&D","Net Profit"],"values":[45,15,12,8,20]}` |
| title | `Cost Structure Breakdown` |
| x_label | (leave empty) |
| y_label | (leave empty) |

**Test 3 — Bar Chart (Peer Comparison)：**

| Field | Value |
|-------|-------|
| chart_type | `bar` |
| chart_data | `{"labels":["WuXi AppTec","Asymchem","Porton"],"series":[{"name":"Gross Margin","values":[0.38,0.42,0.35]}]}` |
| title | `Peer Gross Margin Comparison` |
| x_label | `Company` |
| y_label | `Gross Margin` |

---

# 第 6 部分：合并 — Orchestrator + Workflow

> 前提：A1-A5 全部工具已建好且自测通过。

## 6.1 创建主 Agent

| 字段 | 值 |
|------|-----|
| Name | `CDMO_Orchestrator` |
| Description | `Main coordinator for end-to-end CDMO equity research with semi-automated DCF. Orchestrates A1→A5 sequentially. Auto-analyzes data + knowledge base to suggest DCF assumptions in an editable interactive form at Step 4. Enforces human-in-the-loop: user must confirm or edit before DCF runs. Never auto-generates critical valuation inputs.` |

Prompt：`01_prompt_templates.md` 最下面 `## Orchestrator Prompt` → 复制 → 粘贴。
确认包含：Step 4 半自动假设生成 + 交互式表单 + JSON 覆盖优先级。

**插入工具引用**：Orchestrator 需要调用全部 5 个工具。在 Prompt 中找到每个 Step 中的 `{}`，依次选择对应插件：

| 位置 | 找到这一行 | 选择的插件 |
|------|----------|-----------|
| Step 1 | `Call the WRDS_Condensed_Financial_Stmt plugin at {}` | `WRDS_Condensed_Financial_Stmt` |
| Step 2 | `Call the Forecast_Condensed_Statements plugin at {}` | `Forecast_Condensed_Statements` |
| Step 3 | `Call the WRDS_Beta plugin at {}` | `WRDS_Beta` |
| Step 4 | `call the Get_DCF plugin at {}` | `Get_DCF` |
| Step 5 | `Call the Chart_Generator plugin at {}` | `Chart_Generator` |

> 每个 `{}` 独立操作：光标放上去 → 弹出下拉 → 选择对应工具 → Coze 自动替换。

5. **设置开场白（Opening Greeting）**：在 Agent 编辑页找到「开场白 / Opening Greeting」字段，粘贴以下英文开场白：

   > Hello! I am the CDMO Valuation Orchestrator. I will guide you through the complete equity research workflow: financial data retrieval (A1) → ratio analysis & forecasting (A2) → beta estimation (A3) → DCF valuation with semi-automated assumptions (A4) → charts & report assembly (A5). Please provide the company stock code, industry segment, and year range to begin.

## 6.2 挂载 5 个工具

打开 `CDMO_Orchestrator` → Tools → Add Tool → 依次添加：
- `WRDS_Condensed_Financial_Stmt`
- `Forecast_Condensed_Statements`
- `WRDS_Beta`
- `Get_DCF`
- `Chart_Generator`

## 6.3 创建 Workflow

| 字段 | 值 |
|------|-----|
| Name | `CDMO_Valuation_Workflow` |
| Description | `Complete CDMO equity research valuation pipeline. Trigger when user requests company valuation or DCF analysis. Executes sequentially: A1 retrieves financial statements from WRDS, A2 builds forecasts and FCFF projections, A3 estimates beta, pauses for user DCF assumption confirmation, A4 calculates DCF valuation, A5 generates charts. All critical assumptions require human approval. Outputs include financial statements, ratio tables, DCF valuation, charts, and analyst-style research report.` |

进入 Workflow 编辑器 → 添加 5 个节点并连线：
```
用户输入 → CDMO_Orchestrator → A1 → A2 → A3 → A4 → 输出
                                A5（由 Orchestrator 按需调用）
```
在 A3→A4 之间加「确认」节点（人工确认 DCF 假设）。

## 6.4 上传知识库

创建三个 Knowledge Base：
- `CDMO_Industry_Overview` — 行业总览
- `CDMO_Company_Research` — 公司深度
- `CDMO_Valuation_Reference` — 估值参考

每个至少上传一份 PDF。

## 6.5 测试 Orchestrator Agent

在 `CDMO_Orchestrator` 页面点击 Preview。输入："Please help me analyze WuXi AppTec (603259) in the CDMO industry, with peer companies Asymchem and Porton Pharma, for years 2019-2024." 期望 Orchestrator 按序调用 A1→A2→A3，暂停确认 DCF 假设，然后调用 A4→A5，最终输出完整报告。

---

# 第 7 部分：全流程测试

前提：A1-A5 独立测试全部通过。

用 `10_example_input.txt` 在 Orchestrator 对话框跑：
- 公司：WuXi AppTec / 603259
- 年份：2019-2024
- WRDS 账号密码
- DCF 假设（系统会暂停让你逐项确认）

检查：A1 报表 → A2 预测 + FCFF → A3 beta → 确认假设 → A4 DCF → A5 图表 → 最终报告。

再用 `10_test_input_1.txt` 和 `10_test_input_2.txt` 各跑一次。

---

# 第 8 部分：导出和提交

## 8.1 输出包

对话结果（文本 + 表格 + 图表截图）复制到 Word 保存。文件命名：`CDMO_Valuation_Output_{company}_{date}.docx`

## 8.2 提交物

1. Working Valuation Agent 链接
2. 3-5 分钟 Demo Video（参考 `12_demo_video_script.md`）
3. Prompt & Orchestration 文档（参考 `14_prompt_orchestration_doc.md`）
4. 样例输出包
5. User Guide（参考 `13_user_guide_template.md`）
6. 测试输入文件（`10_*.txt`）

---

# 常见问题

## 沙箱调用失败

| 现象 | 解决 |
|------|------|
| ModuleNotFoundError: No module named 'pandas' | 确认代码开头是 `def handler(args):` 而不是 `import pandas`。pandas 的 import 必须在 handler 内部 |
| ModuleNotFoundError: typings.XXX | 工具名称和代码第 2 行不一致。对照 0.4 节表格检查 |
| function /python/python not found | 创建工具时没选 Python 3。创建工具时必须选 Python 3（不是 Node.js） |
| pip / subprocess 报错 | Coze 沙箱禁用 pip。不要写任何 pip install 代码 |

## WRDS 连接

| 现象 | 解决 |
|------|------|
| 连接失败 | 检查账号密码、确认 Coze 沙箱有外网权限 |
| 数据为空 | stkcd 写 6 位数字，不要带 .SH；试改年份范围 |
| 表格全 0 | 年份范围可能无数据，改 `2018-2023` 或 `2020-2024` |

## 参数报错

| 现象 | 解决 |
|------|------|
| must be a valid JSON object / list | JSON 用英文双引号 `"`，不是中文 `""`。可在 jsonlint.com 验证 |
| DCF vps 异常 | long_term_growth 必须 < WACC。检查 D 是否太大 |

## 合理数值范围

| 参数 | 范围 | 说明 |
|------|------|------|
| sales_growth | 0.03~0.20 | CDMO 行业 3%-20% |
| Rf | 0.015~0.035 | 中国 10 年国债 |
| beta | 0.4~2.0 | CDMO 通常 0.8-1.5 |
| long_term_growth | 0.02~0.04 | 必须 < WACC |
| TaxRate | 0.15~0.25 | 高新技术 15%，普通 25% |
| Rd | 0.02~0.06 | 债务成本 2%-6% |

---

# 课堂对照

| 周次 | 要求 | 项目 | 状态 |
|------|------|------|------|
| W7 | 研报结构 | 行业→公司→财务→估值 | ✅ |
| W8 | 专业 Agent | A4 研报 + 知识库 | ✅ |
| W9 | 提交物 | 6 项全有模板 | ✅ |
| W10 | DCF 手动假设 | A3→A4 人工确认 | ✅ |


---
---

## 05.10 00:19 — Agent测试 + {}工具引用 + 依赖步骤下沉

### 0.4 节
- 新增「Prompt 中插入工具引用（{} 机制）」说明——课堂 W9 做法，在 Prompt 末尾输入 {} 选择对应工具

### 每个 A1-A4 节
- 依赖步骤从 0.6 下沉到「粘贴代码 → 加依赖 → 测试」流程中
- 「回到Agent填Prompt」新增两步：插入工具引用（{}选择工具）+ 测试 Agent
- 新增 Agent 测试节（1.6/2.6/3.6/4.6）——验证 Agent 能否正确调用工具

### Prompt 模板
- A1 Prompt 重写：匹配用户期望的对话流程（自动英文自我介绍 → 收集输入 → 调用工具）

### 依赖总览（0.6）
- 精简为汇总表，具体步骤见各节



---

## 05.10 00:26 — A5+Orchestrator补齐 + {}机制修正

### 0.4 节
- {} 机制说明修正：不是只在末尾加，而是在 Prompt 中**需要调用工具的位置**插入（LLM 需要上下文理解何时用哪个工具）

### Orchestrator（第6部分）
- Prompt 后新增 {} 步骤：依次插入 5 个工具的引用
- 新增 6.5 节：测试 Orchestrator Agent

### A1-A4
- {} 说明从"在 Prompt 末尾"改为"在 Prompt 中需要调用工具的位置"

# 修改日志（Change Log）

记录本手册和项目代码的每一次重要修改，方便追踪。

## 2026-05-10 00:34 — A1/A2/A3 字段统一为 username/password

### A1/A2/A3 代码
- 输入字段统一对齐为 `username / stkcd / start_year / end_year / password` 的表单风格
- 代码保留旧字段兼容：仍可识别 `wrds_username` / `pwd`

### 手册与示例
- A1/A2/A3 的字段表、测试 JSON 和示例输入统一更新
- A1 表单顺序与课堂截图保持一致

## 2026-05-10 00:46 — A1 Prompt: Role/Skills 插入，插件引用置中

### 变更内容
- 将 A1 Prompt 替换为包含 Role / Skills 的详细描述（含 Input Validation、Data Retrieval、Write Analysis 三项技能），并在数据检索步骤位置插入工具引用占位符 `{}`（即在 Prompt 中间、不是末尾）。
- 在 `02_coze_tool_fields.md` 中为 A1 新增 `company_dict` 字段（string，接受 JSON 或 Python dict 字符串），并在 `01_prompt_templates.md` 中加入示例输入。

### 说明与后续建议
- 编辑 Agent Prompt 时，在 `{}` 处选择 `WRDS_Financial_Data_Pivot`（或你在 Coze 中命名的 WRDS 插件），Coze 会插入工具引用并自动生成对应的表单输入项。
- 当前 A1 代码仍以单一 `stkcd` 为基本路径；若需要并行处理 `company_dict` 中的多家公司，请确认是否要扩展 A1 的并行查询与合并逻辑（我可以继续实现）。


## 2026-05-09 23:45 — tabulate 依赖 + 修改日志

### 依赖更新
- 新增 `tabulate v0.9.0`（pandas `to_markdown()` 的隐藏依赖）
- 最终依赖表：A1/A2/A3 装 numpy+pandas+wrds+tabulate；A4 装 numpy+pandas+tabulate；A5 装 numpy+pandas
- 每工具节的依赖步骤移到「粘贴代码 → 加依赖 → 测试」流程中

### 手册
- 末尾新增修改日志

---

## 2026-05-09 23:30 — A2 forward BS/IS + fillna 修正

### A2 代码
- 新增 ~100 行 forward projection（固定点现金循环），对齐课堂 W10 Walkthrough 2
- 新增输出 `bs_forecast`、`is_forecast`，现在 A2 共 13 个输出

### A1/A2 代码
- `fillna(0)` 从 `drop(stkcd)` 前移到后，解决 pandas 2.2.3 StringArray 报错

---

## 2026-05-09 23:15 — 手册重写 + 课堂对比

### 手册
- 每部分开头新增课堂对比框（课堂参考 + 多了什么）
- 测试段全部替换为可复制 JSON 代码块
- 操作流程修正为 Agent → Plugin → Tool 三层
- `object` → `string`（json.dumps 序列化）
- `start_year`/`end_year`: `string` → `number`
- array 字段补充子项目类型说明

---

## 2026-05-09 22:50 — 依赖版本对齐课堂

- numpy 2.2.5 / pandas 2.2.3 / wrds 3.3.0（对齐 W9 课堂）
- `_ensure_package` 移除（Coze 禁用 subprocess）
- import 全部移入 handler 内部

---

## 2026-05-09 22:20 — 项目结构扁平化

- 10 个子文件夹 → 23 个根目录文件，按数字编号
- 文件命名从中文 → 英文
