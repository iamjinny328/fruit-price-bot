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
        print("🚀 [엔진] 지능형 통합 수집 시스템을 가동합니다.")
        options = Options()
        options.add_argument('--headless') 
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 실제 브라우저처럼 보이게 위장
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        
        # 이미지 로딩 차단 (속도 향상 및 서버 부하 감소)
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # 로봇 감지 우회 설정
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        self.results = []
        self.processed_pcodes = set()

    def human_wait(self, min_s=1.2, max_s=2.8):
        """사람이 고민하고 클릭하는 것처럼 랜덤하게 대기합니다."""
        time.sleep(random.uniform(min_s, max_s))

    def load_keywords_from_gsheet(self, url):
        """마스터 시트에서 수집할 과일 키워드 목록을 가져옵니다."""
        try:
            # URL을 CSV 내보내기 형식으로 자동 변환
            csv_url = url.replace('/edit#gid=', '/export?format=csv&gid=').replace('/edit?gid=', '/export?format=csv&gid=')
            if '/export' not in csv_url:
                csv_url = url.split('/edit')[0] + '/export?format=csv'
            
            df = pd.read_csv(csv_url, on_bad_lines='skip')
            col_name = df.columns[0]
            k_list = [str(k).strip() for k in df[col_name].dropna().tolist() if str(k).strip()]
            print(f"✅ [키워드] 수집 대상: {', '.join(k_list)}")
            return k_list
        except Exception as e:
            print(f"❌ [키워드] 마스터 시트 로드 실패: {e}")
            return None

    def login(self, site_name, login_url, username, password, selectors):
        try:
            print(f"🔐 [{site_name}] 보안 로그인 시도 중...")
            self.driver.get(login_url)
            self.human_wait(2, 4)
            
            wait = WebDriverWait(self.driver, 15)
            u_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors['username'])))
            u_input.send_keys(username)
            self.human_wait(0.5, 1.2)
            self.driver.find_element(By.CSS_SELECTOR, selectors['password']).send_keys(password)
            self.human_wait(0.5, 1.0)
            self.driver.find_element(By.CSS_SELECTOR, selectors['login_button']).click()
            
            time.sleep(4) # 로그인 세션 안정화
            return True
        except:
            return False

    def collect_site_data(self, site_name, list_url, domain, selectors, keywords, grade="일반"):
        """
        [어드민 하이브리드 수집]
        - VIP: 리스트 전체 페이지(1~7) 전수 조사하여 기획상품 추출
        - 일반: 키워드 검색 결과만 빠르게 수집
        """
        try:
            target_products = []
            
            if grade == "VIP":
                print(f"📡 [{site_name}] VIP 전수 조사 모드 가동 (리스트 전체 스캔)")
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
                print(f"🔍 [{site_name}] 일반 검색 수집 모드 가동")
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

            # 중복 제거 및 정밀 분석
            unique_targets = {t['pcode']: (t['name'], t['kw']) for t in target_products}
            print(f"📦 [{site_name}] {len(unique_targets)}개의 품목을 정밀 분석합니다.")

            for pcode, (p_name, kw_hint) in unique_targets.items():
                if pcode in self.processed_pcodes: continue
                
                try:
                    detail_url = f"https://{domain}/partner/product/prt.detail.pop.php?pcode={pcode}"
                    self.driver.get(detail_url)
                    self.human_wait(0.8, 1.5)
                    
                    rows = self.driver.find_elements(By.CSS_SELECTOR, ".list_table tr")
                    label = f"{site_name}({grade})" if grade != "일반" else site_name

                    if len(rows) > 1:
                        # 하위 옵션이 있는 경우 (기획 상품 등)
                        for row in rows[1:]:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 6:
                                opt_name = cells[0].text.strip()
                                # 팝업 안에서 우리가 원하는 모든 과일을 한꺼번에 찾습니다.
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
        """
        [지능형 시트 탐색]
        - 시트 전체를 엑셀로 다운로드하여 모든 탭(과일, 농산 등)을 스스로 찾습니다.
        - 키워드가 포함된 탭만 골라내어 데이터를 추출합니다.
        """
        try:
            print(f"📊 [{name}] 시트 지능형 스캔 시작...")
            # 엑셀 다운로드 주소로 자동 변환
            xlsx_url = base_url.split('/edit')[0] + '/export?format=xlsx'
            
            response = requests.get(xlsx_url)
            all_sheets = pd.read_excel(io.BytesIO(response.content), sheet_name=None, header=None)
            
            for sheet_name, df in all_sheets.items():
                # 1. 탭 전체 내용물에 키워드가 있는지 검사
                content_sample = ' '.join(df.astype(str).values.flatten())
                matched_kws = [k for k in keywords if k in content_sample]
                
                if not matched_kws: continue
                
                print(f"   ㄴ [{sheet_name}] 탭에서 키워드 발견! 수집 중...")
                
                # 2. 제목줄(Header) 위치 자동 탐색
                header_idx = 0
                for i, row in df.iterrows():
                    row_txt = ' '.join(row.astype(str))
                    if any(x in row_txt for x in ['상품', '품목', '제품', '명칭']):
                        header_idx = i; break
                
                df.columns = df.iloc[header_idx]
                data_df = df[header_idx+1:].copy()
                
                # 3. 열 이름 지능적 선택
                name_col, price_col = None, None
                for col in data_df.columns:
                    c_str = str(col)
                    if any(x in c_str for x in ['상품', '품목', '제품']): name_col = col
                    if any(x in c_str for x in ['공급', '단가', '판매', '가격']): price_col = col
                
                # 가격열을 못 찾았거나 날짜별 시트인 경우 맨 오른쪽 선택
                if not price_col or '날짜' in str(price_col) or '/' in str(price_col):
                    price_col = data_df.columns[-1]

                if not name_col: continue

                # 4. 데이터 매칭 및 수집
                for _, r in data_df.iterrows():
                    p_val = str(r.get(name_col, ''))
                    o_val = str(r.get('옵션', '')) if '옵션' in data_df.columns else ''
                    
                    for k in matched_kws:
                        if k in p_val or k in o_val:
                            price_val = str(r.get(price_col, ''))
                            if price_val.strip() and 'nan' not in price_val.lower():
                                self.results.append({
                                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                    '사이트명': f"{name}({sheet_name})", '키워드': k,
                                    '상품명': p_val.strip(), '옵션명': o_val.strip(),
                                    '공급가': price_val.strip(), '재고': '시트참조',
                                    '배송비': '별도확인', '상세URL': base_url
                                })
                            break
            print(f"✅ [{name}] 시트 수집 완료.")
        except Exception as e:
            print(f"❌ [{name}] 시트 분석 실패: {e}")

    def save_excel(self, filename):
        if self.results:
            pd.DataFrame(self.results).drop_duplicates().to_excel(filename, index=False)
            print(f"💾 총 {len(self.results)}건의 데이터를 성공적으로 저장했습니다.")

    def close(self): self.driver.quit()
