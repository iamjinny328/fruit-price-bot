# -*- coding: utf-8 -*-

# 1. B2B 어드민 사이트 목록
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

for s in SITES:
    SITES[s]['selectors'] = {'username': '#memid', 'password': '#admpwd', 'login_button': 'button[type="submit"]'}
    SITES[s]['product_selectors'] = {'item_container': 'div[onclick^="prtView"]', 'product_name': '.pname'}

# 2. 공유 구글 시트 목록 (지능형 탭 탐색: gid가 없어도 알아서 찾아냅니다)
GSHEETS = {
    '업체_p0WM': 'https://docs.google.com/spreadsheets/d/1p0WM4X2JztS1LfGKVdUXd3GTvBJJGYPNO0ya8ihfns4',
    '농협경제지주': 'https://docs.google.com/spreadsheets/d/1WmoBoJJEgjyTNns-y4ditymdLT2Ygp0NvBG0nfL8a3g',
    '김통깨(통합)': 'https://docs.google.com/spreadsheets/d/1JUx1b2nxxGyl1SR5hITWfFLbjmIc_53D',
    '제이비티엠': 'https://docs.google.com/spreadsheets/d/1g0Bxmz773DqPjCfYgBNyBtlYKxYuLJYY2zasqiC5u7Y',
    '업체_bFfY': 'https://docs.google.com/spreadsheets/d/1bFfYmNNzPpIztK6_AD918Hu7s3JvaqkGGlwfIi6LxqY',
    '웰그린푸드': 'https://docs.google.com/spreadsheets/d/14DLy78orKYHYlmQOuO7Efg2OL-yvwjgo4bOpacw5vZ4'
}

# 3. 마스터 키워드 관리 시트 주소
KEYWORD_MASTER_URL = 'https://docs.google.com/spreadsheets/d/17IYejCC_YsfjXrjqh0AZ_SQMu3_sQWsbGopJw3qvNyE/edit'

PRICE_HISTORY_FILE = '가격이력.xlsx'
