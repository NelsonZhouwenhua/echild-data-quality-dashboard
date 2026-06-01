# 两分钟面试展示说明

这个项目完全使用合成数据，不包含或声称访问 ECHILD、HES、NPD 或儿童社会照护真实记录。

建议展示顺序：

1. 打开 `01 Resource overview`，说明项目模拟 health、education 和 social-care 三类行政数据，以及 linked data resource 的维护问题。
2. 打开 `04 Linkage-quality evaluation`，强调页面展示的是 linkage rate，而不是简单 matched count。说明需要比较不同 deprivation quintile 和 region，检查可能的 linkage bias。
3. 打开 `05 Cohort feasibility builder`，设置 index hospital-admission cohort，改变出生年份、诊断分组、follow-up 和 required modules。说明系统会动态生成 cohort attrition、warning 和 extract manifest。
4. 打开 `07 Phenotype repository`，说明 phenotype definition 需要版本、逻辑、变量、缺失值处理规则和限制说明。
5. 打开 `08 Data refresh comparison`，说明数据资源不是一次性分析；每次 refresh 都需要确认 source、module、year coverage 和 QA status。
6. 说明公开页面只显示 aggregate outputs，小样本单元格使用示例 suppression rule。真实 row-level records 应留在获批的 TRE 内部。

可以使用的英文总结：

> I built a fully synthetic linked child administrative-data support portal. It demonstrates how I would help researchers scope a question, assess data availability, inspect linkage quality and possible linkage bias, construct a cohort spine, review attrition, document phenotype logic and generate an aggregate feasibility report. The public app exposes aggregate outputs only; row-level records are treated as TRE-only data.
