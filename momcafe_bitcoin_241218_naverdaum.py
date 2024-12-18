import requests
import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import time
import random
import json
import matplotlib.dates as mdates
import numpy as np
import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup

def get_post_dates_from_naver_api(url):
    """API에서 게시글 날짜를 추출하는 함수"""
    print(f"API 접근 시작: {url}")
    dates = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        print(f"API 접근 성공: {url}")
        data = response.json()
        
        if data and data.get("message") and data["message"].get("result") and data["message"]["result"].get("articleList"):
            article_list = data["message"]["result"]["articleList"]
            print(f"게시글 목록 개수: {len(article_list)}")
            for item in article_list:
                if item["type"] == "ARTICLE" and item.get("item") and item["item"].get("currentSecTime"):
                    date_text = item["item"]["currentSecTime"]
                    try:
                        date_obj = datetime.datetime.strptime(date_text, '%y.%m.%d.')
                        dates.append(date_obj)
                    except ValueError:
                        print(f"날짜 형식 변환 실패: {date_text}")
            print(f"추출된 날짜 개수: {len(dates)}")
        else:
            print("API 응답에서 게시글 목록을 찾을 수 없습니다.")
    except requests.exceptions.RequestException as e:
        print(f"API 접근 오류: {url}, {e}")
    except Exception as e:
        print(f"기타 오류 발생: {url}, {e}")
    return dates, data.get("message", {}).get("result", {}).get("nextRequestParameter")

def get_post_dates_from_daum_cafe(url, grpid, pagenum, last_article_num=None):
    """다음 카페에서 게시글 날짜를 추출하는 함수"""
    print(f"다음 카페 접근 시작: {url}")
    dates = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"다음 카페 접근 성공: {url}")
        soup = BeautifulSoup(response.text, 'html.parser')

        # 게시글 번호와 날짜 정보가 있는 태그를 찾습니다.
        article_rows = soup.select('table.bbsList tr')  # 게시글 행을 찾습니다.

        # 첫 번째 게시글 번호 추출 (마지막 페이지 판별용)
        first_article_num = None
        if article_rows:
            first_article_num_elem = article_rows[0].select_one('td.search_num')
            if first_article_num_elem:
                try:
                    first_article_num = int(first_article_num_elem.get_text(strip=True))
                except ValueError:
                    print(f"게시글 번호 추출 실패")
                    pass

        date_elements = soup.select('td.date')
        num_date_elements = len(date_elements)
        print(f"게시글 날짜 요소 개수: {num_date_elements}")

        for element in date_elements:
            date_text = element.get_text(strip=True)
            try:
                date_text = date_text.rstrip('.')
                # HH:MM 형식 처리
                if len(date_text) == 5:
                    today = datetime.date.today()
                    date_obj = datetime.datetime.strptime(f"{today.year}.{today.month}.{today.day} {date_text}", '%Y.%m.%d %H:%M')
                elif len(date_text) == 8:
                    date_obj = datetime.datetime.strptime(date_text, '%y.%m.%d')
                elif len(date_text) == 9:
                    date_obj = datetime.datetime.strptime(date_text, '%y.%m.%d')
                else:
                    date_obj = datetime.datetime.strptime(date_text, '%Y.%m.%d')
                dates.append(date_obj)
            except ValueError:
                print(f"날짜 형식 변환 실패: {date_text}")
        print(f"추출된 날짜 개수: {len(dates)}")

        # 다음 페이지 번호를 찾습니다.
        next_page_params = None
        paging_area = soup.select_one('div.paging')

        if paging_area:
            # 마지막 페이지 번호 추출
            last_page_link = paging_area.select('a.num_box')[-1]
            last_page_num = int(last_page_link.text) if last_page_link else None

            # 현재 페이지 번호(pagenum)와 마지막 페이지 번호가 같으면 종료
            if pagenum == last_page_num:
                print("여기가 마지막 페이지입니다.")
            # 마지막 페이지가 아닌경우 페이지번호+1 하여 계속 조회
            else:
                next_page_params = {
                    "grpid": grpid,
                    "pagenum": pagenum + 1
                }

    except requests.exceptions.RequestException as e:
        print(f"다음 카페 접근 오류: {url}, {e}")
    except Exception as e:
        print(f"기타 오류 발생: {url}, {e}")
    return dates, next_page_params, first_article_num

