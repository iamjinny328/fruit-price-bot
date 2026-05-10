# -*- coding: utf-8 -*-
from price_collector import B2BPriceCollector
from config import SITES, GSHEETS, PRICE_HISTORY_FILE, KEYWORD_MASTER_URL
import os

def main():
    # 수집기 엔진 가동
    collector = B2BPriceCollector()
    
    # 1. 키워드 로드 (디렉터님 개인 구글 시트에서 최우선적으로 읽어옵니다)
    keywords = collector.load_keywords_from_gsheet(KEYWORD_MASTER_URL)
    
    # 만약 시트 연결에 실패할 경우를 대비한 백업 (기존 keywords.txt 사용)
    if not keywords:
        try:
            print("⚠️ 시트 로딩 실패로 기존 keywords.txt 파일을 참조합니다.")
            with open('keywords.txt', 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ 키워드 파일을 찾을 수 없습니다. 기본값을 사용합니다: {e}")
            keywords = ['사과', '참외', '토마토']

    # 2. 계정 정보 로드 (accounts.txt)
    accounts = {}
    try:
        with open('accounts.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ',' not in line or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    site_key, user, pw = parts[0], parts[1], parts[2]
                    # ALL 계정 처리
                    if site_key.upper() == 'ALL':
                        for s in SITES:
                            accounts[s] = {'u': user, 'p': pw}
                    elif site_key in SITES:
                        accounts[site_key] = {'u': user, 'p': pw}
    except Exception as e:
        print(f"⚠️ 계정 정보를 읽는 중 오류가 발생했습니다: {e}")

    try:
        # --- [1단계] B2B 사이트 상세 수집 가동 ---
        print("\n" + "="*50)
        print("🌐 1단계: B2B 웹사이트 상세 가격 수집 시작")
        print("="*50)
        
        for site_name, info in SITES.items():
            acc = accounts.get(site_name)
            if not acc:
                print(f"⏩ [{site_name}] 계정 정보가 없어 건너뜁니다.")
                continue
            
            # 사이트 로그인 시도
            if collector.login(site_name, info['login_url'], acc['u'], acc['p'], info['selectors']):
                # 디렉터님 시트에서 가져온 키워드별로 검색
                for kw in keywords:
                    collector.collect_by_search(
                        site_name, 
                        info['list_url'], 
                        info['domain'], 
                        info['product_selectors'], 
                        kw
                    )
                # 다음 사이트를 위해 쿠키 초기화
                collector.driver.delete_all_cookies()
            else:
                print(f"❌ [{site_name}] 로그인 실패로 수집을 건너뜁니다.")

        # --- [2단계] 타사 구글 시트 단가표 연동 가동 ---
        print("\n" + "="*50)
        print("📈 2단계: 구글 시트 단가표 데이터 연동 시작")
        print("="*50)
        
        for sheet_name, conf in GSHEETS.items():
            collector.collect_from_gsheet(sheet_name, conf, keywords)

        # --- [3단계] 최종 결과 저장 ---
        print("\n" + "="*50)
        collector.save_excel(PRICE_HISTORY_FILE)
        print("="*50)
        
    except Exception as e:
        print(f"❌ 전체 수집 공정 중 오류 발생: {e}")
        
    finally:
        # 브라우저 종료 및 로봇 퇴근
        collector.close()
        print("\n👋 모든 수집 작업이 성공적으로 종료되었습니다. 고생하셨습니다!")

if __name__ == "__main__":
    main()
