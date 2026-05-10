# -*- coding: utf-8 -*-
from price_collector import B2BPriceCollector
from config import SITES, GSHEETS, PRICE_HISTORY_FILE, KEYWORD_MASTER_URL
import os

def main():
    # 수집기 엔진 기동
    collector = B2BPriceCollector()
    
    # 1. 키워드 로드 (디렉터님의 마스터 구글 시트에서 읽기)
    keywords = collector.load_keywords_from_gsheet(KEYWORD_MASTER_URL)
    
    if not keywords:
        print("❌ 키워드를 불러오지 못했습니다. 프로그램을 종료합니다.")
        collector.close()
        return

    # 2. 계정 정보 로드 (accounts.txt 분석)
    # 형식: [사이트명, 아이디, 비밀번호, 등급]
    accounts = {}
    try:
        if os.path.exists('accounts.txt'):
            with open('accounts.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if ',' not in line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    
                    if len(parts) >= 3:
                        site_key = parts[0]
                        user_id = parts[1]
                        user_pw = parts[2]
                        # 4번째 칸에 등급(VIP 등)이 있으면 읽고, 없으면 '일반'으로 처리
                        grade = parts[3] if len(parts) > 3 else "일반"
                        
                        if site_key.upper() == 'ALL':
                            for s in SITES:
                                accounts[s] = {'u': user_id, 'p': user_pw, 'g': grade}
                        elif site_key in SITES:
                            accounts[site_key] = {'u': user_id, 'p': user_pw, 'g': grade}
        else:
            print("⚠️ accounts.txt 파일이 없어 수집을 진행할 수 없습니다.")
    except Exception as e:
        print(f"⚠️ 계정 파일을 읽는 중 오류 발생: {e}")

    try:
        # --- [1단계] B2B 사이트 상세 수집 (어드민 기반) ---
        print("\n" + "="*60)
        print("🌐 1단계: B2B 어드민 사이트 가격 수집 시작")
        print("="*60)
        
        for site_name, info in SITES.items():
            acc = accounts.get(site_name)
            if not acc:
                print(f"⏩ [{site_name}] 설정된 계정이 없습니다. 수집을 건너뜁니다.")
                continue
            
            # 로그인 시도
            if collector.login(site_name, info['login_url'], acc['u'], acc['p'], info['selectors']):
                # 로그인한 계정의 등급(VIP 등)을 포함하여 검색 수집 실행
                for kw in keywords:
                    collector.collect_by_search(
                        site_name, 
                        info['list_url'], 
                        info['domain'], 
                        info['product_selectors'], 
                        kw,
                        acc['g'] # 등급 정보 전달
                    )
                # 사이트 간 데이터 꼬임 방지를 위해 쿠키 삭제
                collector.driver.delete_all_cookies()
            else:
                print(f"❌ [{site_name}] 로그인 실패. 아이디/비번 혹은 보안 설정을 확인하세요.")

        # --- [2단계] 타사 구글 시트 단가표 연동 ---
        print("\n" + "="*60)
        print("📈 2단계: 외부 구글 시트 단가표 데이터 연동 시작")
        print("="*60)
        
        for sheet_name, conf in GSHEETS.items():
            collector.collect_from_gsheet(sheet_name, conf, keywords)

        # --- [3단계] 최종 데이터 저장 ---
        print("\n" + "="*60)
        collector.save_excel(PRICE_HISTORY_FILE)
        print("="*60)
        
    except Exception as e:
        print(f"❌ 작업 중 심각한 오류 발생: {e}")
        
    finally:
        # 모든 작업 완료 후 브라우저 종료
        collector.close()
        print("\n👋 수집 공정이 모두 끝났습니다. 대시보드를 확인해 보세요!")

if __name__ == "__main__":
    main()
