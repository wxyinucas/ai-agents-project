# Students

每名学生使用教师分配的公开课程代号，例如 `s07`：

```text
students/s07/
├── system/              唯一一份持续演化的可运行系统
└── weeks/
    └── week-03/         当周报告、证据与责任判断
```

学生只修改自己的目录。`system/` 不按周复制；Git 历史负责保存代码版本，`weeks/` 负责保存当时的判断与证据。

第一次建立个人目录时，从仓库根运行：

```bash
bash course/week-03/init-student.sh sXX
```

必须把 `sXX` 换成自己的课程代号。若目标目录已经存在，脚本会停止，不会覆盖已有内容。
