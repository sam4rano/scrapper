import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import nest_asyncio

nest_asyncio.apply()

async def extract_article_content(page, article_url):
    try:
        await page.goto(article_url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
        # Extract article content from provided selector
        content_elements = await page.query_selector_all("div.field--name-body p")
        content = " ".join([await elem.inner_text() for elem in content_elements]).strip()
        return content
    except Exception as e:
        print(f"Error crawling {article_url}: {str(e)}")
        return ""

async def scrape_and_save_csv(max_pages=200):
    all_news = []
    processed_urls = set()  # Track unique article URLs to avoid duplicates

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set browser-like headers to avoid detection
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        for page_num in range(1, max_pages + 1):
            url = f"https://www.kenyans.co.ke/news?page={page_num - 1}"  # page=0 is first page
            for attempt in range(3):  # Retry up to 3 times
                try:
                    print(f"Navigating to {url} (Page {page_num}/{max_pages})")
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    break
                except PlaywrightTimeoutError as e:
                    print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                    if attempt == 2:
                        print(f"Failed to load {url} after 3 attempts. Moving to next page.")
                        break
                    await page.wait_for_timeout(5000)  # Wait before retrying

            # Extract articles
            news_items = []
            article_elements = await page.query_selector_all("li.news-article-list")
            if not article_elements:
                print(f"No articles found on page {page_num}. Stopping.")
                break

            for article in article_elements:
                try:
                    headline_elem = await article.query_selector("h2.news-title a")
                    url_elem = await article.query_selector("h2.news-title a")
                    time_elem = await article.query_selector("time.datetime")
                    author_elem = await article.query_selector("span.news-author")
                    teaser_elem = await article.query_selector("div.news-teaser")
                    
                    article_url = await url_elem.get_attribute("href") if url_elem else ""
                    if not article_url.startswith("http"):
                        article_url = "https://www.kenyans.co.ke" + article_url
                    if article_url in processed_urls:
                        continue  # Skip duplicates
                    processed_urls.add(article_url)
                    
                    news_item = {
                        "headline": await headline_elem.inner_text() if headline_elem else "",
                        "url": article_url,
                        "published_at": await time_elem.get_attribute("datetime") if time_elem else "",
                        "author": await author_elem.inner_text() if author_elem else "",
                        "teaser": await teaser_elem.inner_text() if teaser_elem else "",
                        "content": ""
                    }
                    news_items.append(news_item)
                except Exception as e:
                    print(f"Error extracting article on page {page_num}: {str(e)}")

            all_news.extend(news_items)
            print(f"Extracted {len(news_items)} articles from page {page_num}. Total: {len(all_news)}")

            # Check for "Next" button
            next_button = await page.query_selector("li.pager__item--next a")
            if not next_button or page_num == max_pages:
                print(f"No 'Next' button or reached max pages at page {page_num}. Stopping.")
                break

            await page.wait_for_timeout(2000)  # Delay to avoid rate limits

        # Extract content for each article
        for news_item in all_news:
            if news_item["url"]:
                news_item["content"] = await extract_article_content(page, news_item["url"])
                print(f"Extracted content for {news_item['headline']}")
                await page.wait_for_timeout(1000)  # Delay to avoid rate limits

        await browser.close()

    # Save to CSV
    if all_news:
        df = pd.DataFrame(all_news)
        df.to_csv("kenyans_news_content.csv", index=False, encoding="utf-8")
        print(f"✅ Saved {len(df)} articles to kenyans_news_content.csv")
    else:
        print("No data found")

# Run the script
if __name__ == "__main__":
    asyncio.run(scrape_and_save_csv(max_pages=200))