import json
import logging
import markdown

from google import genai

from app.config import settings
from app.report_template import wrap_report_html

logger = logging.getLogger(__name__)


def _build_prompt(keyword: str, activities: list[dict]) -> str:
    summary_data = []
    for a in activities:
        summary_data.append({
            "title": a.get("title"),
            "price": a.get("price"),
            "rating": a.get("rating"),
            "review_count": a.get("review_count"),
            "duration": a.get("duration"),
            "supplier": a.get("supplier"),
            "description": a.get("description", "")[:300],
            "highlights": a.get("highlights", [])[:5],
        })

    return f"""你是一位资深旅游行业竞品分析师。我是一个准备在 GetYourGuide 上架产品的商家/供应商，正在对关键词「{keyword}」进行竞品调研。请基于以下采集数据，从商家竞品分析的角度生成一份详尽的中文调研报告（Markdown 格式）。

## 采集数据（共 {len(activities)} 个活动）:
{json.dumps(summary_data, ensure_ascii=False, indent=2)}

## 报告要求（以商家视角撰写）:

### 1. 市场概览
- 该关键词下的商品总量和市场活跃度
- 市场成熟度判断（蓝海/红海/细分机会）
- 主要品类和产品形态分布（跟团游、自由行、一日游、多日游、门票、体验等）

### 2. 价格策略分析
- 价格区间（最低、最高、均价、中位数），使用人民币（¥/CNY）
- 价格带分布（按区间统计产品数量占比）
- 不同价格带的竞争激烈程度
- **定价建议**：作为新入场商家，建议的定价区间和理由

### 3. 竞品评分与口碑分析
- 评分分布（高分段集中度）
- 高评分商品（4.8+）的共性特征是什么？
- 低评分商品的常见问题（如果有）
- **口碑启示**：哪些因素最影响用户评价？

### 4. 头部竞品深度拆解
- 列出 TOP 10 竞品（按评论数排序），逐一分析：
  - 产品名称、价格、评分、评论数
  - 产品卖点和差异化策略
  - 预估月销量（基于评论数推算）
- 头部竞品的共性打法

### 5. 供应商竞争格局
- 有哪些主要供应商/运营商？
- 是否存在垄断型玩家？
- 中小供应商的生存空间分析

### 6. 产品设计洞察
- 热门时长设计（哪些时长最受欢迎）
- 高频出现的卖点关键词
- 常见的包含项/不包含项设计
- 取消政策的主流做法

### 7. 市场机会与入场策略
- **蓝海细分**：尚未被充分覆盖的细分品类或主题
- **差异化方向**：如何与现有竞品形成差异
- **定价策略**：建议的价格定位
- **产品设计建议**：时长、行程亮点、包含项等具体建议
- **冷启动策略**：新商品如何快速积累评论和排名

### 8. 风险提示
- 该市场的主要风险和挑战
- 季节性因素
- 需要注意的合规/运营要点

### 9. 总结：行动清单
- 列出 5-8 条具体可执行的行动建议，按优先级排序

请用数据说话，引用具体数字。语言风格：专业但易读，适合商业决策参考。全文使用中文。Output in Markdown format only."""


async def analyze_activities(keyword: str, activities: list[dict]) -> tuple[str, str]:
    """Use Gemini to analyze scraped activities. Returns (markdown, html)."""
    if not activities:
        md = f"# Research Report: {keyword}\n\nNo activities found for this keyword."
        return md, wrap_report_html(markdown.markdown(md), title=f"Report: {keyword}")

    if not settings.gemini_api_key:
        md = _generate_fallback_report(keyword, activities)
        body = markdown.markdown(md, extensions=["tables"])
        return md, wrap_report_html(body, title=f"竞品分析报告：{keyword}")

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _build_prompt(keyword, activities)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        md = response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        md = _generate_fallback_report(keyword, activities)

    body_html = markdown.markdown(md, extensions=["tables", "fenced_code"])
    html = wrap_report_html(body_html, title=f"竞品分析报告：{keyword}")
    return md, html


def _generate_fallback_report(keyword: str, activities: list[dict]) -> str:
    """Generate a basic statistical report without LLM."""
    prices = [a["price"] for a in activities if a.get("price")]
    ratings = [a["rating"] for a in activities if a.get("rating")]
    reviews = [a["review_count"] for a in activities if a.get("review_count")]

    lines = [
        f"# Research Report: {keyword}",
        f"\n*Generated from {len(activities)} activities (statistical summary, no AI analysis)*\n",
        "## Price Analysis",
    ]

    if prices:
        prices.sort()
        avg_price = sum(prices) / len(prices)
        median_price = prices[len(prices) // 2]
        lines.extend([
            f"- **Range**: ¥{min(prices):.0f} - ¥{max(prices):.0f}",
            f"- **Average**: ¥{avg_price:.0f}",
            f"- **Median**: ¥{median_price:.0f}",
            f"- **Products with price**: {len(prices)}/{len(activities)}",
        ])
    else:
        lines.append("- No price data available")

    lines.append("\n## Rating Analysis")
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        lines.extend([
            f"- **Range**: {min(ratings):.1f} - {max(ratings):.1f}",
            f"- **Average**: {avg_rating:.1f}",
            f"- **Products with rating**: {len(ratings)}/{len(activities)}",
        ])
    else:
        lines.append("- No rating data available")

    if reviews:
        lines.append("\n## Review Volume")
        total_reviews = sum(reviews)
        lines.extend([
            f"- **Total reviews**: {total_reviews:,}",
            f"- **Average per product**: {total_reviews // len(reviews):,}",
            f"- **Max reviews**: {max(reviews):,}",
        ])

    lines.append("\n## Top Products")
    lines.append("| Title | Price | Rating | Reviews |")
    lines.append("|-------|-------|--------|---------|")
    sorted_activities = sorted(
        activities,
        key=lambda x: (x.get("rating") or 0, x.get("review_count") or 0),
        reverse=True,
    )
    for a in sorted_activities[:10]:
        title = (a.get("title") or "")[:50]
        price = f"¥{a['price']:.0f}" if a.get("price") else "-"
        rating = f"{a['rating']:.1f}" if a.get("rating") else "-"
        reviews_str = f"{a['review_count']:,}" if a.get("review_count") else "-"
        lines.append(f"| {title} | {price} | {rating} | {reviews_str} |")

    return "\n".join(lines)
