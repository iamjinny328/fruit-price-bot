# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from datetime import datetime
import os

class B2BPriceCollector:
    def __init__(self):
        print("🚀 수집 엔진 시작 (고속 검색 및 클라우드 모드)...")
        options = Options()
        # [GitHub 전용] 서버 환경 실행을 위한 Headless 설정
        options.add_argument('--headless') 
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # 이미지 로딩 끄기 (속도 향상)
        prefs = {'profile.managed_default_content_settings.images': 2}
        options.add_experimental_option('prefs', prefs)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.results = []
        self.seen_pcodes = set() # 한 번 확인한 상품 중복 수집 방지

    def login(self, site_name, login_url, username, password, selectors):
        try:
            print(f"\n🔐 [{site_name}] 로그인 시도 ({username})...")
            self.driver.get(login_url)
            time.sleep(2)
            
            wait = WebDriverWait(self.driver, 10)
            user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors['username'])))
            user_input.clear()
            user_input.send_keys(username)
            
            pass_input = self.driver.find_element(By.CSS_SELECTOR, selectors['password'])
            pass_input.clear()
            pass_input.send_keys(password)
            
            self.driver.find_element(By.CSS_SELECTOR, selectors['login_button']).click()
            time.sleep(2)
            
            if "login" in self.driver.current_url.lower():
                print(f"❌ [{site_name}] 로그인 실패")
                return False
            
            print(f"✅ [{site_name}] 로그인 성공!")
            return True
        except Exception as e:
            print(f"❌ [{site_name}] 로그인 중 오류: {e}")
            return False

    def collect_by_search(self, site_name, list_url, domain, selectors, keyword, account_grade):
        try:
            from config import MAX_PAGES
            page = 1
            last_first_item = ""

            while page <= MAX_PAGES:
                search_url = f"{list_url}&stx={keyword}&page={page}"
                self.driver.get(search_url)
                time.sleep(2)
                
                items = self.driver.find_elements(By.CSS_SELECTOR, selectors['item_container'])
                if not items: break
                
                # 중복 페이지 방지: 첫 상품이 이전 페이지와 같으면 수집 멈춤
                current_first_item = items[0].text
                if current_first_item == last_first_item: break
                last_first_item = current_first_item

                for item in items:
                    try:
                        onclick = item.get_attribute('onclick')
                        pcode = onclick.split("'")[1] if "'" in onclick else onclick.split('"')[1]
                        
                        if pcode in self.seen_pcodes: continue
                        
                        product_name = item.find_element(By.CSS_SELECTOR, selectors['product_name']).text
                        detail_url = f"https://{domain}/partner/product/prt.detail.pop.php?pcode={pcode}"
                        
                        # 팝업창 띄우기
                        self.driver.execute_script(f"window.open('{detail_url}','_blank');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(1.5)
                        
                        # 옵션 테이블 파싱 (기존 로직 유지)
                        rows = self.driver.find_elements(By.CSS_SELECTOR, ".list_table tr")[1:]
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 6:
                                self.results.append({
                                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    '사이트명': site_name,
                                    '계정등급': account_grade,
                                    '키워드': keyword,
                                    '상품명': product_name,
                                    '옵션명': cells[0].text.strip(),
                                    '공급가': cells[2].text.strip(),
                                    '재고': cells[1].text.strip(),
                                    '배송비': cells[5].text.strip().split('\n')[0],
                                    '상세URL': detail_url
                                })
                        
                        self.seen_pcodes.add(pcode)
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    except: continue
                page += 1
        except Exception as e:
            print(f"⚠️ [{site_name}] 검색 수집 중단: {e}")

    def save_excel(self, history_filename):
        if not self.results: return
        df = pd.DataFrame(self.results)
        df.to_excel(history_filename, index=False)
        print(f"\n💾 수집 완료 및 엑셀 저장됨: {history_filename}")

    def close(self):
        self.driver.quit()