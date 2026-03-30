import asyncio
import logging
import random
import re
from urllib.parse import quote_plus

from playwright.async_api import async_playwright, Page
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.task import Activity, Task

logger = logging.getLogger(__name__)

BASE_URL = "https://www.getyourguide.com"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

EXTRACT_CARDS_JS = """
() => {
    // Helper: parse common fields from text content
    function parseCardText(allText, href) {
        let gygId = null;
        if (href) {
            const match = href.match(/-t(\\d+)/);
            if (match) gygId = match[1];
        }

        // Price: last "From €XX" pattern (discounted price)
        let price = null;
        let currency = null;
        const priceMatches = allText.match(/From[\\s]*([€$£¥])([\\d,.]+)/g);
        if (priceMatches && priceMatches.length > 0) {
            const last = priceMatches[priceMatches.length - 1];
            const pm = last.match(/From[\\s]*([€$£¥])([\\d,.]+)/);
            if (pm) {
                currency = pm[1] === '€' ? 'EUR' : pm[1] === '$' ? 'USD' : pm[1] === '£' ? 'GBP' : pm[1] === '¥' ? 'JPY' : 'EUR';
                price = parseFloat(pm[2].replace(',', ''));
            }
        }

        // Review count: (N,NNN)
        let reviewCount = null;
        const reviewMatch = allText.match(/\\(([\\d,]+)\\)/);
        if (reviewMatch) {
            reviewCount = parseInt(reviewMatch[1].replace(',', ''));
        }

        // Rating: standalone decimal like 4.9 or 5 before parenthesis
        let rating = null;
        const ratingMatch = allText.match(/(\\d\\.\\d)\\s*\\(/);
        if (ratingMatch) {
            rating = parseFloat(ratingMatch[1]);
        } else {
            // Match standalone "5" before "("
            const ratingMatch2 = allText.match(/([45])\\s*\\(/);
            if (ratingMatch2) rating = parseFloat(ratingMatch2[1]);
        }

        // Duration
        let duration = null;
        const durationMatch = allText.match(/(\\d+(?:\\.\\d+)?\\s*-\\s*\\d+(?:\\.\\d+)?\\s+(?:hours?|days?|minutes?))|(\\d+(?:\\.\\d+)?\\s+(?:hours?|days?|minutes?))/i);
        if (durationMatch) duration = durationMatch[0];
        if (!duration) {
            const minMatch = allText.match(/(\\d+)\\s*minutes/i);
            if (minMatch) duration = minMatch[0];
        }

        return { gygId, price, currency, rating, reviewCount, duration };
    }

    const results = [];
    const seenIds = new Set();

    // Strategy 1: vertical-activity-card (grid layout, e.g. "paris tour")
    document.querySelectorAll('[data-test-id="vertical-activity-card"]').forEach(card => {
        const link = card.querySelector('[data-test-id="vertical-activity-card-link"]');
        const title = card.querySelector('[data-test-id="activity-card-title"]');
        const ratingEl = card.querySelector('[data-test-id="activity-card-rating-overall"]');
        const img = card.querySelector('img');
        const href = link ? link.getAttribute('href') : null;
        const allText = card.textContent || '';
        const parsed = parseCardText(allText, href);

        if (ratingEl) parsed.rating = parseFloat(ratingEl.textContent.trim()) || parsed.rating;
        if (parsed.gygId && !seenIds.has(parsed.gygId)) {
            seenIds.add(parsed.gygId);
            results.push({
                gyg_id: parsed.gygId,
                title: title ? title.textContent.trim() : null,
                url: href,
                price: parsed.price,
                currency: parsed.currency,
                rating: parsed.rating,
                review_count: parsed.reviewCount,
                duration: parsed.duration,
                image_url: img ? img.getAttribute('src') : null,
            });
        }
    });

    // Strategy 2: activity links in list layout (e.g. "shenzhen")
    if (results.length === 0) {
        document.querySelectorAll('a[href*="-t"]').forEach(link => {
            const href = link.getAttribute('href') || '';
            if (!href.match(/-t\\d+\\//)) return; // must be activity URL pattern
            const idMatch = href.match(/-t(\\d+)\\//);
            if (!idMatch) return;
            const gygId = idMatch[1];
            if (seenIds.has(gygId)) return;

            const allText = link.textContent || '';
            if (allText.length < 10) return; // skip navigation links

            const parsed = parseCardText(allText, href);
            const img = link.querySelector('img');

            // Extract title: usually the longest meaningful text line
            const titleEl = link.querySelector('h2, h3, [class*="title"]');
            let title = titleEl ? titleEl.textContent.trim() : null;
            if (!title) {
                // Fallback: derive from URL slug
                const slugMatch = href.match(/\\/([^/]+)-t\\d+/);
                if (slugMatch) {
                    title = slugMatch[1].replace(/-/g, ' ').replace(/^\\w/, c => c.toUpperCase());
                }
            }

            if (title && title.length > 5) {
                seenIds.add(gygId);
                results.push({
                    gyg_id: gygId,
                    title: title,
                    url: href,
                    price: parsed.price,
                    currency: parsed.currency,
                    rating: parsed.rating,
                    review_count: parsed.reviewCount,
                    duration: parsed.duration,
                    image_url: img ? img.getAttribute('src') : null,
                });
            }
        });
    }

    return results;
}
"""

