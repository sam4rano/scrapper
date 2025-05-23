import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import nest_asyncio

nest_asyncio.apply()

async def extract_article_content(page, article_url):
    """Extract all <p> tags from the <div class='entry'> on an article page."""
    for attempt in range(3):  # Retry up to 3 times
        try:
            await page.goto(article_url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
            # Wait for the entry div to ensure content is loaded
            await page.wait_for_selector("div.entry", timeout=10000)
            
            # Find the entry div
            entry_div = await page.query_selector("div.entry")
            if not entry_div:
                return "Entry div not found"
            
            # Find all <p> tags within the entry div
            p_tags = await entry_div.query_selector_all("p")
            if not p_tags:
                return "No <p> tags found"
            
            # Extract text from all <p> tags and join them
            p_contents = [await p.inner_text() for p in p_tags]
            return " ".join([content.strip() for content in p_contents if content.strip()])
        
        except PlaywrightTimeoutError as e:
            print(f"Attempt {attempt + 1} failed for {article_url}: {str(e)}")
            if attempt == 2:
                return f"Failed to load {article_url} after 3 attempts"
            await page.wait_for_timeout(5000)  # Wait before retrying
        except Exception as e:
            print(f"Error crawling {article_url}: {str(e)}")
            return f"Error extracting content: {str(e)}"

async def scrape_and_save_csv(start_page=1, end_page=70):
    """C  Crawl Global Voices Kenya pages and save data to CSV."""
    all_articles = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        )
        page = await context.new_page()

        # Iterate through pages 1 to 70
        for page_num in range(start_page, end_page + 1):
            url = f"https://globalvoices.org/-/world/sub-saharan-africa/kenya/page/{page_num}/"
            print(f"Crawling page {page_num}: {url}")
            
            for attempt in range(3):  # Retry up to 3 times
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)  # 60s timeout
                    # Wait for articles to load
                    await page.wait_for_selector("div.gv-promo-card-container", timeout=10000)
                    break
                except PlaywrightTimeoutError as e:
                    print(f"Attempt {attempt + 1} failed for page {page_num}: {str(e)}")
                    if attempt == 2:
                        print(f"Failed to load page {page_num} after 3 attempts. Skipping.")
                        break
                    await page.wait_for_timeout(5000)  # Wait before retrying
            
            try:
                # Extract articles from the listing page
                article_elements = await page.query_selector_all("div.gv-promo-card-container")
                if not article_elements:
                    print(f"No articles found on page {page_num}")
                    continue
                
                for article in article_elements:
                    try:
                        # Extract title and URL
                        title_elem = await article.query_selector("h3.post-title a")
                        title = await title_elem.inner_text() if title_elem else "N/A"
                        article_url = await title_elem.get_attribute("href") if title_elem else "N/A"
                        
                        # Extract tagline
                        tagline_elem = await article.query_selector("div.postmeta.post-tagline")
                        tagline = await tagline_elem.inner_text() if tagline_elem else "N/A"
                        
                        # Extract author
                        author_elem = await article.query_selector("span.credit-label + a.user-link")
                        author = await author_elem.inner_text() if author_elem else "N/A"
                        
                        # Extract date
                        date_elem = await article.query_selector("span.datestamp")
                        date = await date_elem.inner_text() if date_elem else "N/A"
                        
                        # Extract all <p> tags from the article page
                        article_content = await extract_article_content(page, article_url) if article_url != "N/A" else "N/A"
                        
                        # Store article data
                        all_articles.append({
                            "Page": page_num,
                            "Title": title,
                            "URL": article_url,
                            "Tagline": tagline,
                            "Author": author,
                            "Date": date,
                            "Article Content": article_content
                        })
                        
                        print(f"Extracted article: {title}")
                        await page.wait_for_timeout(1000)  # Delay to avoid rate limits
                        
                    except Exception as e:
                        print(f"Error extracting article on page {page_num}: {str(e)}")
                        continue
                
                # Delay to avoid overloading the server
                await page.wait_for_timeout(2000)  # 2-second delay
                
            except Exception as e:
                print(f"Error crawling page {page_num}: {str(e)}")
                continue

        await browser.close()

    # Save to CSV
    if all_articles:
        df = pd.DataFrame(all_articles)
        df.to_csv("globalvoices_kenya_articles.csv", index=False, encoding="utf-8")
        print(f"✅ Saved {len(df)} articles to globalvoices_kenya_articles.csv")
    else:
        print("No data found")

# Run the script
if __name__ == "__main__":
    asyncio.run(scrape_and_save_csv(start_page=1, end_page=70))