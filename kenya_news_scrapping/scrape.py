import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import pandas as pd
from aiohttp import ClientSession
import nest_asyncio
import aiohttp
nest_asyncio.apply()

async def extract_citizen_top_stories():
    schema = {
        "name": "Citizen Top Stories",
        "baseSelector": ".featuredstory div[data-v-e95ea058]",
        "fields": [
            {
                "name": "category",
                "selector": ".next-topstory-tags span[data-v-e95ea058]",
                "type": "text",
            },
            {
                "name": "time",
                "selector": ".timepublished [data-v-e95ea058]",
                "type": "text",
            },
            {
                "name": "headline",
                "selector": "h1 > a[data-v-e95ea058]",
                "type": "text",
            },
            {
                "name": "description",
                "selector": "p[data-v-e95ea058]",
                "type": "text",
            },
           
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    
    config = CrawlerRunConfig(
        cache_mode = CacheMode.BYPASS,
        extBraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
         result = await crawler.arun(
            url="https://www.citizen.digital",

            config=config
        )
         if not result.success:
            print("Crawl failed:", result.error_message)
            return
        
    data = json.loads(result.extracted_content)
    if data:
        df = pd.DataFrame(data)
        df.to_csv("news.csv", index=False)
        print("✅ Saved news with", len(df), "entries")
    else:
        print("No data found")
        print(json.dumps(data[0], indent=2) if data else "No data found")
        print(f"Extracted {len(data)} coin entries")

asyncio.run(extract_citizen_top_stories())
