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
import re

class B2BPriceCollector:
    def __init__(self):
        print("🚀 [엔진] 브라우저를 기동합니다 (보안 우회 모드)...")
        options = Options()
        options.add_argument('--headless') 
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # ⭐ 로봇 차단을 피하기 위한 위장술(User-Agent) 및 설정 추가
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # 자동화 탐지 방지 스크립트 적용
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        self.results = []
        self.seen_pcodes = set() 
        self.MAX_ITEMS_PER_KW = 15 

    def load_keywords_from_gsheet(self, url):
        """디렉터님의 마스터 시트에서 수집 대상 키워드 목록을 가져옵니다."""
        try:
            print("📜 [키워드] 마스터 시트 로드 중...")
            df = pd.read_csv(url, on_bad_lines='skip')
            col_name = df.columns[0]
            k_list = df[col_name].dropna().astype(str).tolist()
            return [k.strip() for k in k_list if k.strip()]
        except Exception as e:
            print(f"⚠️ [키워드] 시트 로드 실패: {e}")
            return None

    def login(self, site_name, login_url, username, password, selectors):
        """로그인 세션을 확실하게 잡기 위해 대기 로직을 강화했습니다."""
        try:
            print(f"🔐 [{site_name}] 로그인 시도 중...")
            self.driver.get(login_url)
            wait = WebDriverWait(self.driver, 15)
            
            user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors['username'])))
            user_input.clear()
            user_input.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, selectors['password']).send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, selectors['login_button']).click()
            
            time.sleep(5)
            
            # 로그인 성공 여부 체크
            current_url = self.driver.current_url.lower()
            if "login" in current_url and "login_ok" not in current_url:
                print(f"❌ [{site_name}] 로그인 실패 (URL 확인 요망)")
                return False
                
            print(f"✅ [{site_name}] 로그인 성공!")
            return True
        except Exception as e:
            print(f"❌ [{site_name}] 로그인 에러: {e}")
            return False

    def collect_by_search(self, site_name, list_url, domain, selectors, keyword, grade="일반"):
        """검색 결과에서 VIP 등 등급 정보를 포함하여 수집합니다."""
        try:
            from config import MAX_PAGES
            print(f"🔍 [{site_name}] ({grade}) '{keyword}' 검색 중...")
            count = 0
            
            for page in range(1, MAX_PAGES + 1):
                if count >= self.MAX_ITEMS_PER_KW: break

                search_url = f"{list_url}&stx={keyword}&page={page}"
                self.driver.get(search_url)
                time.sleep(4) 
                
                # 상품 리스트 로딩 대기
                try:
                    wait = WebDriverWait(self.driver, 10)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors['item_container'])))
                except:
                    print(f"   - {page}페이지: 상품 없음")
                    break
                
                items = self.driver.find_elements(By.CSS_SELECTOR, selectors['item_container'])
                for item in items:
                    if count >= self.MAX_ITEMS_PER_KW: break
                    try:
                        onclick = item.get_attribute('onclick')
                        if not onclick or 'prtView' not in onclick: continue
                        
                        pcode_match = re.search(r"['\"]([^'\"]+)['\"]", onclick)
                        if not pcode_match: continue
                        pcode = pcode_match.group(1)
                        
                        if pcode in self.seen_pcodes: continue
                        
                        p_name = item.find_element(By.CSS_SELECTOR, selectors['product_name']).text
                        detail_url = f"https://{domain}/partner/product/prt.detail.pop.php?pcode={pcode}"
                        
                        # 상세 팝업 열기
                        self.driver.execute_script(f"window.open('{detail_url}','_blank');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(3)
                        
                        option_rows = self.driver.find_elements(By.CSS_SELECTOR, ".list_table tr")
                        if len(option_rows) > 1:
                            for row in option_rows[1:]:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 6:
                                    # 등급 표시 추가
                                    display_site = f"{site_name}({grade})" if grade != "일반" else site_name
                                    self.results.append({
                                        '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                        '사이트명': display_site, 
                                        '키워드': keyword,
                                        '상품명': p_name, 
                                        '옵션명': cells[0].text.strip(),
                                        '공급가': cells[2].text.strip(), 
                                        '재고': cells[1].text.strip(),
                                        '배송비': cells[5].text.strip().split('\n')[0], 
                                        '상세URL': detail_url
                                    })
                        
                        self.seen_pcodes.add(pcode)
                        count += 1
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    except: continue
                    
            print(f"✅ [{site_name}] '{keyword}' 수집 완료 ({count}개 품목)")
        except Exception as e:
            print(f"⚠️ [{site_name}] 수집 중단: {e}")

    def collect_from_gsheet(self, name, conf, keywords):
        """구글 시트 단가표에서 최신 날짜의 가격을 추출합니다."""
        try:
            print(f"📊 [{name}] 구글 시트 분석 중...")
            df = pd.read_csv(conf['url'], on_bad_lines='skip', header=None)
            h_idx = 0
            for i, r in df.iterrows():
                if any(x in ' '.join(map(str, r)) for x in ['상품명', '품목', '제품명']):
                    h_idx = i; break
            df.columns = [str(c).strip() for c in df.iloc[h_idx]]
            df = df[h_idx+1:]
            for _, r in df.iterrows():
                p_name = str(r.get(conf['mapping'].get('상품명', '상품명'), ''))
                o_name = str(r.get(conf['mapping'].get('옵션명', '옵션명'), ''))
                matched = None
                for k in keywords:
                    if k in p_name or k in o_name: matched = k; break
                if not matched: continue 
                
                # 가격 컬럼(가장 우측 날짜) 자동 탐색
                p_col = conf['mapping'].get('공급가', '공급가')
                if p_col not in df.columns or p_col == '가장우측날짜':
                    for c in reversed(df.columns):
                        if any(x in str(c) for x in ['/', '.', '월', '공급가']): p_col = c; break
                
                price = str(r.get(p_col, ''))
                if not p_name.strip() or not price.strip() or 'nan' in str(price).lower(): continue
                
                self.results.append({
                    '수집날짜': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    '사이트명': name, '키워드': matched, '상품명': p_name.strip(), '옵션명': o_name.strip(),
                    '공급가': price.strip(), '재고': '시트참조', '배송비': '별도확인', '상세URL': conf['url'].split('/export')[0]
                })
        except Exception as e:
            print(f"❌ [{name}] 시트 분석 오류: {e}")

    def save_excel(self, filename):
        if self.results:
            final_df = pd.DataFrame(self.results).drop_duplicates()
            final_df.to_excel(filename, index=False)
            print(f"💾 총 {len(final_df)}건의 데이터를 성공적으로 저장했습니다!")
        else:
            print("⚠️ 수집된 데이터가 없습니다.")

    def close(self): self.driver.quit()
