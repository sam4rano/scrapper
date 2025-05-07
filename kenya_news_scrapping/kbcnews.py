import asyncio
import csv
import pandas as pd
from playwright.async_api import async_playwright
import nest_asyncio

nest_asyncio.apply()

async def extract_article_content(page, article_url):
    try:
        await page.goto(article_url, wait_until="domcontentloaded")
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
        
        # Navigate to the main page
        await page.goto("https://www.kbc.co.ke/category/news/local-news/", wait_until="domcontentloaded")

        async def extract_news():
            news_items = []
            # Extract categories and articles
            category_elements = await page.query_selector_all("div.elementor-element-84706cc.e-flex.e-con-boxed.e-con.e-parent")
            for category in category_elements:
                try:
                    cat_name_elem = await category.query_selector("h2.heading-title a.h-link")
                    cat_name = await cat_name_elem.inner_text() if cat_name_elem else ""
                    
                    article_elements = await category.query_selector_all("div.p-wrap")
                    for article in article_elements:
                        headline_elem = await article.query_selector("h2.entry-title a.p-url")
                        url_elem = await article.query_selector("h2.entry-title a.p-url")
                        time_elem = await article.query_selector("time.updated")
                        tags_elems = await article.query_selector_all("div.p-categories a.p-category")
                        desc_elem = await article.query_selector("div.p-content > p")
                        
                        tags = [await tag.inner_text() for tag in tags_elems] if tags_elems else []
                        news_item = {
                            "category": cat_name,
                            "headline": await headline_elem.inner_text() if headline_elem else "",
                            "url": await url_elem.get_attribute("href") if url_elem else "",
                            "published_at": await time_elem.get_attribute("datetime") if time_elem else "",
                            "tags": ",".join(tags),
                            "description": await desc_elem.inner_text() if desc_elem else "",
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
                # Wait for new content to load
                await page.wait_for_timeout(3000)  # Adjust timeout as needed
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

        await browser.close()

    # Save to CSV
    if all_news:
        df = pd.DataFrame(all_news)
        df.to_csv("kbc_news_with_content.csv", index=False, encoding="utf-8")
        print(f"✅ Saved {len(df)} articles to kbc_news_with_content.csv")
    else:
        print("No data found")

# Run the script
if __name__ == "__main__":
    asyncio.run(scrape_and_save_csv(max_clicks=15))