from playwright.sync_api import sync_playwright
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)

def scrape_places(search_query: str, total: int = 10):
    """
    Scrape Google Maps for places based on search query
    
    Args:
        search_query: Search term (e.g., "restaurants à Paris")
        total: Number of results to scrape
    
    Returns:
        List of dictionaries containing place information
    """
    places = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to Google Maps
            logging.info(f"Searching for: {search_query}")
            page.goto("https://www.google.com/maps", timeout=60000)
            page.wait_for_timeout(2000)
            
            # Search
            search_box = page.locator('input[id="searchboxinput"]')
            search_box.fill(search_query)
            search_box.press("Enter")
            page.wait_for_timeout(3000)
            
            # Wait for results
            page.wait_for_selector('div[role="feed"]', timeout=10000)
            
            # Scroll to load more results
            scrollable_div = page.locator('div[role="feed"]')
            
            previously_counted = 0
            while len(places) < total:
                # Scroll
                scrollable_div.evaluate("el => el.scrollTop = el.scrollHeight")
                page.wait_for_timeout(2000)
                
                # Get all place elements
                place_elements = page.locator('div[role="feed"] > div > div > a').all()
                
                if len(place_elements) >= total:
                    place_elements = place_elements[:total]
                    break
                
                # Check if we're stuck
                if len(place_elements) == previously_counted:
                    logging.warning(f"No more results found. Got {len(place_elements)} places.")
                    break
                    
                previously_counted = len(place_elements)
                logging.info(f"Found {len(place_elements)} places so far...")
            
            # Extract data from each place
            for i, element in enumerate(place_elements[:total]):
                try:
                    element.click()
                    page.wait_for_timeout(2000)
                    
                    place_data = {
                        "name": "",
                        "address": "",
                        "website": "",
                        "phone_number": "",
                        "reviews_count": None,
                        "reviews_average": None,
                        "place_type": "",
                        "opens_at": "",
                        "introduction": ""
                    }
                    
                    # Name
                    try:
                        name_elem = page.locator('h1').first
                        place_data["name"] = name_elem.inner_text()
                    except:
                        pass
                    
                    # Address
                    try:
                        address_elem = page.locator('button[data-item-id="address"]').first
                        place_data["address"] = address_elem.inner_text()
                    except:
                        pass
                    
                    # Website
                    try:
                        website_elem = page.locator('a[data-item-id="authority"]').first
                        place_data["website"] = website_elem.get_attribute("href")
                    except:
                        pass
                    
                    # Phone
                    try:
                        phone_elem = page.locator('button[data-item-id^="phone:tel:"]').first
                        place_data["phone_number"] = phone_elem.inner_text()
                    except:
                        pass
                    
                    # Reviews
                    try:
                        reviews_elem = page.locator('div.F7nice').first
                        reviews_text = reviews_elem.inner_text()
                        parts = reviews_text.split()
                        if len(parts) >= 2:
                            place_data["reviews_average"] = float(parts[0].replace(',', '.'))
                            place_data["reviews_count"] = int(parts[1].replace('(', '').replace(')', '').replace(',', ''))
                    except:
                        pass
                    
                    # Type
                    try:
                        type_elem = page.locator('button[jsaction*="category"]').first
                        place_data["place_type"] = type_elem.inner_text()
                    except:
                        pass
                    
                    places.append(place_data)
                    logging.info(f"Scraped {i+1}/{total}: {place_data['name']}")
                    
                except Exception as e:
                    logging.error(f"Error scraping place {i+1}: {str(e)}")
                    continue
            
        except Exception as e:
            logging.error(f"Error during scraping: {str(e)}")
        finally:
            browser.close()
    
    return places

def save_places_to_csv(places: list, filename: str, append: bool = False):
    """Save places data to CSV file"""
    df = pd.DataFrame(places)
    
    if append and pd.io.common.file_exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)
    
    logging.info(f"Saved {len(places)} places to {filename}")
