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
        print("🚀 [엔진] 브라우저를 준비하고 있습니다...")
        options = Options()
        options.add_argument('--headless')  # 화면 없이 실행
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # 속도 향상을 위해 이미지 로딩 제외
        options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.results = []
        self.seen_pcodes = set() 

    def load_keywords_from_gsheet(self, url):
        """디렉터님의 마스터 시트에서 수집 대상 품목(키워드)을 읽어옵니다."""
        try:
            print("📜 [키워드] 마스터 시트에서 오늘의 품목을 읽어오는 중...")
            # CSV로 로드 시도
            df = pd.read_csv(url, on_bad_lines='skip')
            # 첫 번째 열의 데이터를 리스트로 변환
            col_name = df.columns[0]
            k_list = df[col_name].dropna().astype(str).tolist()
            k_list = [k.strip() for k in k_list if k.strip()]
            print(f"🎯 [키워드] {len(k_list)}개 품목 수집 명령 하달: {', '.join(k_list)}")
            return k_list
        except Exception as e:
            print(f"⚠️ [키워드] 시트 로드 실패. 공유 설정을 확인하세요! ({e})")
            return None

    def login(self, site_name, login_url, username, password, selectors):
        """웹사이트 로그인 (대기 시간 강화)"""
        try:
            print(f"🔐 [{site_name}] 접속 및 로그인 시도 중...")
            self.driver.get(login_url)
            wait = WebDriverWait(self.driver, 15)
            
            user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors['username'])))
            user_input.clear()
            user_input.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, selectors['password']).send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, selectors['login_button']).click()
            
            time.sleep(6) # 로그인 후 메인 로딩 대기
            return "login" not in self.driver.current_url.lower()
        except:
            return False

    def collect_by_search(self, site_name, list_url, domain, selectors, keyword):
        """웹사이트 상세 검색 및 수집"""
        try:
            from config import MAX_PAGES
            print(f"🔍 [{site_name}] '{keyword}' 검색 중...")
            for page in range(1, MAX_PAGES + 1):
                self.driver.get(f"{list_url}&stx={keyword}&page={page}")
                time.sleep(4)
                
                items = self.driver.find_elements(By.CSS_SELECTOR, selectors['item_container'])
                if not items: break
                
                for item in items:
                    try:
                        onclick = item.get_attribute('onclick')
                        if not onclick: continue
                        pcode = onclick.split("'")[1] if "'" in onclick else onclick.split('"')[1]
                        if pcode in self.seen_pcodes: continue
                        
                        p_name = item.find_element(By.CSS_SELECTOR, selectors['product_name']).text
                        detail_url = f"https://{domain}/partner/product/prt.detail.pop.php?pcode={pcode}"
                        
                        self.driver.execute_script(f"window.open('{detail_url}','_blank');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(3)
                        
                        rows = self.driver.find_elements(By.CSS_SELECTOR, ".list_table tr")[1:]
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 6:
                                self.results.append({
                                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    '사이트명': site_name, '키워드': keyword,
                                    '상품명': p_name, '옵션명': cells[0].text.strip(),
                                    '공급가': cells[2].text.strip(), '재고': cells[1].text.strip(),
                                    '배송비': cells[5].text.strip().split('\n')[0], '상세URL': detail_url
                                })
                        self.seen_pcodes.add(pcode)
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    except: continue
        except: pass

    def collect_from_gsheet(self, name, conf, keywords):
        """구글 시트 단가표 연동 (최신 날짜 가격 자동 탐색 및 키워드 필터링)"""
        try:
            print(f"📊 [{name}] 시트 가격 데이터 분석 중...")
            df = pd.read_csv(conf['url'], on_bad_lines='skip', header=None)
            h_idx = 0
            for i, r in df.iterrows():
                row_str = ' '.join(map(str, r))
                if any(x in row_str for x in ['상품명', '품목', '제품명']):
                    h_idx = i; break
            df.columns = [str(c).strip() for c in df.iloc[h_idx]]
            df = df[h_idx+1:]
            
            for _, r in df.iterrows():
                p_name = str(r.get(conf['mapping'].get('상품명', '상품명'), ''))
                o_name = str(r.get(conf['mapping'].get('옵션명', '옵션명'), ''))
                
                # 마스터 시트에서 로드한 키워드가 포함된 경우만 수집
                matched = None
                for k in keywords:
                    if k in p_name or k in o_name:
                        matched = k; break
                if not matched: continue 
                
                # 가변 날짜(예: 웰그린푸드)에서 가장 오른쪽 가격 열 찾기
                p_col = conf['mapping'].get('공급가', '공급가')
                if p_col not in df.columns or p_col == '가장우측날짜':
                    for c in reversed(df.columns): # 오른쪽부터 역순 탐색
                        if any(x in str(c) for x in ['/', '.', '월', '공급가', '~']): 
                            p_col = c; break
                
                price = str(r.get(p_col, ''))
                if not p_name.strip() or not price.strip() or 'nan' in p_name.lower(): 
                    continue
                
                self.results.append({
                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    '사이트명': name, '키워드': matched, '상품명': p_name.strip(), '옵션명': o_name.strip(),
                    '공급가': price.strip(), '재고': '시트참조', '배송비': '별도확인', 
                    '상세URL': conf['url'].split('/export')[0]
                })
            print(f"✅ [{name}] 시트 연동 완료")
        except Exception as e:
            print(f"❌ [{name}] 오류: {e}")

    def save_excel(self, filename):
        if self.results:
            pd.DataFrame(self.results).to_excel(filename, index=False)
            print(f"💾 총 {len(self.results)}건 저장 완료!")

    def close(self): 
        self.driver.quit()
