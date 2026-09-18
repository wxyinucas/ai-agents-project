# Common

这里保留给课程共同使用、由教师维护的稳定接口与公共实现。

当前 W4～W9 编程入门不要求学生使用本目录的旧行情合同。下列实现来自旧 W4 Longbridge 试点，保留供教师参考，尚未成为新版周任务：

- `course_common.week04.observe_market_file()` 读取本地课程行情 JSON；
- 统一检查 `course.market-bars.v1`、排序并生成脱敏证据；
- 统一计算与运行模式无关的稳定 `data_sha256`。

旧任务曾让学生项目通过 uv 本地 path dependency 使用本目录。新 W4 只延续 W3 的本地 `market-check`，不添加这项依赖。这里没有 Longbridge SDK、网络请求或凭证处理。
