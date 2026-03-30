import json
import logging
import markdown

from google import genai

from app.config import settings

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

    return f"""You are a professional travel product analyst. Analyze the following GetYourGuide search results for the keyword "{keyword}" and generate a comprehensive research report in Markdown format.

## Data ({len(activities)} activities collected):
{json.dumps(summary_data, ensure_ascii=False, indent=2)}

## Report Requirements:
Generate a structured report with these sections:

### 1. Market Overview
- Total number of products found
- Overall market characteristics for this keyword

### 2. Price Analysis
- Price range (min, max, average, median)
- Price tiers/bands distribution
- Price sweet spots

### 3. Rating & Review Analysis
- Rating distribution
- Correlation between price and rating
- Top-rated products and their common traits

### 4. Supplier Landscape
- Number of unique suppliers
- Top suppliers by product count and ratings
- Market concentration

### 5. Product Feature Analysis
- Common duration patterns
- Popular highlights/selling points
- Common inclusions/exclusions

### 6. Competitive Insights
- What makes top products stand out
- Market gaps and opportunities
- Recommendations for new entrants

### 7. Summary & Key Takeaways
- Top 3-5 actionable insights

Write in a professional, data-driven tone. Use specific numbers from the data. Output in Markdown format only."""


async def analyze_activities(keyword: str, activities: list[dict]) -> tuple[str, str]:
    """Use Gemini to analyze scraped activities. Returns (markdown, html)."""
    if not activities:
        md = f"# Research Report: {keyword}\n\nNo activities found for this keyword."
        return md, markdown.markdown(md)

    if not settings.gemini_api_key:
        md = _generate_fallback_report(keyword, activities)
        return md, markdown.markdown(md, extensions=["tables"])

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _build_prompt(keyword, activities)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        md = response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        md = _generate_fallback_report(keyword, activities)

    html = markdown.markdown(md, extensions=["tables", "fenced_code"])
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
            f"- **Range**: €{min(prices):.0f} - €{max(prices):.0f}",
            f"- **Average**: €{avg_price:.0f}",
            f"- **Median**: €{median_price:.0f}",
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
        price = f"€{a['price']:.0f}" if a.get("price") else "-"
        rating = f"{a['rating']:.1f}" if a.get("rating") else "-"
        reviews_str = f"{a['review_count']:,}" if a.get("review_count") else "-"
        lines.append(f"| {title} | {price} | {rating} | {reviews_str} |")

    return "\n".join(lines)
