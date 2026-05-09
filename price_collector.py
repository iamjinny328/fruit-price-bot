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
        print("🚀 [엔진] 크롬 브라우저를 준비합니다...")
        options = Options()
        options.add_argument('--headless') 
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # 이미지 로딩을 비활성화하여 수집 속도를 높입니다.
        options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.results = []
        self.seen_pcodes = set()

    def login(self, site_name, login_url, username, password, selectors):
        try:
            print(f"🔐 [{site_name}] 로그인 시도 중...")
            self.driver.get(login_url)
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR, selectors['username']).send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, selectors['password']).send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, selectors['login_button']).click()
            time.sleep(3)
            # 로그인 성공 여부 확인 (URL에 login 단어가 사라졌는지 체크)
            return "login" not in self.driver.current_url.lower()
        except Exception as e:
            print(f"❌ [{site_name}] 로그인 오류: {e}")
            return False

    def collect_by_search(self, site_name, list_url, domain, selectors, keyword):
        try:
            from config import MAX_PAGES
            print(f"🔍 [{site_name}] '{keyword}' 검색 중...")
            for page in range(1, MAX_PAGES + 1):
                self.driver.get(f"{list_url}&stx={keyword}&page={page}")
                time.sleep(2)
                items = self.driver.find_elements(By.CSS_SELECTOR, selectors['item_container'])
                if not items: break
                
                for item in items:
                    try:
                        onclick = item.get_attribute('onclick')
                        pcode = onclick.split("'")[1] if "'" in onclick else onclick.split('"')[1]
                        if pcode in self.seen_pcodes: continue
                        
                        p_name = item.find_element(By.CSS_SELECTOR, selectors['product_name']).text
                        detail_url = f"https://{domain}/partner/product/prt.detail.pop.php?pcode={pcode}"
                        
                        # 상세 옵션 가격 수집을 위해 팝업창을 열고 제어권을 넘깁니다.
                        self.driver.execute_script(f"window.open('{detail_url}','_blank');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(1.5)
                        
                        # 팝업창 내의 가격 테이블 분석
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
                        self.driver.close() # 팝업창 닫기
                        self.driver.switch_to.window(self.driver.window_handles[0]) # 메인 창으로 복귀
                    except: continue
                page += 1
        except Exception as e:
            print(f"⚠️ [{site_name}] 웹 수집 중 오류: {e}")

    def collect_from_gsheet(self, name, conf, keywords):
        try:
            print(f"📊 [{name}] 구글 시트 단가표 분석 시작...")
            # 구글 시트를 CSV 형식으로 즉시 다운로드하여 읽어옵니다.
            df = pd.read_csv(conf['url'], on_bad_lines='skip', header=None)
            
            # 실제 제목(헤더) 줄이 어디인지 찾습니다.
            header_idx = 0
            for i, r in df.iterrows():
                row_str = ' '.join(map(str, r))
                if any(x in row_str for x in ['상품명', '품목', '제품명']):
                    header_idx = i; break
            
            df.columns = [str(c).strip() for c in df.iloc[header_idx]]
            df = df[header_idx+1:]
            
            for _, r in df.iterrows():
                p_name = str(r.get(conf['mapping'].get('상품명', '상품명'), ''))
                o_name = str(r.get(conf['mapping'].get('옵션명', '옵션명'), ''))
                
                # 가격 열이 날짜별로 변하는 경우(예: 웰그린) 마지막 유효 열을 찾습니다.
                p_col = conf['mapping'].get('공급가', '공급가')
                if p_col not in df.columns or p_col == '가장우측날짜':
                    for c in reversed(df.columns):
                        if any(x in str(c) for x in ['/', '월', '~', '공급가']): 
                            p_col = c; break
                
                price = str(r.get(p_col, ''))
                if not p_name.strip() or not price.strip() or 'nan' in p_name.lower(): 
                    continue
                
                # 키워드 매칭
                matched = "기타"
                for k in keywords:
                    if k in p_name or k in o_name: 
                        matched = k; break
                
                self.results.append({
                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    '사이트명': name, '키워드': matched, 
                    '상품명': p_name.strip(), '옵션명': o_name.strip(),
                    '공급가': price.strip(), '재고': '시트참조', '배송비': '별도확인', 
                    '상세URL': conf['url'].split('/export')[0]
                })
            print(f"✅ [{name}] 시트 수집 성공!")
        except Exception as e: 
            print(f"❌ [{name}] 시트 오류: {e}")

    def save_excel(self, filename):
        if self.results:
            pd.DataFrame(self.results).to_excel(filename, index=False)
            print(f"💾 총 {len(self.results)}건 수집 완료! '{filename}'에 저장되었습니다.")
        else:
            print("⚠️ 수집된 데이터가 없어 저장하지 않습니다.")

    def close(self): 
        self.driver.quit()
