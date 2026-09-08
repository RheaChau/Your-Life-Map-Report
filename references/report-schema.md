# report.json 结构

最小可用示例：

```json
{
  "subject_code": "A01",
  "language": "zh-CN",
  "locale": "zh-CN",
  "labels": {"cover_title": "八字 × 紫微", "cover_subtitle": "人生主题参考报告"},
  "generated_at": "2026-08-30",
  "as_of_date": "2026-08-30",
  "method": "八字 + 紫微斗数综合印证（算法层版本号）",
  "display_birth": {
    "calendar": "solar",
    "date": "2000-01-01",
    "time": "12:00",
    "gender": "男",
    "birth_place": "云南·普洱",
    "current_location": "上海"
  },
  "chart": {
    "bazi_pillars": ["年柱", "月柱", "日柱", "时柱"],
    "day_master": "日主",
    "wuxing_summary": "五行统计与旺衰摘要",
    "dayun": [{"period": "甲子", "age": "10-19", "theme": "主题"}],
    "ziwei_summary": "命宫、身宫、四化和关键宫位摘要"
  },
  "forecast": {
    "anchor_date": "2026-08-30",
    "next_3_years": {"start": "2026-08-30", "end": "2029-08-30", "years": [2026, 2027, 2028]},
    "next_3_months": {"start": "2026-08-30", "end": "2026-11-30"}
  },
  "overall_note": "整体阅读说明：本报告把传统术语当作自我观察的语言；章节不重复写置信度或免责声明。",
  "pattern_analysis": [
    {
      "name": "示例格局",
      "status": "成立 / 有条件成立 / 兼格或局部关系 / 不取此格",
      "classical_text": "《古籍》：短句原文",
      "evidence": "月令、透干、根气、制化与组合证据",
      "day_master_effect": "身强身弱如何改变格局表现",
      "dayun_effects": [{"period": "甲子", "effect": "该运引动的结构与现实主题"}]
    }
  ],
  "sections": [
    {"title": "01｜你是什么样的人：人格底色与行为模式", "basis": "盘面依据", "content": "通俗解读与现实场景", "actions": ["可执行建议"]}
  ],
  "disclaimer": "本报告基于传统八字与紫微斗数理论框架，仅供文化研究与娱乐参考。"
}
```

`sections` 是有序数组；`content` 可包含换行，`actions`、`cautions`、`evidence` 可选。每个 `content` 的第一段应是有出处的古籍原文节录，第二段起再写盘面依据与现代汉语情境解读。`confidence` 字段为兼容旧数据保留，但渲染器不再逐章显示；若需要说明不确定性，请写入顶层 `overall_note`，集中说明一次。建议至少提供以下清晰章节：人格底色与行为模式、优势与盲点、健康与压力、事业/工作方式、适合行业、财富与资源、感情与亲密关系、父母/家庭、社交与合作、五行与方位、完整十年大运、未来 3 年、未来 3 个月、日常提运技巧、长期注意事项。

`sections[].title` 应为总结型陈述句，直接归纳该模块的整体判断；避免问句、冒号和栏目式提问。标题应能脱离正文独立表达结论。