def get_bitcoin_prices_yfinance(start_date, end_date):
    """yfinance 라이브러리를 사용하여 비트코인 가격 데이터를 가져오는 함수"""
    print("yfinance를 사용하여 비트코인 가격 데이터 가져오기 시작")
    try:
        ticker = yf.Ticker("BTC-USD")
        data = ticker.history(start=start_date, end=end_date, interval="1wk")
        prices = data['Close'].to_dict()

        # datetime 객체로 변환 및 시간 정보 제거, 주 시작 날짜로 변경
        prices = {date.replace(tzinfo=None) - datetime.timedelta(days=date.weekday()): price for date, price in prices.items()}
        print("yfinance를 사용하여 비트코인 가격 데이터 가져오기 완료")
        # print(prices)
        return prices
    except Exception as e:
        print(f"yfinance 오류: {e}")
        return {}

def group_by_week(dates):
    """날짜 목록을 주차별로 그룹화하는 함수"""
    print("주차별 그룹화 시작")
    weekly_counts = defaultdict(int)
    for date in dates:
        # 해당 날짜가 속한 주의 시작 날짜 계산
        week_start = date - datetime.timedelta(days=date.weekday())
        weekly_counts[week_start] += 1
    print("주차별 그룹화 완료")
    return weekly_counts

