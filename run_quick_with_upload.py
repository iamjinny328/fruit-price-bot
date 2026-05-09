# -*- coding: utf-8 -*-
"""
B2B 가격 수집 실행기 (메인 루프)
"""
from price_collector import B2BPriceCollector
from config import SITES, FILTER_KEYWORDS, PRICE_HISTORY_FILE
from datetime import datetime

def main():
    collector = B2BPriceCollector()
    
    try:
        print("="*50)
        print("🚀 B2B 가격 비교 자동 수집 프로세스 시작")
        print("="*50)

        for site_name, config in SITES.items():
            if not config['accounts']: continue
            
            # 계정 등급별로 수집
            for acc in config['accounts']:
                success = collector.login(
                    site_name=site_name,
                    login_url=config['login_url'],
                    username=acc['user'],
                    password=acc['pw'],
                    selectors=config['selectors']
                )
                
                if success:
                    for keyword in FILTER_KEYWORDS:
                        print(f"🔍 [{site_name}] '{keyword}' 수집 중...")
                        collector.collect_by_search(
                            site_name=site_name,
                            list_url=config['list_url'],
                            domain=config['domain'],
                            selectors=config['product_selectors'],
                            keyword=keyword,
                            account_grade=acc['grade']
                        )
                    # 다른 계정 로그인을 위한 세션 초기화
                    collector.driver.delete_all_cookies()

        collector.save_excel(PRICE_HISTORY_FILE)

    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
    finally:
        collector.close()
        print("\n👋 모든 수집 작업을 안전하게 종료합니다.")

if __name__ == "__main__":
    main()