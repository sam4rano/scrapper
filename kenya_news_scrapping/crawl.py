import asyncio
import json
import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_crypto_prices():
    schema = {
    "name": "Top Stories",
    "baseSelector": "div.topstory.featuredstory",  # main repeating container
    "fields": [
        {
            "name": "title",
            "selector": "h1 > a",
            "type": "text"
        },

        {
            "name": "published",
            "selector": "span.timepublished",
            "type": "text"
        },
        
        {
            "name": "description",
            "selector": "p",
            "type": "text"
        }
    ]
}

    # 1. Define a simple extraction schema
    # schema = {
    #     "name": "Cry",
    #     "baseSelector": "div.topstory-excerpt",    # Repeated elements
    #     "fields": [
    #          {
    #             "name": "title",
    #             "selector": "next-topstory-tags p",
    #             "type": "text"
    #         },
    #           {
    #             "name": "time",
    #             "selector": "div.timepublished",
    #             "type": "text"
    #         },
             
    #         {
    #             "name": "sentences",
    #             "selector": "topstory-excerpt p",
    #             "type": "text"
    #         },
    #         {
    #             "name": "price",
    #             "selector": "next-topstory-tags h1 a",
    #             "type": "text"
    #         }
    #     ]
    # }



    # 2. Create the extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    # 3. Set up your crawler config (if needed)
    config = CrawlerRunConfig(
        # e.g., pass js_code or wait_for if the page is dynamic
        # wait_for="css:.crypto-row:nth-child(20)"
        cache_mode = CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        # 4. Run the crawl and extraction
        result = await crawler.arun(
            url="https://www.citizen.digital",

            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        # 5. Parse the extracted JSON
        data = json.loads(result.extracted_content)
        if data:
            df = pd.DataFrame(data)
            df.to_csv("news.csv", index=False)
            print("✅ Saved news with", len(df), "entries")
        else:
            print("No data found")
            print(json.dumps(data[0], indent=2) if data else "No data found")
            print(f"Extracted {len(data)} coin entries")

asyncio.run(extract_crypto_prices()) 