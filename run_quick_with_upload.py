# -*- coding: utf-8 -*-
from price_collector import B2BPriceCollector
from config import SITES, GSHEETS, PRICE_HISTORY_FILE
import os

def main():
    # 1. 키워드 목록 로드 (keywords.txt 파일 읽기)
    try:
        with open('keywords.txt', 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        print(f"✅ 수집 키워드 로드 완료: {', '.join(keywords)}")
    except Exception as e:
        print(f"⚠️ 키워드 파일을 읽을 수 없어 기본값(사과, 배)을 사용합니다: {e}")
        keywords = ['사과', '배']

    # 2. 계정 정보 로드 (accounts.txt 파일 읽기)
    accounts = {}
    try:
        with open('accounts.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ',' not in line or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    site_key, user, pw = parts[0], parts[1], parts[2]
                    # ALL 계정이면 모든 사이트에 할당, 아니면 특정 사이트에만 할당
                    if site_key.upper() == 'ALL':
                        for s in SITES:
                            accounts[s] = {'u': user, 'p': pw}
                    elif site_key in SITES:
                        accounts[site_key] = {'u': user, 'p': pw}
        print(f"✅ 접속 계정 정보 로드 완료 (대상 사이트: {len(accounts)}곳)")
    except Exception as e:
        print(f"⚠️ 계정 파일을 읽는 중 오류가 발생했습니다: {e}")

    # 3. 수집 엔진 가동
    collector = B2BPriceCollector()
    
    try:
        # --- [1단계] B2B 사이트 로그인 및 상세 검색 수집 ---
        print("\n" + "="*50)
        print("🌐 1단계: B2B 웹사이트 상세 가격 수집 시작")
        print("="*50)
        
        for site_name, info in SITES.items():
            acc = accounts.get(site_name)
            if not acc:
                print(f"⏩ [{site_name}] 계정 정보가 없어 건너뜁니다.")
                continue
            
            # 로그인 시도
            if collector.login(site_name, info['login_url'], acc['u'], acc['p'], info['selectors']):
                # 키워드별로 검색 실행
                for kw in keywords:
                    collector.collect_by_search(
                        site_name, 
                        info['list_url'], 
                        info['domain'], 
                        info['product_selectors'], 
                        kw
                    )
                # 다음 사이트 접속을 위해 쿠키 삭제
                collector.driver.delete_all_cookies()
            else:
                print(f"❌ [{site_name}] 로그인 실패로 인해 수집을 진행할 수 없습니다.")

        # --- [2단계] 구글 시트 단가표 연동 수집 ---
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
        print(f"❌ 수집 프로세스 도중 예상치 못한 오류 발생: {e}")
        
    finally:
        # 브라우저 종료
        collector.close()
        print("\n👋 모든 작업을 마치고 로봇이 퇴근합니다. 수고하셨습니다!")

if __name__ == "__main__":
    main()
