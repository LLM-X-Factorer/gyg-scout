import json
import logging
import markdown

from google import genai

from app.config import settings
from app.report_template import wrap_report_html

logger = logging.getLogger(__name__)


def _build_merchant_section(name: str) -> str:
    return f"""

### 11. 「{name}」专属商业诊断与战略建议（重点章节）

**重要说明**：本章节专门为商家「{name}」撰写。请从数据中找到该商家的所有产品，进行深度分析和战略建议。请保持辩证思维——既指出优势也不回避问题，既看到机会也警示风险。

#### 11.1 现状诊断
- **产品矩阵审视**：「{name}」目前有哪些产品？覆盖了哪些品类？产品之间的关系是什么（互补？重叠？蚕食？）
- **市场位置评估**：在整个市场中处于什么位置？（头部/腰部/尾部）与头部竞品的差距有多大？差距的核心原因是什么？
- **核心竞争力**：「{name}」当前最大的竞争优势是什么？这个优势是否可持续？是否容易被复制？
- **关键短板**：最需要改进的是什么？（产品设计？定价？文案？评论数？品类覆盖？）

#### 11.2 商业模式思考
请从商业模式的角度辩证分析：

**增长路径选择**（需辩证讨论利弊）：
- **路径A：深耕现有品类** — 在当前产品领域做到极致，提升客单价和复购
  - 正方论点：专注带来口碑，避免资源分散
  - 反方论点：天花板明显，单品类抗风险能力弱
- **路径B：横向扩展品类** — 开发新的产品线（比如从科技游扩展到文化游/美食游）
  - 正方论点：多元化降低风险，交叉销售提升LTV
  - 反方论点：每个新品类都需要投入，可能稀释品牌定位
- **路径C：纵向整合供应链** — 比如自建导游团队、合作独家景点
  - 正方论点：提升服务品质和利润率
  - 反方论点：重资产运营，灵活性降低

请基于「{name}」的实际数据，推荐最优路径并论证。

**定价策略辩证**：
- 当前定价在市场中的竞争力如何？
- 是否有提价空间？提价的前提条件是什么？
- 低价引流 vs 高价高质，哪种更适合「{name}」当前阶段？为什么？

**规模化思考**：
- 「{name}」当前的业务规模如何？（从评论数和产品数推测）
- 规模化的主要瓶颈是什么？（导游供给？获客成本？运营能力？）
- 如何突破瓶颈？

#### 11.3 竞争策略
- **与头部的差异化**：不应正面硬刚头部，「{name}」应该怎样错位竞争？
- **护城河构建**：如何建立竞争对手难以复制的优势？（独家资源？品牌认知？服务标准？）
- **防御策略**：如果头部竞品进入「{name}」的优势领域，如何应对？

#### 11.4 具体可落地的行动建议
请给出 **5-8 条具体、可执行、有优先级** 的行动建议，每条包括：
- **做什么**（具体动作）
- **为什么**（基于数据的理由）
- **预期效果**
- **风险/代价**
- **优先级**（P0 立即执行 / P1 本月执行 / P2 本季度执行）

#### 11.5 需要警惕的陷阱
- 列出 3-5 个「{name}」在扩张过程中最可能踩的坑
- 每个陷阱附带具体的规避建议
"""


def _build_prompt(keyword: str, activities: list[dict], merchant_name: str | None = None) -> str:
    summary_data = []
    for a in activities:
        summary_data.append({
            "title": a.get("title"),
            "price": a.get("price"),
            "rating": a.get("rating"),
            "review_count": a.get("review_count"),
            "duration": a.get("duration"),
            "supplier": a.get("supplier"),
            "description": a.get("description", "")[:500],
            "highlights": a.get("highlights", [])[:8],
            "includes": a.get("includes", [])[:8],
            "excludes": a.get("excludes", [])[:5],
            "cancellation_policy": a.get("cancellation_policy", ""),
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

### 5. 供应商竞争格局与商家画像
- 有哪些主要供应商/运营商？列出所有可识别的供应商名称
- 是否存在垄断型玩家？头部供应商各自的产品数量和市场份额
- 中小供应商的生存空间分析

### 6. 商家产品策略深度拆解（重点章节）
这是本报告的核心分析章节。请逐一分析**有详情数据的商家**，深度拆解每个商家的产品逻辑和运营思路：

对于每个可识别的供应商/商家：
- **商家名称与产品矩阵**：该商家在此关键词下有几个产品？产品之间如何差异化？
- **定价逻辑**：高中低档如何布局？是否有折扣/促销策略？
- **产品包装思路**：
  - 行程描述的写法和卖点提炼手法（分析 description 和 highlights 的文案套路）
  - 包含项/不包含项的设计策略（哪些包含是真正的增值，哪些是标准配置）
  - 时长设计的考量
- **差异化策略**：该商家与其他商家相比的独特之处是什么？
- **运营手法推测**：
  - 从评论数和评分推测其获客能力和服务质量
  - 标题/描述中的 SEO 关键词策略
  - 取消政策的选择（免费取消vs不可退款）及其商业逻辑

最后总结：
- **最值得学习的商家是谁？为什么？**
- **不同商家的产品思路有什么共性规律？**
- **从商家视角看，有哪些"套路"或"门道"值得借鉴？**

### 7. 产品设计洞察
- 热门时长设计（哪些时长最受欢迎）
- 高频出现的卖点关键词
- 常见的包含项/不包含项设计
- 取消政策的主流做法
- 产品描述的文案模式和写作技巧

### 8. 市场机会与入场策略
- **蓝海细分**：尚未被充分覆盖的细分品类或主题
- **差异化方向**：如何与现有竞品形成差异
- **定价策略**：建议的价格定位
- **产品设计建议**：时长、行程亮点、包含项等具体建议
- **文案策略**：标题和描述的写法建议，参考头部商家的成功文案套路
- **冷启动策略**：新商品如何快速积累评论和排名

### 9. 风险提示
- 该市场的主要风险和挑战
- 季节性因素
- 需要注意的合规/运营要点

### 10. 总结：行动清单
- 列出 5-8 条具体可执行的行动建议，按优先级排序
{_build_merchant_section(merchant_name) if merchant_name else ""}
请用数据说话，引用具体数字。语言风格：专业但易读，适合商业决策参考。全文使用中文。Output in Markdown format only."""


async def analyze_activities(keyword: str, activities: list[dict], merchant_name: str | None = None) -> tuple[str, str]:
    """Use Gemini to analyze scraped activities. Returns (markdown, html)."""
    if not activities:
        md = f"# Research Report: {keyword}\n\nNo activities found for this keyword."
        return md, wrap_report_html(markdown.markdown(md), title=f"Report: {keyword}")

    if not settings.gemini_api_key:
        md = _generate_fallback_report(keyword, activities)
        body = markdown.markdown(md, extensions=["tables"])
        return md, wrap_report_html(body, title=f"竞品分析报告：{keyword}")

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _build_prompt(keyword, activities, merchant_name=merchant_name)

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