def plot_weekly_counts(weekly_counts, bitcoin_prices, min_date):
    """주차별 게시글 수와 비트코인 가격을 차트로 그리는 함수"""
    print("차트 생성 시작")
    if not bitcoin_prices:
        print("비트코인 가격 데이터가 없습니다.")
        return

    # 비트코인 가격 데이터의 시작일과 종료일을 기준으로 모든 주차를 생성합니다.
    start_date = min(bitcoin_prices.keys())
    end_date = max(bitcoin_prices.keys())
    all_weeks = pd.date_range(start=start_date, end=end_date, freq='W-MON')

    # 비트코인 가격 데이터 보간
    price_df = pd.DataFrame.from_dict(bitcoin_prices, orient='index', columns=['price'])
    price_df = price_df.reindex(all_weeks)
    price_df = price_df.interpolate(method='linear')
    price_dates = price_df.index.tolist()
    prices = price_df['price'].tolist()

    # 게시글 데이터의 주차별 개수를 조정합니다.
    counts = [weekly_counts.get(week, 0) for week in all_weeks]  # 없는 주에는 0을 할당

    print("차트 데이터 확인:")
    # print("모든 주차:", all_weeks)
    # print("게시글 수:", counts)
    # print("가격 주차:", price_dates)
    # print("가격:", prices)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 게시글 수 막대 그래프
    ax1.bar(all_weeks, counts, width=5, label='Post Count', color='skyblue')
    ax1.set_xlabel('Week Start Date')
    ax1.set_ylabel('Number of Posts', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')

    # 비트코인 가격 꺾은선 그래프
    ax2 = ax1.twinx()
    ax2.plot(price_dates, prices, color='orange', label='Bitcoin Price')
    ax2.set_ylabel('Bitcoin Price', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    # x축 날짜 형식 지정 및 간격 조절 (월별로 표시)
    ax1.xaxis.set_major_locator(mdates.MonthLocator())  # 매월 1일만 표시
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # 날짜 형식 변경

    # x축 레이블 회전, 가운데 정렬, 폰트 크기 조절
    ax1.tick_params(axis='x', rotation=90, labelsize=8)

    fig.tight_layout()

    # 범례 표시
    fig.legend(loc="upper left", bbox_to_anchor=(0, 1), bbox_transform=fig.transFigure)

    plt.show()
    print("차트 생성 완료")

if __name__ == "__main__":
    naver_base_url = "https://apis.naver.com/cafe-web/cafe-mobile/CafeMobileWebArticleSearchListV4"
    naver_cafe_ids = [
        14793916,  # 줌마렐라(마산맘)
        14042965,  # 강남엄마 목동엄마
        12448054,  # 고.우.리 일산아지매
        10094499,  # 맘스홀릭 베이비
        22897837,  # 동탄맘들 모여라
        22897837,  # 인천아띠아모 (동탄맘과 동일한 ID)
        13276223,  # 수원맘모여라
        11306253,  # 파주맘
        18391491,  # 광명맘
        15194989,  # 분따
        12165814,  # 운정맘
        18376548,  # 대전세종맘스베이비
        24361059,  # 세종맘카페
        12182370,  # 도담도담대전맘
        27069107,  # 청주맘블리
        26217677,  # 천안아산줌마렐라
        24000254,  # 대구맘365
        23604018,  # 구미맘수다방
        26025763,   # 광주맘
        # 10912875, # 여우야
        # 10050813, # 파우더룸

    ]
    
    daum_base_url = "https://cafe.daum.net/_c21_/cafesearch"
    daum_cafe_ids = [
        "ut",  # 맘스카페
        "SqBK", # 대구맘
        "YfAr", # 부산맘
        # "1IHuH", # 여성시대
    ]
    
    all_dates = []
    min_date = datetime.datetime.now() # 게시글 데이터의 최소 날짜를 저장할 변수 초기화

    # 네이버 카페 게시글 날짜 수집
    for cafe_id in naver_cafe_ids:
        query_params = {
            "cafeId": cafe_id,
            "query": "비트코인",
            "searchBy": 1,
            "sortBy": "date",
            "page": 1,
            "perPage": 1000,
            "adUnit": "MW_CAFE_BOARD",
            "lastItemIndex": 0,
            "lastAdIndex": 0,
            "ad": "true"
        }
        
        next_page_params = None
        while True:
            url = naver_base_url + "?" + "&".join([f"{k}={v}" for k, v in query_params.items()])
            if next_page_params:
                url += "&" + "&".join([f"{k}={v}" for k, v in next_page_params.items()])
            
            time.sleep(random.uniform(1.1, 3.5))
            dates, next_page_params = get_post_dates_from_naver_api(url)
            all_dates.extend(dates)
            
            if not next_page_params or not next_page_params.get("page"):
                break
            query_params["page"] = next_page_params["page"]
            query_params["lastAdIndex"] = next_page_params.get("lastAdIndex", -1)
            query_params["lastItemIndex"] = next_page_params.get("lastItemIndex", -1)

    # 다음 카페 게시글 날짜 수집
    for grpid in daum_cafe_ids:
        pagenum = 1
        last_article_num = None  # 이전 페이지의 마지막 게시글 번호를 저장하기 위한 변수
        while True:
            url = f"{daum_base_url}?grpid={grpid}&fldid=&pagenum={pagenum}&listnum=100&item=onlytitle&head=&query=%EB%B9%84%ED%8A%B8%EC%BD%94%EC%9D%B8&attachfile_yn=&media_info=&viewtype=tit&searchPeriod=all&sorttype=0&nickname="

            time.sleep(random.uniform(1.1, 3.5))
            dates, next_page_params, first_article_num = get_post_dates_from_daum_cafe(url, grpid, pagenum, last_article_num)
            all_dates.extend(dates)

            if next_page_params is None:
                print(f"'{grpid}' 카페 크롤링 완료")
                break

            last_article_num = first_article_num  # 이전 페이지의 마지막 게시글 번호 업데이트
            pagenum += 1  # pagenum 1 증가

    if all_dates:
        min_date = min(all_dates)
    else:
        print("게시글 데이터가 없습니다.")
        exit()
    
    end_date = datetime.datetime.now()
    bitcoin_prices = get_bitcoin_prices_yfinance(min_date, end_date)
    
    print(f"전체 추출된 날짜 개수: {len(all_dates)}")

    weekly_counts = group_by_week(all_dates)
    plot_weekly_counts(weekly_counts, bitcoin_prices, min_date)