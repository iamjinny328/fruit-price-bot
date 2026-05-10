# -*- coding: utf-8 -*-
from price_collector import B2BPriceCollector
from config import SITES, GSHEETS, PRICE_HISTORY_FILE, KEYWORD_MASTER_URL
import os

def main():
    print("📢 과일 가격 통합 수집 로봇 가동 (하이브리드 & 지능형 탐색 모드)")
    collector = B2BPriceCollector()
    
    # 1. 마스터 키워드 로드
    keywords = collector.load_keywords_from_gsheet(KEYWORD_MASTER_URL)
    if not keywords:
        print("❌ 키워드 로드 실패. 마스터 시트 설정을 확인하세요.")
        collector.close(); return

    # 2. 계정 정보 로드 (accounts.txt)
    accounts = {}
    if os.path.exists('accounts.txt'):
        with open('accounts.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ',' not in line or line.startswith('#'): continue
                p = [parts.strip() for parts in line.split(',')]
                if len(p) >= 3:
                    grade = p[3] if len(p) > 3 else "일반"
                    if p[0].upper() == 'ALL':
                        for s in SITES: accounts[s] = {'u': p[1], 'p': p[2], 'g': grade}
                    elif p[0] in SITES:
                        accounts[p[0]] = {'u': p[1], 'p': p[2], 'g': grade}

    try:
        # --- 1단계: B2B 어드민 웹사이트 수집 (등급별 차등 수집) ---
        print("\n" + "="*50)
        print("🌐 1단계: B2B 사이트 가격 수집 시작")
        print("="*50)
        for site_name, info in SITES.items():
            acc = accounts.get(site_name)
            if not acc: continue
            
            if collector.login(site_name, info['login_url'], acc['u'], acc['p'], info['selectors']):
                collector.collect_site_data(site_name, info['list_url'], info['domain'], info['product_selectors'], keywords, acc['g'])
                collector.driver.delete_all_cookies()
                # 다음 사이트로 넘어가기 전 안전하게 휴식
                collector.human_wait(5, 10)

        # --- 2단계: 공유 구글 시트 지능형 수집 ---
        print("\n" + "="*50)
        print("📊 2단계: 공유 구글 시트 지능형 스캔 시작")
        print("="*50)
        for name, url in GSHEETS.items():
            collector.collect_from_gsheet_smart(name, url, keywords)

        # --- 3단계: 최종 데이터 저장 ---
        print("\n" + "="*50)
        collector.save_excel(PRICE_HISTORY_FILE)
        print("="*50)
        
    finally:
        collector.close()
        print("\n👋 모든 수집 공정이 안전하게 완료되었습니다.")

if __name__ == "__main__":
    main()
