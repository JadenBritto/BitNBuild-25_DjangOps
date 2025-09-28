import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
from urllib.parse import urlparse
import logging

class ReviewScraper:
    def __init__(self, max_reviews=20):
        """
        Initialize the scraper with a maximum number of reviews to collect.
        
        Args:
            max_reviews (int): Maximum number of reviews to scrape (default: 30)
        """
        self.max_reviews = max_reviews
        self.logger = logging.getLogger(__name__)
        self.setup_driver()
    
    def setup_driver(self):
        chrome_options = Options()
        # Performance optimizations
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-gpu-sandbox')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')  # Suppress console messages
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Reduce resource usage
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Set timeouts
        chrome_options.add_argument('--page-load-strategy=eager')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Set shorter timeouts for faster operation
            self.driver.set_page_load_timeout(12)  # Further reduced for performance
            self.driver.implicitly_wait(2)  # Reduced for faster element searches
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Chrome driver not found: {e}")
            self.driver = None
    
    def identify_site(self, url):
        domain = urlparse(url).netloc.lower()
        
        if 'amazon' in domain:
            return 'amazon'
        elif 'flipkart' in domain:
            return 'flipkart'
        elif 'ebay' in domain:
            return 'ebay'
        else:
            return 'generic'
    
    def scrape_amazon_reviews(self, url):
        reviews = []
        product_name = ""
        
        try:
            # Get product ASIN from URL
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if not asin_match:
                asin_match = re.search(r'/product/([A-Z0-9]{10})', url)
            
            if asin_match:
                asin = asin_match.group(1)
                print(f"Scraping amazon reviews (max: {self.max_reviews})")
                
                # Extract the original domain to preserve regional Amazon sites
                parsed_url = urlparse(url)
                base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # Optimized URL order - product page first (most reliable based on logs)
                review_urls = [
                    f"{base_domain}/dp/{asin}",  # Most successful from logs
                    f"{base_domain}/product-reviews/{asin}",
                    f"{base_domain}/gp/product/{asin}"
                ]
                
                for i, review_url in enumerate(review_urls):
                    try:
                        print(f"Trying URL {i+1}/{len(review_urls)}: {review_url}")
                        self.driver.get(review_url)
                        time.sleep(2)  # Reduced wait time
                        
                        # Check if we're blocked or redirected
                        current_url = self.driver.current_url
                        if 'captcha' in current_url.lower() or 'robot' in current_url.lower():
                            print("Detected captcha/robot check, trying next URL")
                            continue
                        
                        # Try multiple selectors for product name
                        product_name_selectors = [
                            "[data-hook='product-link']",
                            "a[data-hook='product-link']",
                            ".cr-product-link",
                            "h1.product-title",
                            ".product-title",
                            "#productTitle",
                            "h1.a-size-large"
                        ]
                        
                        for selector in product_name_selectors:
                            try:
                                product_element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                product_name = product_element.text.strip()
                                if product_name:
                                    print(f"Found product name: {product_name[:50]}...")
                                    break
                            except TimeoutException:
                                continue
                        
                        if not product_name:
                            product_name = "Amazon Product"
                        
                        # Extract reviews from current page
                        reviews = self.extract_amazon_reviews_from_page()
                        
                        if reviews:
                            print(f"Found {len(reviews)} reviews on page")
                            # If we have fewer reviews than desired, try to get more
                            if len(reviews) < self.max_reviews:
                                self.load_more_amazon_reviews(reviews)
                            break
                        else:
                            print("No reviews found, trying next URL")
                            
                    except Exception as e:
                        print(f"Error with URL {review_url}: {e}")
                        continue
                
                # If still no reviews found, that's OK - some products may not have reviews
                        
        except Exception as e:
            print(f"Error scraping Amazon reviews: {e}")
        
        final_reviews = reviews[:self.max_reviews]
        print(f"Scraped {len(final_reviews)} Amazon reviews")
        return final_reviews, product_name
    
    def extract_amazon_reviews_from_page(self):
        """Extract reviews from the current Amazon page"""
        reviews = []
        
        try:
            # Wait for reviews to load with comprehensive selectors
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-hook='review'], .review, .cr-original-review-item, .a-section.review, div[data-hook='review']"))
            )
        except TimeoutException:
            print("Timed out waiting for reviews to load")
            # Try scrolling to load reviews
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                # Try one more time after scroll
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-hook='review'], .review, .cr-original-review-item"))
                )
            except TimeoutException:
                print("Still no reviews found after scrolling")
                return reviews
        
        # Optimized selectors - including Amazon India specific ones
        review_selectors = [
            "[data-hook='review']",  # Most successful from logs
            ".cr-original-review-item",
            "div[data-hook='review']",  # Amazon India variant
            ".review",
            ".a-section.review",  # Amazon India specific
            "[data-testid='reviews-section'] .review",  # New Amazon layout
            "div.review-item",  # Alternative pattern
            ".celwidget[data-cel-widget*='review']"
        ]
        
        review_elements = []
        for selector in review_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    # Limit to max_reviews + 5 to avoid processing too many elements
                    review_elements = elements[:self.max_reviews + 5]
                    print(f"Found {len(elements)} review elements, processing first {len(review_elements)} with selector: {selector}")
                    break
            except Exception as e:
                continue
        
        if not review_elements:
            print("No review elements found with any selector")
            # Debug: Print page title and some content to understand what we're seeing
            try:
                page_title = self.driver.title
                print(f"Page title: {page_title}")
                
                # Check if we're on a product page or review page
                if "Amazon" in page_title:
                    # Try to find any text that might indicate reviews
                    review_hints = self.driver.find_elements(By.CSS_SELECTOR, "*[class*='review'], *[data-hook*='review'], *[id*='review']")
                    if review_hints:
                        print(f"Found {len(review_hints)} elements with 'review' in attributes")
                    else:
                        print("No elements with 'review' found in page")
                        
                    # Check if page is fully loaded
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text[:200]
                    print(f"Page content preview: {body_text}...")
            except Exception as e:
                print(f"Debug error: {e}")
            
            return reviews
        
        for element in review_elements:
            if len(reviews) >= self.max_reviews:
                break
                
            try:
                # Optimized selectors - including Amazon India variants
                text_selectors = [
                    "[data-hook='review-body'] span",
                    "[data-hook='review-body']",
                    ".review-text",
                    ".cr-original-review-text",  # Amazon India specific
                    "span[data-hook='review-body']",  # Alternative structure
                    ".reviewText",  # Older Amazon format
                    ".a-size-base.review-text.review-text-content span"
                ]
                
                text = ""
                for text_selector in text_selectors:
                    try:
                        text_elements = element.find_elements(By.CSS_SELECTOR, text_selector)
                        if text_elements:
                            text = " ".join([elem.text.strip() for elem in text_elements[:3] if elem.text.strip()])  # Limit to first 3 elements
                            if text and len(text) > 15:  # Slightly higher minimum
                                break
                    except Exception:
                        continue
                
                # Improved rating extraction for all Amazon variants
                rating = 0
                rating_selectors = [
                    "[data-hook='review-star-rating'] .a-icon-alt",
                    ".review-rating .a-icon-alt",
                    ".a-icon-alt",
                    "[data-hook='review-star-rating']",
                    ".cr-original-review-rating .a-icon-alt"  # Amazon India
                ]
                
                for rating_selector in rating_selectors:
                    try:
                        rating_element = element.find_element(By.CSS_SELECTOR, rating_selector)
                        rating_text = rating_element.get_attribute('innerHTML') or rating_element.text or rating_element.get_attribute('title') or ""
                        
                        # Quick extraction - look for number before 'out of'
                        rating_match = re.search(r'(\d+(?:\.\d+)?)\s*out\s*of', rating_text, re.IGNORECASE)
                        if rating_match:
                            rating = min(5, max(1, int(float(rating_match.group(1)))))
                            break
                        
                        # Alternative patterns for different regions
                        rating_patterns = [
                            r'a-star-(\d+)',  # class name like "a-star-4"
                            r'(\d+)\s*star',  # "4 stars"
                            r'(\d+)'  # any digit
                        ]
                        
                        for pattern in rating_patterns:
                            rating_match = re.search(pattern, rating_text, re.IGNORECASE)
                            if rating_match:
                                rating = min(5, max(1, int(float(rating_match.group(1)))))
                                break
                        
                        if rating > 0:
                            break
                    except Exception:
                        continue
                
                if rating == 0:
                    rating = 3  # Default neutral rating if extraction fails
                
                if text and len(text) > 10:
                    reviews.append({
                        'text': text,
                        'rating': rating
                    })
                    
            except Exception as e:
                print(f"Error extracting individual review: {e}")
                continue
        
        return reviews
    
    def load_more_amazon_reviews(self, reviews):
        """Try to load more reviews - simplified approach to avoid bot detection"""
        if len(reviews) >= self.max_reviews:
            return
            
        print("Attempting to load more reviews without pagination...")
        
        try:
            # Try to click "See all reviews" button instead of pagination
            see_all_selectors = [
                "a[data-hook='see-all-reviews-link-foot']",
                "a[data-hook='see-all-reviews-link']", 
                "a.cr-lighthouse-terms",
                "a:contains('See all reviews')",
                "[data-hook='reviews-medley-footer'] a"
            ]
            
            for selector in see_all_selectors:
                try:
                    see_all_button = WebDriverWait(self.driver, 2).until(  # Reduced timeout
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if see_all_button:
                        print(f"Found 'See all reviews' button with selector: {selector}")
                        self.driver.execute_script("arguments[0].click();", see_all_button)
                        time.sleep(2)  # Reduced wait time
                        
                        # Extract additional reviews from the full reviews page
                        new_reviews = self.extract_amazon_reviews_from_page()
                        if new_reviews and len(new_reviews) > len(reviews):
                            reviews.extend(new_reviews[len(reviews):])  # Add only new reviews
                            print(f"Added {len(new_reviews) - len(reviews)} new reviews from full reviews page")
                        return
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Quick scroll attempt if we have very few reviews
            if len(reviews) < 5:
                print("Trying quick scroll for more reviews...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                new_reviews = self.extract_amazon_reviews_from_page()
                if len(new_reviews) > len(reviews):
                    reviews.clear()
                    reviews.extend(new_reviews[:self.max_reviews])
                    print(f"Found {len(new_reviews)} total reviews after scrolling")
            
        except Exception as e:
            print(f"Error trying to load more reviews: {e}")
            # Don't fail completely, just return what we have
    
    def scrape_flipkart_reviews(self, url):
        reviews = []
        product_name = ""
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Get product name with multiple selectors
            product_name_selectors = [
                "span.B_NuCI",
                ".product-title",
                "h1",
                ".pdp-product-name"
            ]
            
            for selector in product_name_selectors:
                try:
                    product_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    product_name = product_element.text.strip()
                    if product_name:
                        break
                except:
                    continue
            
            if not product_name:
                product_name = "Flipkart Product"
            
            # Find reviews section and load more reviews
            current_page = 1
            max_pages = min(5, (self.max_reviews // 10) + 1)
            
            while len(reviews) < self.max_reviews and current_page <= max_pages:
                try:
                    # Multiple selectors for reviews section
                    review_section_selectors = [
                        "div._16PBlm",
                        ".reviews-section",
                        ".review-container"
                    ]
                    
                    reviews_section = None
                    for selector in review_section_selectors:
                        try:
                            reviews_section = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if not reviews_section:
                        print("No reviews section found")
                        break
                    
                    # Multiple selectors for individual reviews
                    review_item_selectors = [
                        "div._27M-vq",
                        ".review-item",
                        ".review"
                    ]
                    
                    review_elements = []
                    for selector in review_item_selectors:
                        try:
                            review_elements = reviews_section.find_elements(By.CSS_SELECTOR, selector)
                            if review_elements:
                                break
                        except:
                            continue
                    
                    for element in review_elements:
                        if len(reviews) >= self.max_reviews:
                            break
                            
                        try:
                            # Review text with multiple selectors
                            text_selectors = [
                                "div.t-ZTKy",
                                ".review-text",
                                ".review-content"
                            ]
                            
                            text = ""
                            for text_selector in text_selectors:
                                try:
                                    text_element = element.find_element(By.CSS_SELECTOR, text_selector)
                                    text = text_element.text.strip()
                                    if text and len(text) > 10:
                                        break
                                except:
                                    continue
                            
                            # Rating with multiple selectors
                            rating = 0
                            rating_selectors = [
                                "div._3LWZlK",
                                ".rating",
                                ".review-rating"
                            ]
                            
                            for rating_selector in rating_selectors:
                                try:
                                    rating_element = element.find_element(By.CSS_SELECTOR, rating_selector)
                                    rating_text = rating_element.text.strip()
                                    rating_match = re.search(r'(\d)', rating_text)
                                    if rating_match:
                                        rating = int(rating_match.group(1))
                                        break
                                except:
                                    continue
                            
                            if text and len(text) > 10:
                                reviews.append({
                                    'text': text,
                                    'rating': rating
                                })
                        except:
                            continue
                    
                    # Try to load more reviews
                    if len(reviews) < self.max_reviews:
                        load_more_selectors = [
                            "//span[contains(text(), 'Load more')]",
                            "//button[contains(text(), 'Load more')]",
                            ".load-more"
                        ]
                        
                        loaded_more = False
                        for selector in load_more_selectors:
                            try:
                                if selector.startswith("//"):
                                    load_more_button = self.driver.find_element(By.XPATH, selector)
                                else:
                                    load_more_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                
                                if load_more_button.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", load_more_button)
                                    time.sleep(3)
                                    current_page += 1
                                    loaded_more = True
                                    break
                            except:
                                continue
                        
                        if not loaded_more:
                            break
                    else:
                        break
                        
                except Exception as e:
                    print(f"Error on Flipkart page {current_page}: {e}")
                    break
                
        except Exception as e:
            print(f"Error scraping Flipkart reviews: {e}")
        
        final_reviews = reviews[:self.max_reviews]
        print(f"Scraped {len(final_reviews)} Flipkart reviews")
        return final_reviews, product_name
    
    def scrape_generic_reviews(self, url):
        reviews = []
        product_name = ""
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common review selectors
            review_selectors = [
                '.review', '.review-item', '.user-review',
                '[class*="review"]', '[class*="comment"]'
            ]
            
            for selector in review_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        if len(reviews) >= self.max_reviews:
                            break
                            
                        text = element.get_text().strip()
                        if text and len(text) > 20:
                            reviews.append({
                                'text': text,
                                'rating': 0
                            })
                    break
            
            # Try to get product name
            title_selectors = ['h1', '.product-title', '[class*="title"]', 'title']
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    product_name = element.get_text().strip()
                    break
                    
        except Exception as e:
            print(f"Error scraping generic reviews: {e}")
        
        final_reviews = reviews[:self.max_reviews]
        print(f"Scraped {len(final_reviews)} generic reviews")
        return final_reviews, product_name
    
    def scrape_reviews(self, url, max_reviews=None):
        """
        Scrape reviews from the given URL.
        
        Args:
            url (str): The product URL to scrape
            max_reviews (int, optional): Override the default max_reviews for this scrape
            
        Returns:
            tuple: (reviews_list, product_name)
        """
        if max_reviews is not None:
            original_max = self.max_reviews
            self.max_reviews = max_reviews
        
        site_type = self.identify_site(url)
        print(f"Scraping {site_type} reviews (max: {self.max_reviews})")
        
        if site_type == 'amazon':
            result = self.scrape_amazon_reviews(url)
        elif site_type == 'flipkart':
            result = self.scrape_flipkart_reviews(url)
        else:
            result = self.scrape_generic_reviews(url)
        
        # Restore original max_reviews if it was overridden
        if max_reviews is not None:
            self.max_reviews = original_max
            
        return result
    
    def set_max_reviews(self, max_reviews):
        """
        Update the maximum number of reviews to scrape.
        
        Args:
            max_reviews (int): New maximum number of reviews
        """
        self.max_reviews = max_reviews
        print(f"Updated max reviews to: {max_reviews}")
    
    def close(self):
        """Properly close the webdriver"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                print(f"Error closing driver: {e}")
    
    def __del__(self):
        self.close()