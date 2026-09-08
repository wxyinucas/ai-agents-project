# AI Agents Project

本仓库承载 AI Agents 课程从 W3 到 W16 的持续项目。代码只保留一份当前版本；每周目录保存证据和责任判断，不复制源码。

## 稳定布局

```text
course/                 教师维护的任务书、公开测试、fixture 与课程工具
common/                 教师维护的公共代码；按课程需要逐步增加
students/sXX/system/    学生唯一一份持续演化的系统
students/sXX/weeks/     学生按周追加的报告与证据
```

`sXX` 是教师分配的公开课程代号，例如 `s07`。学生只修改自己的 `students/sXX/**`；不要修改 `course/**`、`common/**`、其他学生目录、根 `.gitignore` 或仓库工作流。

## W3 起点

fork 并 clone 自己的仓库后，在仓库根目录运行：

```bash
bash course/week-03/init-student.sh sXX
code .
```

必须把 `sXX` 换成自己的课程代号。W3 的任务与验收入口见 `course/week-03/`。

## Git 汇总规则

- 平时在个人 fork 的 `origin/main` 持续工作。
- W6、W9、W14 等里程碑通过 PR 汇总到教师 `upstream/main`。
- 汇总后用 tag 冻结检查点，例如 `checkpoint-w06`、`checkpoint-w09`、`rc-w14`。
- 周次不是并行开发线，因此不建立 `dev-week-n` 分支。

课程会在需要相应能力时再加入公共代码、CI 和平台接口，不预先建立未来功能空壳。
