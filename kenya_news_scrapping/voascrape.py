import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import nest_asyncio

nest_asyncio.apply()

async def extract_article_description(page, article_url):
    try:
        await page.goto(article_url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
        # Extract description from article page
        description_elements = await page.query_selector_all("div.intro.m-t-md p")
        description = " ".join([await elem.inner_text() for elem in description_elements]).strip()
        return description
    except Exception as e:
        print(f"Error crawling {article_url}: {str(e)}")
        return ""

async def scrape_and_save_csv(max_clicks=30):
    all_news = []
    processed_ids = set()  # Track unique article IDs to avoid duplicates

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set browser-like headers to avoid detection
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        # Navigate to the news page with retry logic
        url = "https://www.voaafrica.com/z/7605"
        for attempt in range(3):
            try:
                print(f"Navigating to {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                break
            except PlaywrightTimeoutError as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    print(f"Failed to load {url} after 3 attempts. Exiting.")
                    await browser.close()
                    return
                await page.wait_for_timeout(5000)

        async def extract_news():
            news_items = []
            # Extract articles
            article_elements = await page.query_selector_all("div.news__item.news__item--unopenable.accordeon__item")
            for article in article_elements:
                try:
                    article_id = await article.get_attribute("data-article-id")  # Unique ID
                    if article_id in processed_ids:
                        continue  # Skip duplicates
                    processed_ids.add(article_id)
                    
                    date_elem = await article.query_selector("time[pubdate='pubdate']")
                    title_elem = await article.query_selector("h1.title.pg-title.pg-title--immovable")
                    url_elem = await article.query_selector("a.js-media-title-link")
                    
                    article_url = await url_elem.get_attribute("href") if url_elem else ""
                    if not article_url.startswith("http"):
                        article_url = "https://www.voaafrica.com" + article_url
                    
                    news_item = {
                        "date": await date_elem.get_attribute("datetime") if date_elem else "",
                        "title": await title_elem.inner_text() if title_elem else "",
                        "description": "",
                        "url": article_url
                    }
                    news_items.append(news_item)
                except Exception as e:
                    print(f"Error extracting article: {str(e)}")
            return news_items

        # Extract initial articles
        all_news.extend(await extract_news())
        print(f"Extracted {len(all_news)} initial articles")

        # Simulate clicking "Load more" button
        for i in range(max_clicks):
            try:
                load_more_button = await page.query_selector("a.btn.link-showMore.btn__text")
                if not load_more_button:
                    print(f"No 'Load more' button found on click {i+1}. Stopping.")
                    break
                
                await load_more_button.click()
                # Wait for new articles to load
                await page.wait_for_selector("div.news__item.news__item--unopenable.accordeon__item", timeout=10000)
                await page.wait_for_timeout(3000)  # Ensure stability
                print(f"Clicked 'Load more' button {i+1}/{max_clicks}")
                
                # Extract new articles
                new_stories = await extract_news()
                all_news.extend(new_stories)
                print(f"Total articles after click {i+1}: {len(all_news)}")
            except Exception as e:
                print(f"Error clicking 'Load more' button: {str(e)}")
                break

        # Extract description for each article
        for news_item in all_news:
            if news_item["url"]:
                news_item["description"] = await extract_article_description(page, news_item["url"])
                print(f"Extracted description for {news_item['title']}")
                await page.wait_for_timeout(1000)  # Avoid rate limits

        await browser.close()

    # Save to CSV
    if all_news:
        df = pd.DataFrame(all_news)
        df.to_csv("voa_africa_news.csv", index=False, encoding="utf-8")
        print(f"✅ Saved {len(df)} articles to voa_africa_news.csv")
    else:
        print("No data found")

# Run the script
if __name__ == "__main__":
    asyncio.run(scrape_and_save_csv(max_clicks=30))