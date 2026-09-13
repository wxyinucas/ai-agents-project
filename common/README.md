# Common

这里保留给课程共同使用、由教师维护的稳定接口与公共实现。

W3 只冻结了所有权边界；W4 第一次加入真实公共能力：

- `course_common.week04.observe_market_file()` 读取本地课程行情 JSON；
- 统一检查 `course.market-bars.v1`、排序并生成脱敏证据；
- 统一计算与运行模式无关的稳定 `data_sha256`。

学生项目通过 uv 本地 path dependency 使用本目录，不复制这份实现，也不修改公共区。这里没有 Longbridge SDK、网络请求或凭证处理。
