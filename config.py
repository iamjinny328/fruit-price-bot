# -*- coding: utf-8 -*-

# 1. 수집 대상 B2B 사이트 기본 정보 (AdminPlus 계열)
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

# 공통 웹 선택자 설정
for s in SITES:
    SITES[s]['selectors'] = {'username': '#memid', 'password': '#admpwd', 'login_button': 'button[type="submit"]'}
    SITES[s]['product_selectors'] = {'item_container': 'div[onclick^="prtView"]', 'product_name': '.pname'}

# 2. 타사 구글 시트 단가표 연동 리스트
GSHEETS = {
    '김통깨(특가행사)': {'url': 'https://docs.google.com/spreadsheets/d/1WmoBoJJEgjyTNns-y4ditymdLT2Ygp0NvBG0nfL8a3g/export?format=csv&gid=1030436719', 'mapping': {'상품명': '상품명', '옵션명': '옵션', '공급가': '공급단가', '배송비': '택배사'}},
    '제이비티엠(농산물)': {'url': 'https://docs.google.com/spreadsheets/d/1g0Bxmz773DqPjCfYgBNyBtlYKxYuLJYY2zasqiC5u7Y/export?format=csv&gid=1410862921', 'mapping': {'상품명': '품목', '옵션명': '옵션명', '공급가': '일반공급가', '배송비': '운임비'}},
    '웰그린푸드(국산과일)': {'url': 'https://docs.google.com/spreadsheets/d/14DLy78orKYHYlmQOuO7Efg2OL-yvwjgo4bOpacw5vZ4/export?format=csv&gid=0', 'mapping': {'상품명': '제품명', '옵션명': '옵션', '공급가': '가장우측날짜'}},
    '업체(p0WM)': {'url': 'https://docs.google.com/spreadsheets/d/1p0WM4X2JztS1LfGKVdUXd3GTvBJJGYPNO0ya8ihfns4/export?format=csv&gid=1594213233', 'mapping': {'상품명': '상품명', '옵션명': '옵션', '공급가': '공급가'}},
    '업체(JUx1)': {'url': 'https://docs.google.com/spreadsheets/d/1JUx1b2nxxGyl1SR5hITWfFLbjmIc_53D/export?format=csv&gid=625002004', 'mapping': {'상품명': '품목', '옵션명': '규격', '공급가': '단가'}},
    '업체(bFfY)': {'url': 'https://docs.google.com/spreadsheets/d/1bFfYmNNzPpIztK6_AD918Hu7s3JvaqkGGlwfIi6LxqY/export?format=csv&gid=322594718', 'mapping': {'상품명': '상품명', '옵션명': '옵션', '공급가': '공급가'}}
}

# ⭐ 3. 디렉터님의 '마스터 조종 시트' (키워드 관리용)
KEYWORD_MASTER_URL = 'https://docs.google.com/spreadsheets/d/17IYejCC_YsfjXrjqh0AZ_SQMu3_sQWsbGopJw3qvNyE/export?format=csv&gid=0'

MAX_PAGES = 2
PRICE_HISTORY_FILE = '가격이력.xlsx'
