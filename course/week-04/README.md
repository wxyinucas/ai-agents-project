# W4｜真实行情成为可验证的数据

W3 让一份本地 CSV 能被程序读懂；W4 再向前一步：把来源不同的日线行情放进同一份课程数据合同，并用证据判断它是否可信。

## 本目录中的文件

- `PROJECT_BRIEF.txt`：学生交给 Agent 的完整自然语言契约；
- `query.json`：本周唯一查询，教师取数工具与 replay 共用；
- `data/synthetic-replay.json`：不联网也能完成课程的合成数据；
- `tests/`：W3 回归测试与 W4 公开黑盒测试；
- `report-template.md`：只记录证据与判断，不粘贴原始行情；
- `init-week.sh`：在已有学生目录中建立 W4 报告。

`synthetic-replay.json` 的价格和成交量均为教学用合成值，不是 AAPL 的历史行情。它只模拟真实取数工具应当交付的数据形状。

本周也是 `common/` 第一次承载真实功能：公共包统一读取、验收、排序和计算摘要；每名学生只在自己的 `system/` 中接入一个很薄的命令入口。

## 学生入口

在仓库根目录运行一次：

```bash
bash course/week-04/init-week.sh sXX
```

然后进入自己的持续项目：

```bash
cd students/sXX/system
```

把 `../../../course/week-04/PROJECT_BRIEF.txt` 交给本地 Agent。完成后运行：

```bash
uv run --locked market-observe ../../../course/week-04/data/synthetic-replay.json
uv run --locked pytest -q ../../../course/week-04/tests
```

第二条命令已包含 W3 的五项回归检查；不需要再单独运行 W3 测试。

## 安全边界

学生程序只读取本地标准 JSON，不联网、不读取环境变量或剪贴板，也不安装 Longbridge SDK。平台注册、凭证和只读取数由教师提供的受信工具单独处理；它们不进入学生项目和公开证据。

若真实平台临时不可用，使用 `synthetic-replay.json` 仍可取得完整的 W4 课程结果。`replay` 是明确记录的数据来源，不是假装调用过平台。

合同检查能证明文档内部自洽，不能单独证明平台真的被调用；真实来源仍由受信取数边界和教师演示负责。
