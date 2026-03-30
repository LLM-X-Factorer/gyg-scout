import asyncio
import logging
import random
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
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]


async def _random_delay():
    delay = random.uniform(settings.scraper_delay_min, settings.scraper_delay_max)
    await asyncio.sleep(delay)


async def _extract_search_results(page: Page) -> list[dict]:
    """Extract activity cards from a GYG search results page."""
    results = []

    cards = await page.query_selector_all('[data-activity-card-id]')
    if not cards:
        cards = await page.query_selector_all('div[class*="activity-card"]')
    if not cards:
        cards = await page.query_selector_all('article')

    for card in cards:
        try:
            item = {}

            activity_id = await card.get_attribute("data-activity-card-id")
            item["gyg_id"] = activity_id

            title_el = await card.query_selector('h3, h2, [class*="title"]')
            if title_el:
                item["title"] = (await title_el.inner_text()).strip()

            link_el = await card.query_selector('a[href*="/activity/"], a[href*="-t"]')
            if not link_el:
                link_el = await card.query_selector("a")
            if link_el:
                href = await link_el.get_attribute("href")
                if href:
                    item["url"] = href if href.startswith("http") else BASE_URL + href

            price_el = await card.query_selector('[class*="price"] span, [data-test*="price"]')
            if not price_el:
                price_el = await card.query_selector('[class*="price"]')
            if price_el:
                price_text = (await price_el.inner_text()).strip()
                item["price_text"] = price_text
                price_num = "".join(c for c in price_text if c.isdigit() or c == ".")
                if price_num:
                    try:
                        item["price"] = float(price_num)
                    except ValueError:
                        pass

            rating_el = await card.query_selector('[class*="rating"], [aria-label*="rating"]')
            if rating_el:
                rating_text = await rating_el.get_attribute("aria-label") or await rating_el.inner_text()
                nums = [s for s in rating_text.replace(",", "").split() if s.replace(".", "").isdigit()]
                if nums:
                    try:
                        item["rating"] = float(nums[0])
                    except ValueError:
                        pass

            review_el = await card.query_selector('[class*="review-count"], [class*="ratings-count"]')
            if review_el:
                review_text = (await review_el.inner_text()).strip()
                review_num = "".join(c for c in review_text if c.isdigit())
                if review_num:
                    try:
                        item["review_count"] = int(review_num)
                    except ValueError:
                        pass

            duration_el = await card.query_selector('[class*="duration"]')
            if duration_el:
                item["duration"] = (await duration_el.inner_text()).strip()

            img_el = await card.query_selector("img")
            if img_el:
                item["image_url"] = await img_el.get_attribute("src")

            if item.get("title"):
                results.append(item)
        except Exception as e:
            logger.warning(f"Failed to extract card: {e}")
            continue

    return results


async def _extract_activity_detail(page: Page) -> dict:
    """Extract detailed info from a GYG activity detail page."""
    detail = {}

    desc_el = await page.query_selector('[class*="description"], [data-test*="description"]')
    if desc_el:
        detail["description"] = (await desc_el.inner_text()).strip()[:2000]

    highlights = []
    hl_els = await page.query_selector_all('[class*="highlight"] li, [data-test*="highlight"] li')
    for el in hl_els:
        text = (await el.inner_text()).strip()
        if text:
            highlights.append(text)
    if highlights:
        detail["highlights"] = highlights

    includes = []
    inc_section = await page.query_selector('[class*="included"], [data-test*="included"]')
    if inc_section:
        inc_items = await inc_section.query_selector_all("li")
        for el in inc_items:
            text = (await el.inner_text()).strip()
            if text:
                includes.append(text)
    if includes:
        detail["includes"] = includes

    excludes = []
    exc_section = await page.query_selector('[class*="excluded"], [data-test*="excluded"]')
    if exc_section:
        exc_items = await exc_section.query_selector_all("li")
        for el in exc_items:
            text = (await el.inner_text()).strip()
            if text:
                excludes.append(text)
    if excludes:
        detail["excludes"] = excludes

    cancel_el = await page.query_selector('[class*="cancellation"], [data-test*="cancellation"]')
    if cancel_el:
        detail["cancellation_policy"] = (await cancel_el.inner_text()).strip()[:500]

    supplier_el = await page.query_selector('[class*="supplier"], [class*="provider"]')
    if supplier_el:
        detail["supplier"] = (await supplier_el.inner_text()).strip()[:200]

    return detail


async def scrape_keyword(
    keyword: str,
    max_pages: int,
    task_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Scrape GYG search results for a keyword. Save activities to DB."""
    all_activities = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.scraper_headless)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        page = await context.new_page()

        try:
            for page_num in range(1, max_pages + 1):
                search_url = f"{BASE_URL}/s/?q={quote_plus(keyword)}&page={page_num}"
                logger.info(f"Scraping page {page_num}: {search_url}")

                await page.goto(search_url, wait_until="domcontentloaded", timeout=settings.scraper_timeout)
                await page.wait_for_timeout(2000)

                results = await _extract_search_results(page)
                if not results:
                    logger.info(f"No results on page {page_num}, stopping")
                    break

                logger.info(f"Found {len(results)} activities on page {page_num}")

                for item in results:
                    detail_url = item.get("url")
                    if detail_url:
                        try:
                            await _random_delay()
                            await page.goto(detail_url, wait_until="domcontentloaded", timeout=settings.scraper_timeout)
                            await page.wait_for_timeout(1500)
                            detail = await _extract_activity_detail(page)
                            item.update(detail)
                        except Exception as e:
                            logger.warning(f"Failed to get detail for {detail_url}: {e}")

                    activity = Activity(
                        task_id=task_id,
                        gyg_id=item.get("gyg_id"),
                        title=item.get("title", ""),
                        url=item.get("url"),
                        price=item.get("price"),
                        currency=item.get("currency", "EUR"),
                        rating=item.get("rating"),
                        review_count=item.get("review_count"),
                        supplier=item.get("supplier"),
                        duration=item.get("duration"),
                        description=item.get("description"),
                        highlights=item.get("highlights"),
                        includes=item.get("includes"),
                        excludes=item.get("excludes"),
                        cancellation_policy=item.get("cancellation_policy"),
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

        finally:
            await browser.close()

    return all_activities
