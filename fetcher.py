import time
import logging
import io
import json
import base64
from PIL import Image
import urllib.robotparser
from urllib.parse import urljoin
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

Image.MAX_IMAGE_PIXELS = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

robot_parsers = {}

def get_robot_parser(url):
    base_url = urljoin(url, '/')
    if base_url in robot_parsers:
        return robot_parsers[base_url]
    
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(base_url, 'robots.txt'))
    try:
        rp.read()
        robot_parsers[base_url] = rp
        return rp
    except Exception as e:
        logging.warning(f"Could not fetch or parse robots.txt for {base_url}: {e}")
        robot_parsers[base_url] = None
        return None

def perform_fetch_selenium(
    url: str,
    user_agent_key: str,
    user_agent_string: str,
    headless: bool,
    timeout_seconds: int,
    language: str,
    obey_robots: bool
) -> dict:
    logging.info(f"Starting fetch for URL: {url} using Scroll-and-Verify Method.")

    options = webdriver.ChromeOptions()
    options.add_argument(f'--lang={language.split(",")[0]}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") 
    options.add_argument("--start-maximized") 
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-web-security") 

    is_mobile = "Smartphone" in user_agent_key
    if not is_mobile:
        options.add_argument(f'user-agent={user_agent_string}')
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080") 

    driver = None
    overall_start_time = time.time()
    status_code, headers, response_reason = "N/A", "N/A", "Unknown"
    
    try:
        driver = webdriver.Chrome(options=options, seleniumwire_options={'disable_encoding': True})
        
        if is_mobile:
            mobile_metrics = {"width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True}
            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", mobile_metrics)
            driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {"userAgent": user_agent_string})
            driver.set_window_size(mobile_metrics["width"], mobile_metrics["height"])
        elif headless:
            driver.set_window_size(1920, 1080)

        driver.set_page_load_timeout(60)
        get_start_time = time.time()
        driver.get(url)
        response_time = time.time() - get_start_time

        try:
            request = driver.wait_for_request(url, timeout=30)
            status_code, response_reason = request.response.status_code, request.response.reason
            headers = "\n".join([f"{k}: {v}" for k, v in request.response.headers.items()])
        except (TimeoutException, Exception):
            logging.warning(f"Could not capture initial request details for {url}.")

        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except (TimeoutException, WebDriverException):
            logging.warning(f"Page load wait condition failed.")

        logging.info(f"Waiting for {timeout_seconds}s for initial dynamic content to settle.")
        time.sleep(timeout_seconds)

        js_gentle_neutralize = """
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
              const position = window.getComputedStyle(element).getPropertyValue('position');
              if (position === 'fixed' || position === 'sticky') {
                element.style.position = 'static';
              }
            }
        """
        
        js_hide_widgets = """
            const selectors = [
                '[id*=chat]', '[id*=Chat]', '[class*=chat]', '[class*=Chat]',
                '[id*=intercom]', '[class*=intercom]',
                '[id*=drift]', '[class*=drift]',
                '[id*=liveperson]', '[class*=liveperson]',
                '.back-to-top', '.go-to-top',
                '[id*=chat-widget]', '[class*=chat-widget]'
            ];
            const elementsToHide = document.querySelectorAll(selectors.join(','));
            elementsToHide.forEach(el => el.style.display = 'none');
        """
        
        # --- START OF THE DEFINITIVE SCROLL-AND-VERIFY LOGIC ---
        
        viewport_height = driver.execute_script("return window.innerHeight")
        driver.execute_script("document.body.style.overflow = 'hidden';")
        
        viewport_screenshots = []
        
        while True:
            # Get current geometry BEFORE taking screenshot
            total_height = driver.execute_script("return document.body.scrollHeight")
            current_scroll_y = driver.execute_script("return window.scrollY")

            # PERSISTENT HIDING: Re-apply hiding scripts to catch late-loading elements
            driver.execute_script(js_gentle_neutralize)
            driver.execute_script(js_hide_widgets)
            time.sleep(0.5)

            logging.info(f"Capturing viewport at scroll position {current_scroll_y} / {total_height}")
            screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
            img_bytes = base64.b64decode(screenshot_data['data'])
            img = Image.open(io.BytesIO(img_bytes))
            viewport_screenshots.append(img)
            
            # Scroll for the next iteration
            driver.execute_script(f"window.scrollBy(0, {viewport_height});")
            # PATIENT WAIT: Give time for animations and new content to load
            time.sleep(2.5) 

            # VERIFY: Get new geometry and check if we're done
            new_scroll_y = driver.execute_script("return window.scrollY")
            new_total_height = driver.execute_script("return document.body.scrollHeight")
            
            # Condition 1: We are at the bottom of the page
            at_the_bottom = (new_scroll_y + viewport_height) >= new_total_height
            # Condition 2 (Fail-safe): We tried to scroll but got stuck
            is_stuck = (new_scroll_y == current_scroll_y)

            if at_the_bottom or is_stuck:
                if is_stuck and not at_the_bottom:
                    logging.warning("Scroll position is stuck, but not at the bottom. Stopping to prevent infinite loop.")
                else:
                    logging.info("Reached the end of the page.")
                break

        # --- END OF THE DEFINITIVE SCROLL-AND-VERIFY LOGIC ---

        logging.info(f"Captured {len(viewport_screenshots)} screenshots. Now stitching them together.")

        if not viewport_screenshots:
            raise Exception("No screenshots were captured.")
            
        final_page_height = driver.execute_script("return document.body.scrollHeight")
        stitched_width = viewport_screenshots[0].width
        stitched_image = Image.new('RGB', (stitched_width, final_page_height))
        
        y_offset = 0
        for img in viewport_screenshots:
            stitched_image.paste(img, (0, y_offset))
            y_offset += img.height
            
        stitched_image = stitched_image.crop((0, 0, stitched_width, final_page_height))

        buffered = io.BytesIO()
        stitched_image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        logging.info("Stitching complete. Final image encoded.")

        final_html = driver.page_source
        
        js_console_errors = []
        try:
            logs = driver.get_log('performance')
            for entry in logs:
                log = json.loads(entry['message'])['message']
                if log['method'] == 'Log.entryAdded' and log['params']['entry']['level'] == 'error':
                    js_console_errors.append({'Message': log['params']['entry']['text'], 'URL': log['params']['entry'].get('url', 'N/A')})
        except WebDriverException:
            logging.warning(f"Could not retrieve performance logs.")

        blocked_by_robots, inaccessible_urls = [], []
        for req in driver.requests:
            if req.url.startswith(('http://', 'https://')):
                if req.response and req.response.status_code >= 400:
                    inaccessible_urls.append({'Resource URL': req.url, 'Resource Type': req.response.headers.get('Content-Type', 'Unknown').split(';')[0], 'Status': f"{req.response.status_code} {req.response.reason}"})
                if obey_robots:
                    rp = get_robot_parser(req.url)
                    if rp and not rp.can_fetch(user_agent_string, req.url):
                        blocked_by_robots.append({'Resource URL': req.url, 'Resource Type': 'Fetch', 'Disallow Rule': 'Disallowed by robots.txt'})

        total_render_time = time.time() - overall_start_time

        return {
            "html": final_html, "rendered_page": base64_image,
            "status_code": f"{status_code} {response_reason}", "headers": headers,
            "response_time": response_time, "total_render_time": total_render_time,
            "js_console_errors": js_console_errors, "inaccessible_urls": inaccessible_urls,
            "blocked_by_robots": blocked_by_robots, "error": None
        }

    except Exception as e:
        error_message = f"An error occurred during fetch: {e.__class__.__name__}"
        logging.error(f"{error_message}\nDetails: {e}", exc_info=True)
        return {"error": error_message}

    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed.")