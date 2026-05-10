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
import random
from datetime import datetime
import re
import io
import requests

class B2BPriceCollector:
    def __init__(self):
        print("🚀 [엔진] 지능형 통합 수집 시스템을 가동합니다. (PC버전 정확도 복구 모드)")
        options = Options()
        options.add_argument('--headless') 
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        
        prefs = {'profile.managed_default_content_settings.images': 2}
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        self.results = []
        self.processed_pcodes = set()

    def human_wait(self, min_s=1.2, max_s=2.8):
        time.sleep(random.uniform(min_s, max_s))

    def load_keywords_from_gsheet(self, url):
        try:
            csv_url = url.replace('/edit#gid=', '/export?format=csv&gid=').replace('/edit?gid=', '/export?format=csv&gid=')
            if '/export' not in csv_url:
                csv_url = url.split('/edit')[0] + '/export?format=csv'
            
            df = pd.read_csv(csv_url, on_bad_lines='skip')
            col_name = df.columns[0]
            k_list = [str(k).strip() for k in df[col_name].dropna().tolist() if str(k).strip()]
            print(f"✅ [키워드] 수집 대상: {', '.join(k_list)}")
            return k_list
        except Exception as e:
            print(f"❌ [키워드] 로드 실패: {e}")
            return None

    def login(self, site_name, login_url, username, password, selectors):
        try:
            print(f"🔐 [{site_name}] 로그인 시도 중...")
            self.driver.get(login_url)
            self.human_wait(2, 4)
            wait = WebDriverWait(self.driver, 15)
            u_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors['username'])))
            u_input.send_keys(username)
            self.human_wait(0.5, 1.2)
            self.driver.find_element(By.CSS_SELECTOR, selectors['password']).send_keys(password)
            self.human_wait(0.5, 1.0)
            self.driver.find_element(By.CSS_SELECTOR, selectors['login_button']).click()
            time.sleep(4) 
            return True
        except:
            return False

    def collect_site_data(self, site_name, list_url, domain, selectors, keywords, grade="일반"):
        try:
            target_products = []
            
            # 1. 목록 수집 (현재의 효율성 유지 - 반복 검색 제거)
            if grade == "VIP":
                for page in range(1, 8):
                    self.driver.get(f"{list_url}&page={page}")
                    self.human_wait(1.5, 2.5)
                    items = self.driver.find_elements(By.CSS_SELECTOR, selectors['item_container'])
                    if not items: break
                    for it in items:
                        try:
                            onclick = it.get_attribute('onclick')
                            pcode = re.search(r"['\"]([^'\"]+)['\"]", onclick).group(1)
                            pname = it.find_element(By.CSS_SELECTOR, selectors['product_name']).text
                            target_products.append({'pcode': pcode, 'name': pname, 'kw': '전체'})
                        except: continue
            else:
                for kw in keywords:
                    self.driver.get(f"{list_url}&stx={kw}&page=1")
                    self.human_wait(1.2, 2.0)
                    items = self.driver.find_elements(By.CSS_SELECTOR, selectors['item_container'])
                    for it in items:
                        try:
                            onclick = it.get_attribute('onclick')
                            pcode = re.search(r"['\"]([^'\"]+)['\"]", onclick).group(1)
                            pname = it.find_element(By.CSS_SELECTOR, selectors['product_name']).text
                            target_products.append({'pcode': pcode, 'name': pname, 'kw': kw})
                        except: continue

            unique_targets = {t['pcode']: (t['name'], t['kw']) for t in target_products}

            # 2. 팝업창 단가표 추출 (과거 PC 버전의 "정확성" 완벽 이식)
            for pcode, (p_name, kw_hint) in unique_targets.items():
                if pcode in self.processed_pcodes: continue
                
                try:
                    detail_url = f"https://{domain}/partner/product/prt.detail.pop.php?pcode={pcode}"
                    self.driver.get(detail_url)
                    
                    # ⭐ 핵심 복구: 과거처럼 표가 화면에 완전히 나타날 때까지 끈질기게 기다림 (최대 5초 대기 + 1초 추가 휴식)
                    try:
                        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".list_table")))
                        time.sleep(1.0) # 표가 로딩된 후 안정화 시간 보장
                    except:
                        pass 
                    
                    rows = self.driver.find_elements(By.CSS_SELECTOR, ".list_table tr")
                    label = f"{site_name}({grade})" if grade != "일반" else site_name

                    if len(rows) > 1:
                        # 하위 옵션이 있는 경우 (기획 상품 완벽 추출)
                        for row in rows[1:]:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 6:
                                opt_name = cells[0].text.strip()
                                for k in keywords:
                                    if k in opt_name or k in p_name:
                                        self.results.append({
                                            '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                            '사이트명': label, '키워드': k,
                                            '상품명': p_name, '옵션명': opt_name,
                                            '공급가': cells[2].text.strip(), '재고': cells[1].text.strip(),
                                            '배송비': cells[5].text.strip().split('\n')[0], '상세URL': detail_url
                                        })
                                        break
                    else:
                        # 단일 품목인 경우
                        for k in keywords:
                            if k in p_name:
                                self.results.append({
                                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    '사이트명': label, '키워드': k,
                                    '상품명': p_name, '옵션명': '단일품목',
                                    '공급가': '상세참조', '재고': '있음', '배송비': '별도', '상세URL': detail_url
                                })
                                break
                    self.processed_pcodes.add(pcode)
                except: continue
        except Exception as e:
            print(f"⚠️ [{site_name}] 수집 중 에러: {e}")

    def collect_from_gsheet_smart(self, name, base_url, keywords):
        try:
            print(f"📊 [{name}] 시트 지능형 스캔 시작...")
            xlsx_url = base_url.split('/edit')[0] + '/export?format=xlsx'
            response = requests.get(xlsx_url)
            all_sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, header=None)
            
            for sheet_name, df in all_sheets.items():
                content_sample = ' '.join(df.astype(str).values.flatten())
                matched_kws = [k for k in keywords if k in content_sample]
                if not matched_kws: continue
                
                header_idx = 0
                for i, row in df.iterrows():
                    row_txt = ''.join(row.astype(str).str.replace(' ', ''))
                    if any(x in row_txt for x in ['상품명', '품목명', '단가', '공급가']):
                        header_idx = i; break
                
                df.columns = df.iloc[header_idx]
                data_df = df[header_idx+1:].copy()
                
                name_col, price_col = None, None
                for col in data_df.columns:
                    c_str = str(col).replace(' ', '')
                    if any(x in c_str for x in ['상품', '품목', '제품']): name_col = col
                    if any(x in c_str for x in ['공급가', '단가', '도매가', '판매가', '금액']): price_col = col
                
                if not name_col or not price_col: continue

                for _, r in data_df.iterrows():
                    p_val = str(r.get(name_col, '')).strip()
                    o_val = str(r.get('옵션', '')) if '옵션' in data_df.columns else ''
                    
                    # ⭐ 과거 방식 필터링 1: 공지사항이나 긴 글 무시
                    if '\n' in p_val or len(p_val) > 40 or p_val.lower() == 'nan': 
                        continue
                    
                    for k in matched_kws:
                        if k in p_val or k in o_val:
                            price_val = str(r.get(price_col, '')).strip()
                            
                            # ⭐ 과거 방식 필터링 2: "8/20일(수) 부터" 같은 가짜 가격 무시 (숫자가 없거나 날짜 단어 포함 시 버림)
                            if any(x in price_val for x in ['일', '월', '부터', '예정', '마감']):
                                continue
                            
                            num_check = re.sub(r'[^\d]', '', price_val)
                            if not num_check or len(num_check) < 3: # 최소 100원 단위 이상이어야 진짜 가격으로 인정
                                continue

                            if price_val and 'nan' not in price_val.lower():
                                self.results.append({
                                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    '사이트명': f"{name}({sheet_name})", '키워드': k,
                                    '상품명': p_val, '옵션명': o_val.strip(),
                                    '공급가': price_val, '재고': '시트참조',
                                    '배송비': '별도확인', '상세URL': base_url
                                })
                            break
        except Exception as e:
            print(f"❌ [{name}] 시트 분석 실패: {e}")

    def save_excel(self, filename):
        if self.results:
            pd.DataFrame(self.results).drop_duplicates().to_excel(filename, index=False)
            print(f"💾 총 {len(self.results)}건의 데이터 수집 완료.")

    def close(self): self.driver.quit()
