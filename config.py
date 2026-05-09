# -*- coding: utf-8 -*-
"""
B2B 가격 수집 설정 파일 (최종 통합 버전)
"""
import os

# ========================================
# 1. 사이트 기본 정보 (AdminPlus 계열 고정 데이터)
# ========================================
SITES = {
    '팡이농장': {'login_url': 'https://jaehwan0330.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://jaehwan0330.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'jaehwan0330.adminplus.co.kr'},
    '최고집': {'login_url': 'https://zain0401.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://zain0401.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'zain0401.adminplus.co.kr'},
    '늘푸른우리': {'login_url': 'https://hwanggs3.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://hwanggs3.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'hwanggs3.adminplus.co.kr'},
    '팜허브': {'login_url': 'https://priceit.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://priceit.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'priceit.adminplus.co.kr'},
    '덤덤몰': {'login_url': 'https://dumdummall.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://dumdummall.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'dumdummall.adminplus.co.kr'},
    '마니팜': {'login_url': 'https://mp3462.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://mp3462.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'mp3462.adminplus.co.kr'},
    '산지이음': {'login_url': 'https://orangec.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://orangec.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'orangec.adminplus.co.kr'},
    '농부를 찾아서': {'login_url': 'https://ongreen.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://ongreen.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'ongreen.adminplus.co.kr'},
    '캄뮤유통': {'login_url': 'https://ehrtnfl20002.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://ehrtnfl20002.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'ehrtnfl20002.adminplus.co.kr'},
    '김통깨(산지직쏭)': {'login_url': 'https://sanji0370.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://sanji0370.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'sanji0370.adminplus.co.kr'},
    '팜플로우': {'login_url': 'https://farmflow.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://farmflow.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'farmflow.adminplus.co.kr'},
    '더그린': {'login_url': 'https://gl1248.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'list_url': 'https://gl1248.adminplus.co.kr/partner/?mod=product&actpage=prt.list', 'domain': 'gl1248.adminplus.co.kr'},
}

# 공통 셀렉터 설정 자동 주입
for s in SITES:
    SITES[s]['selectors'] = {'username': '#memid', 'password': '#admpwd', 'login_button': 'button[type="submit"]'}
    SITES[s]['product_selectors'] = {'item_container': 'div[onclick^="prtView"]', 'product_name': '.pname'}
    SITES[s]['accounts'] = []

# ========================================
# 2. 계정 정보 지능형 로드 (accounts.txt 연동)
# ========================================
common_account = None
specific_accounts = {}

try:
    with open('accounts.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                site, user, pw, grade = parts[0], parts[1], parts[2], parts[3]
                if site.upper() == 'ALL':
                    common_account = {'user': user, 'pw': pw, 'grade': grade}
                else:
                    if site not in SITES: continue
                    if site not in specific_accounts: specific_accounts[site] = []
                    specific_accounts[site].append({'user': user, 'pw': pw, 'grade': grade})

    for site_name in SITES:
        if site_name in specific_accounts:
            SITES[site_name]['accounts'] = specific_accounts[site_name]
        elif common_account:
            SITES[site_name]['accounts'] = [common_account]
    print(f"✅ 계정 설정 로드 완료")
except Exception as e:
    print(f"⚠️ 'accounts.txt' 로드 중 오류: {e}")

# ========================================
# 3. 수집 옵션 및 파일 경로
# ========================================
try:
    with open('keywords.txt', 'r', encoding='utf-8') as f:
        FILTER_KEYWORDS = [line.strip() for line in f if line.strip()]
except:
    FILTER_KEYWORDS = ['사과', '배', '복숭아']

MAX_PAGES = 3
PRICE_HISTORY_FILE = '가격이력.xlsx'