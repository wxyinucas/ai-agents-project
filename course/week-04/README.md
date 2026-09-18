# W4｜让程序留下两处足迹

W3 的 `market-check` 已能报告本地 CSV 的可见事实。本周只增加可选的 `--trace`：程序处理输入路径和读入 CSV 时，向 `stderr` 留下两处追踪。追踪用于诊断，不改变原来的检查结果；数据仍是本地教学样例，不接 Longbridge。

在仓库根目录建立本周报告：

```bash
bash course/week-04/init-week.sh sXX
```

然后进入自己的 `students/sXX/system/`，阅读 [`PROJECT_BRIEF.txt`](./PROJECT_BRIEF.txt)，让 Agent 只修改本人 `system/`。完成后运行：

```bash
uv run --locked market-check ../../../course/week-03/tests/fixtures/another_valid_prices.csv
uv run --locked market-check ../../../course/week-03/tests/fixtures/another_valid_prices.csv --trace
uv run --locked market-check ../../../course/week-03/tests/fixtures/missing_close.csv --trace
uv run --locked pytest -q ../../../course/week-03/tests ../../../course/week-04/tests
```

第三条命令应该明确失败，但仍留下两处追踪；文件不存在时只会到达第一处。累计公开测试为 W3 的 5 项加 W4 的 3 项；本周不配置 CI/CD，也不要求提交 PR 或 tag。

W3 教师基线会在 W3 第三课时讨论后公布；W4 教师实现会在 W4 结束后公布，本周任务和公开测试不依赖它们。基线已公布且需要接续时，先保留个人旧版本的 Git 记录，检查迁入本人目录后的 diff，并在报告中写明来源。不要直接在教师区写个人作业。
