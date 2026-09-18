# AI Agents Project

本仓库承载 AI Agents 课程从 W3 到 W16 的持续项目。代码只保留一份当前版本；每周目录保存证据和责任判断，不复制源码。

## 稳定布局

```text
course/                 教师维护的任务书、公开测试、fixture 与课程工具
common/                 教师维护的公共代码；按课程需要逐步增加
students/sXX/system/    学生唯一一份持续演化的系统
students/sXX/weeks/     学生按周追加的报告与证据
```

`sXX` 是教师分配的公开课程代号，例如 `s07`。学生只修改自己的 `students/sXX/**`；不要修改根 `README.md`、`course/**`、`common/**`、`students/README.md`、其他学生目录、根 `.gitignore` 或仓库工作流。

## W3 起点

fork 并 clone 自己的仓库后，在仓库根目录运行：

```bash
bash course/week-03/init-student.sh sXX
code .
```

必须把 `sXX` 换成自己的课程代号。W3 的任务与验收入口见 `course/week-03/`。

## 当前路线

W4～W9 先在同一份 `system/` 中逐周增加小功能；每周任务和公开测试由 `course/` 发布，教师标准版在该周讨论后再公布。当前 W4 只增加可选的诊断追踪，仍然只读本地教学数据；旧 Longbridge 数据合同保留在 `course/pilots/`，不作为新 W4 作业。

本学期先运行本地公开测试，不配置 CI/CD。普通周继续使用个人 fork 的 `origin/main`；集中 PR 与 tag 周次尚未指定，不沿用旧版 W6/W9/W14 安排。

## Git 汇总规则

- 平时在个人 fork 的 `origin/main` 持续工作。
- 教师 `upstream/main` 保存最近一次已经接纳的全班汇总状态。
- 若某周需要向教师仓库汇总，会在当周任务中明确入口、范围与截止时间；当前不要求为 W4 建立 PR 或 tag。
- 周次不是并行开发线，因此不建立 `dev-week-n` 分支。

课程会在需要相应能力时再加入公共代码和平台接口，不预先建立未来功能空壳。
