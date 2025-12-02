import asyncio
from playwright.async_api import async_playwright


async def scrape_menu_images(google_maps_url: str) -> list[str]:
    """
    Scrapes all menu image URLs from a Google Maps place listing.
    
    Args:
        google_maps_url: The Google Maps URL for the place
        
    Returns:
        List of image URLs from the menu section
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Set a realistic user agent
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to: {google_maps_url}")
            # Use 'load' instead of 'networkidle' - Google Maps has continuous network activity
            await page.goto(google_maps_url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(5000)  # Wait for page to fully load
            
            # Handle potential cookie/popup dialogs
            try:
                # Try to dismiss any cookie consent or popups
                accept_button = page.locator('button:has-text("Accept"), button:has-text("I agree"), [aria-label*="Accept"], [aria-label*="Dismiss"]').first
                if await accept_button.is_visible(timeout=2000):
                    await accept_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass  # No popup found, continue
            
            # Click the "Menu" tab - try multiple selectors
            print("Looking for Menu tab...")
            menu_tab = None
            
            # Try different selectors for the Menu tab
            selectors = [
                ('role', 'tab', {'name': 'Menu'}),
                ('text', 'Menu'),
                ('css', 'button[data-value="Menu"]'),
                ('css', '[role="tab"]:has-text("Menu")'),
            ]
            
            for selector_type, selector, *kwargs in selectors:
                try:
                    if selector_type == 'role':
                        menu_tab = page.get_by_role(selector, **kwargs[0] if kwargs else {})
                    elif selector_type == 'text':
                        menu_tab = page.get_by_text(selector)
                    elif selector_type == 'css':
                        menu_tab = page.locator(selector)
                    
                    if await menu_tab.is_visible(timeout=3000):
                        print(f"Found Menu tab using {selector_type} selector")
                        break
                except:
                    continue
            
            if not menu_tab or not await menu_tab.is_visible(timeout=2000):
                # Debug: take a screenshot to see what's on the page
                await page.screenshot(path="debug_screenshot.png")
                print("⚠️  Menu tab not found. Saved debug_screenshot.png for inspection.")
                print("Trying to find all tabs on the page...")
                all_tabs = await page.evaluate("""
                    () => {
                        const tabs = Array.from(document.querySelectorAll('[role="tab"], button[data-value]'));
                        return tabs.map(t => ({
                            text: t.textContent?.trim(),
                            dataValue: t.getAttribute('data-value'),
                            ariaLabel: t.getAttribute('aria-label')
                        }));
                    }
                """)
                print(f"Found tabs: {all_tabs}")
                await browser.close()
                return []
            
            await menu_tab.click()
            print("Clicked Menu tab")
            await page.wait_for_timeout(4000)  # Wait for menu content to load
            
            # Scroll to load all menu images
            print("Scrolling to load all menu images...")
            last_height = 0
            unchanged_count = 0
            max_scrolls = 20  # Safety limit
            
            for scroll_attempt in range(max_scrolls):
                # Get current scroll height
                current_height = await page.evaluate("document.scrollingElement.scrollHeight")
                
                # Scroll down
                await page.evaluate("window.scrollTo(0, document.scrollingElement.scrollHeight)")
                await page.wait_for_timeout(1500)  # Wait for images to load
                
                # Check if we've reached the bottom
                new_height = await page.evaluate("document.scrollingElement.scrollHeight")
                if new_height == last_height:
                    unchanged_count += 1
                    if unchanged_count >= 2:
                        break
                else:
                    unchanged_count = 0
                    last_height = new_height
                
                # Also scroll within the menu section if there are horizontal scrolls
                menu_section = page.locator('[data-value="Menu"]').locator('..')
                if await menu_section.count() > 0:
                    await menu_section.first().evaluate("element => element.scrollLeft = element.scrollWidth")
            
            print("Extracting image URLs...")
            # Extract all image URLs
            image_urls = await page.evaluate("""
                () => {
                    const images = Array.from(document.querySelectorAll('img'));
                    return images.map(img => img.src || img.currentSrc || img.getAttribute('data-src'))
                        .filter(url => url && url.startsWith('http'));
                }
            """)
            
            # Filter to Google-hosted images (menu photos are typically from googleusercontent.com)
            menu_images = [
                url for url in image_urls
                if "googleusercontent.com" in url or "googleapis.com" in url
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_images = []
            for url in menu_images:
                if url not in seen:
                    seen.add(url)
                    unique_images.append(url)
            
            print(f"✅ Found {len(unique_images)} unique menu image URLs")
            await browser.close()
            return unique_images
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await browser.close()
            raise


async def main():
    import sys
    
    # Get URL from command line argument or use default test URL
    if len(sys.argv) > 1:
        google_maps_url = sys.argv[1]
    else:
        # Default test URL
        google_maps_url = "https://www.google.com/maps/place/CAVA/@33.5087058,-112.0458579,17z/data=!3m1!4b1!4m6!3m5!1s0x872b0dc8ef74aa11:0x4f3ccce4e3eb8f6e!8m2!3d33.5087058!4d-112.0458579!16s%2Fg%2F11rq8nl6lt?entry=ttu&g_ep=EgoyMDI1MTEyMy4xIKXMDSoASAFQAw%3D%3D"
        print("Usage: python scrape_menu.py <google_maps_url>")
        print("Using default test URL...\n")
    
    print("=" * 80)
    print("Google Maps Menu Scraper")
    print("=" * 80)
    
    urls = await scrape_menu_images(google_maps_url)
    
    print("\n" + "=" * 80)
    print(f"Results: Found {len(urls)} menu image URLs")
    print("=" * 80)
    
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")
    
    if len(urls) == 0:
        print("\n⚠️  No menu images found. Possible reasons:")
        print("   - The place doesn't have a Menu tab")
        print("   - The menu section has no images")
        print("   - The page structure may have changed")
    
    return urls


if __name__ == "__main__":
    asyncio.run(main())

