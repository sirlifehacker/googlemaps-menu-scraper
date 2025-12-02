import asyncio
from typing import List
from playwright.async_api import async_playwright

async def _collect_menu_images(place_url: str) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # 1. Go to the place page
            # Use domcontentloaded instead of networkidle for faster loading
            await page.goto(place_url, wait_until="domcontentloaded", timeout=60000)
            # Wait a bit for dynamic content to load
            await page.wait_for_timeout(3000)

            # 2. Click the "Menu" tab if it exists
            # Playwright text selector is resilient to minor DOM changes
            menu_tab = page.get_by_role("tab", name="Menu")
            if not await menu_tab.is_visible():
                # Some listings may not have a dedicated Menu tab
                await browser.close()
                return []

            await menu_tab.click()
            await page.wait_for_timeout(3000)  # let images load

            # 3. Scroll to load all menu photos
            last_height = 0
            unchanged_rounds = 0

            while True:
                height = await page.evaluate("document.scrollingElement.scrollHeight")
                if height == last_height:
                    unchanged_rounds += 1
                else:
                    unchanged_rounds = 0
                    last_height = height

                # Once height hasn't changed for a couple of iterations, assume we're done
                if unchanged_rounds >= 2:
                    break

                await page.mouse.wheel(0, height)
                await page.wait_for_timeout(1200)

            # 4. Grab all img srcs – filter to Google-hosted photos
            image_urls = await page.eval_on_selector_all(
                "img",
                "imgs => imgs.map(img => img.src || img.currentSrc).filter(Boolean)"
            )

            # Often menu photos are Googleusercontent domain
            image_urls = [
                u for u in image_urls
                if "googleusercontent.com" in u
            ]

            # De-duplicate while preserving order
            seen = set()
            unique_urls = []
            for u in image_urls:
                if u not in seen:
                    seen.add(u)
                    unique_urls.append(u)

            await browser.close()
            return unique_urls

        except Exception:
            await browser.close()
            raise

async def test():
    # The URL provided is a search URL - let's convert it to a direct place URL
    # Search URL: https://www.google.com/maps/search/?api=1&query=CAVA&query_place_id=ChIJEap078gNK4cRbo_r4-TMPE8
    # Place URL format: https://www.google.com/maps/place/?place_id=...
    
    place_id = "ChIJEap078gNK4cRbo_r4-TMPE8"
    # Try the standard place URL format
    place_url = f"https://www.google.com/maps/place/?place_id={place_id}"
    
    # Also try with the query parameter format
    place_url_alt = f"https://www.google.com/maps/search/?api=1&query_place_id={place_id}"
    
    print("=" * 80)
    print("Testing with PLACE URL format (recommended):")
    print(f"URL: {place_url}")
    print("Starting scrape...")
    
    try:
        urls = await _collect_menu_images(place_url)
        print(f"\n✅ Found {len(urls)} menu image URLs:")
        for i, url in enumerate(urls[:5], 1):  # Show first 5
            print(f"  {i}. {url}")
        if len(urls) > 5:
            print(f"  ... and {len(urls) - 5} more")
        
        if len(urls) == 0:
            print("\n⚠️  No menu images found with place URL. Trying alternative format...")
            print("\n" + "=" * 80)
            print("Testing with ALTERNATIVE URL format:")
            print(f"URL: {place_url_alt}")
            urls = await _collect_menu_images(place_url_alt)
            print(f"\n✅ Found {len(urls)} menu image URLs:")
            for i, url in enumerate(urls[:5], 1):
                print(f"  {i}. {url}")
            if len(urls) > 5:
                print(f"  ... and {len(urls) - 5} more")
            
            if len(urls) == 0:
                print("\n⚠️  No menu images found. This could mean:")
                print("   - The place doesn't have a Menu tab")
                print("   - The page structure has changed")
                print("   - The URL format needs adjustment")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

