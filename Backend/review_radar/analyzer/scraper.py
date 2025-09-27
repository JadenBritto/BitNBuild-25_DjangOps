import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from urllib.parse import urlparse

class ReviewScraper:
    def __init__(self):
        self.setup_driver()
    
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
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
                review_url = f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm"
                
                self.driver.get(review_url)
                time.sleep(3)
                
                # Get product name
                try:
                    product_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-hook='product-link']"))
                    )
                    product_name = product_element.text
                except:
                    product_name = "Amazon Product"
                
                # Load more reviews
                for _ in range(5):  # Limit to prevent timeout
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "li.a-last a")
                        if next_button:
                            self.driver.execute_script("arguments[0].click();", next_button)
                            time.sleep(2)
                    except:
                        break
                
                # Extract reviews
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-hook='review']")
                
                for element in review_elements:
                    try:
                        # Review text
                        text_element = element.find_element(By.CSS_SELECTOR, "[data-hook='review-body'] span")
                        text = text_element.text.strip()
                        
                        # Rating
                        rating = 0
                        try:
                            rating_element = element.find_element(By.CSS_SELECTOR, "[data-hook='review-star-rating']")
                            rating_text = rating_element.get_attribute('class')
                            rating_match = re.search(r'a-star-(\d)', rating_text)
                            if rating_match:
                                rating = int(rating_match.group(1))
                        except:
                            pass
                        
                        if text and len(text) > 10:
                            reviews.append({
                                'text': text,
                                'rating': rating
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error scraping Amazon reviews: {e}")
        
        return reviews, product_name
    
    def scrape_flipkart_reviews(self, url):
        reviews = []
        product_name = ""
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Get product name
            try:
                product_element = self.driver.find_element(By.CSS_SELECTOR, "span.B_NuCI")
                product_name = product_element.text
            except:
                product_name = "Flipkart Product"
            
            # Find reviews section
            try:
                reviews_section = self.driver.find_element(By.CSS_SELECTOR, "div._16PBlm")
                review_elements = reviews_section.find_elements(By.CSS_SELECTOR, "div._27M-vq")
                
                for element in review_elements:
                    try:
                        # Review text
                        text_element = element.find_element(By.CSS_SELECTOR, "div.t-ZTKy")
                        text = text_element.text.strip()
                        
                        # Rating
                        rating = 0
                        try:
                            rating_element = element.find_element(By.CSS_SELECTOR, "div._3LWZlK")
                            rating = int(rating_element.text.strip())
                        except:
                            pass
                        
                        if text and len(text) > 10:
                            reviews.append({
                                'text': text,
                                'rating': rating
                            })
                    except:
                        continue
                        
            except:
                pass
                
        except Exception as e:
            print(f"Error scraping Flipkart reviews: {e}")
        
        return reviews, product_name
    
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
        
        return reviews, product_name
    
    def scrape_reviews(self, url):
        site_type = self.identify_site(url)
        
        if site_type == 'amazon':
            return self.scrape_amazon_reviews(url)
        elif site_type == 'flipkart':
            return self.scrape_flipkart_reviews(url)
        else:
            return self.scrape_generic_reviews(url)
    
    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()