import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import nest_asyncio

nest_asyncio.apply()

async def extract_article_content(page, article_url):
    try:
        await page.goto(article_url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
        # Extract article content
        content_elements = await page.query_selector_all("div.entry-content.rbct.clearfix p")
        content = " ".join([await elem.inner_text() for elem in content_elements]).strip()
        return content
    except Exception as e:
        print(f"Error crawling {article_url}: {str(e)}")
        return ""

async def scrape_and_save_csv(max_clicks=15):
    all_news = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Set browser-like headers to avoid detection
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        # Navigate to the local news page with retry logic
        url = "https://www.kbc.co.ke/category/entertainment/"
        for attempt in range(3):  # Retry up to 3 times
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
                break
            except PlaywrightTimeoutError as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    print(f"Failed to load {url} after 3 attempts. Exiting.")
                    await browser.close()
                    return
                await page.wait_for_timeout(5000)  # Wait before retrying

        async def extract_news():
            news_items = []
            # Extract articles from the new container
            article_elements = await page.query_selector_all("div.block-inner div.p-wrap.p-grid.p-grid-2")
            for article in article_elements:
                try:
                    headline_elem = await article.query_selector("h2.entry-title a.p-url")
                    url_elem = await article.query_selector("h2.entry-title a.p-url")
                    time_elem = await article.query_selector("time.updated")
                    tags_elems = await article.query_selector_all("div.p-categories.p-top a.p-category")
                    
                    tags = [await tag.inner_text() for tag in tags_elems] if tags_elems else []
                    news_item = {
                        "headline": await headline_elem.inner_text() if headline_elem else "",
                        "url": await url_elem.get_attribute("href") if url_elem else "",
                        "published_at": await time_elem.get_attribute("datetime") if time_elem else "",
                        "tags": ",".join(tags),
                        "content": ""
                    }
                    news_items.append(news_item)
                except Exception as e:
                    print(f"Error extracting article: {str(e)}")
            return news_items

        # Extract initial stories
        all_news.extend(await extract_news())
        print(f"Extracted {len(all_news)} initial articles")

        # Simulate clicking "Show More" button
        for i in range(max_clicks):
            try:
                more_button = await page.query_selector("a.loadmore-trigger")
                if not more_button:
                    print(f"No 'Show More' button found on click {i+1}")
                    break
                
                await more_button.click()
                # Wait for new content to load and ensure articles appear
                await page.wait_for_selector("div.p-wrap.p-grid.p-grid-2", timeout=10000)
                await page.wait_for_timeout(3000)  # Additional wait for stability
                print(f"Clicked 'Show More' button {i+1}/{max_clicks}")
                
                # Extract new stories
                new_stories = await extract_news()
                all_news.extend(new_stories)
                print(f"Total articles after click {i+1}: {len(all_news)}")
            except Exception as e:
                print(f"Error clicking 'Show More' button: {str(e)}")
                break

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
        df.to_csv("kbc_entertainment_news_content.csv", index=False, encoding="utf-8")
        print(f"✅ Saved {len(df)} articles to kbc_local_news_with_content.csv")
    else:
        print("No data found")

# Run the script
if __name__ == "__main__":
    asyncio.run(scrape_and_save_csv(max_clicks=15))