EXTRACT_DETAIL_JS = """
() => {
    const result = {};

    // Description
    const aboutSection = document.querySelector('[data-test-id="about-this-activity"]');
    if (aboutSection) {
        result.description = aboutSection.textContent.trim().substring(0, 2000);
    }

    // Highlights
    const highlights = [];
    document.querySelectorAll('[data-test-id="highlights"] li, [data-test-id="activity-highlights"] li').forEach(li => {
        const t = li.textContent.trim();
        if (t) highlights.push(t);
    });
    if (highlights.length) result.highlights = highlights;

    // Includes / Excludes
    const includes = [];
    const excludes = [];
    document.querySelectorAll('[data-test-id="inclusion-list"] li, [data-test-id="inclusions"] li').forEach(li => {
        includes.push(li.textContent.trim());
    });
    document.querySelectorAll('[data-test-id="exclusion-list"] li, [data-test-id="exclusions"] li').forEach(li => {
        excludes.push(li.textContent.trim());
    });
    if (includes.length) result.includes = includes;
    if (excludes.length) result.excludes = excludes;

    // Cancellation policy
    const cancel = document.querySelector('[data-test-id="cancellation-policy"]');
    if (cancel) result.cancellation_policy = cancel.textContent.trim().substring(0, 500);

    // Supplier
    const supplier = document.querySelector('[data-test-id="supplier-name"], [data-test-id="offered-by"] a');
    if (supplier) result.supplier = supplier.textContent.trim();

    return result;
}
"""


async def _random_delay():
    delay = random.uniform(settings.scraper_delay_min, settings.scraper_delay_max)
    await asyncio.sleep(delay)


async def scrape_keyword(
    keyword: str,
    max_pages: int,
    task_id: int,
    db: AsyncSession,
) -> list[dict]:
    all_activities = []
    seen_ids = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.scraper_headless)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = await context.new_page()
        await page.add_init_script(
            'Object.defineProperty(navigator, "webdriver", { get: () => false });'
        )

        try:
            for page_num in range(1, max_pages + 1):
                search_url = (
                    f"{BASE_URL}/s/?q={quote_plus(keyword)}"
                    f"&page={page_num}&currency=EUR"
                )
                logger.info(f"Scraping page {page_num}: {search_url}")

                await page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=settings.scraper_timeout,
                )
                await page.wait_for_timeout(3000)

                results = await page.evaluate(EXTRACT_CARDS_JS)
                if not results:
                    logger.info(f"No results on page {page_num}, stopping")
                    break

                logger.info(f"Found {len(results)} activities on page {page_num}")

                for item in results:
                    if item.get("url") and not item["url"].startswith("http"):
                        item["url"] = BASE_URL + item["url"]
                    if item.get("url"):
                        item["url"] = re.sub(r'\?ranking_uuid=[^&]+', '', item["url"])

                    gyg_id = item.get("gyg_id")
                    if gyg_id and gyg_id in seen_ids:
                        continue
                    if gyg_id:
                        seen_ids.add(gyg_id)

                    activity = Activity(
                        task_id=task_id,
                        gyg_id=item.get("gyg_id"),
                        title=item.get("title", ""),
                        url=item.get("url"),
                        price=item.get("price"),
                        currency=item.get("currency", "EUR"),
                        rating=item.get("rating"),
                        review_count=item.get("review_count"),
                        duration=item.get("duration"),
                        image_url=item.get("image_url"),
                        raw_data=item,
                    )
                    db.add(activity)
                    all_activities.append(item)

                task = await db.get(Task, task_id)
                if task:
                    task.progress = int((page_num / max_pages) * 70)
                await db.commit()

                if page_num < max_pages:
                    await _random_delay()

            # Scrape details for top activities (by review count)
            sorted_items = sorted(
                all_activities,
                key=lambda x: x.get("review_count") or 0,
                reverse=True,
            )
            detail_count = min(10, len(sorted_items))
            for i, item in enumerate(sorted_items[:detail_count]):
                detail_url = item.get("url")
                if not detail_url:
                    continue
                try:
                    await _random_delay()
                    logger.info(f"Scraping detail {i+1}/{detail_count}: {item.get('title', '')[:50]}")
                    await page.goto(
                        detail_url,
                        wait_until="domcontentloaded",
                        timeout=settings.scraper_timeout,
                    )
                    await page.wait_for_timeout(2000)
                    detail = await page.evaluate(EXTRACT_DETAIL_JS)
                    item.update(detail)

                    # Update DB record
                    from sqlalchemy import select
                    result = await db.execute(
                        select(Activity).where(
                            Activity.task_id == task_id,
                            Activity.gyg_id == item.get("gyg_id"),
                        ).limit(1)
                    )
                    act = result.scalar_one_or_none()
                    if act:
                        act.description = detail.get("description")
                        act.highlights = detail.get("highlights")
                        act.includes = detail.get("includes")
                        act.excludes = detail.get("excludes")
                        act.cancellation_policy = detail.get("cancellation_policy")
                        act.supplier = detail.get("supplier")
                        act.raw_data = item
                        await db.commit()
                except Exception as e:
                    logger.warning(f"Failed to get detail: {e}")

        finally:
            await browser.close()

    return all_activities
