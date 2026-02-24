import os
import requests
import google.generativeai as genai
import smtplib
import yfinance as yf
from email.message import EmailMessage
from datetime import datetime

# 깃허브 Secrets
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MY_EMAIL = os.environ.get('MY_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

def get_detailed_data():
    """금리 및 주요 기업 주가 수치를 정밀하게 수집합니다."""
    tickers = {"10Y_Treasury": "^TNX", "NVDA": "NVDA", "MSFT": "MSFT", "TSMC": "TSM", "Samsung": "005930.KS"}
    data_results = {}
    for name, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="2d")
            if len(h) >= 2:
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2]
                change = curr - prev
                pct = (change / prev) * 100
                data_results[name] = f"{curr:.2f} ({pct:+.2f}%)"
        except:
            data_results[name] = "Data N/A"
    return data_results

def run():
    try:
        # 1. 객관적 수치 수집
        market_stats = get_detailed_data()
        
        # 2. 기업 공시/내부자 정보 위주 뉴스 검색
        query = "(Nvidia OR Samsung OR TSMC) AND (insider selling OR disclosure OR SEC filing OR earnings)"
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        articles = res.get('articles', [])[:8]
        news_context = "\n".join([f"- [{a['source']['name']}] {a['title']}" for a in articles])

        # 3. AI 분석 (냉혹한 퀀트 애널리스트 모드)
        genai.configure(api_key=GEMINI_API_KEY)
        # 생성 설정을 통해 창의성을 배제하고 팩트 위주로 강제
        generation_config = {"temperature": 0.0, "top_p": 1, "max_output_tokens": 2048}
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        
        prompt = f"""
        당신은 숫자로만 말하는 15년차 시니어 퀀트 애널리스트입니다. 
        보고서에서 '격언', '훈계', '개인적 조언'은 모두 쓰레기통에 버리십시오.

        [금지 사항 - 위반 시 해고]
        - '어르신', '65세', '노후', '신중한', '현명한', '삶의 지혜' 등 감성적 단어 일절 사용 금지.
        - 추상적인 문장(예: ~하면 좋습니다) 금지. 

        [작성 형식]
        1. 시장 수치 요약 (표 형식): 금리 및 주요 종목 등락률 나열.
        2. 주요 공시 및 뉴스 (팩트): 수집된 뉴스 중 구체적 수치(매도액, 매출액, 지분율)가 포함된 것 위주 분석.
        3. 내부자 거래 및 지분 변동: SEC 공시나 내부자 매도 현황에 대한 수치적 기록.
        4. 데이터 기반 리스크: 감정이 아닌 지표(금리 역전, 지지선 붕괴 등)로 본 리스크 분석.

        [입력 데이터]
        - 시장 수치: {market_stats}
        - 최신 뉴스 동향:
        {news_context}
        """
        
        response = model.generate_content(prompt)
        report = response.text

        # 4. 메일 전송
        msg = EmailMessage()
        msg.set_content(report)
        msg['Subject'] = f"📊 [Fact Check] {datetime.now().strftime('%Y-%m-%d')} AI/반도체 데이터 리포트"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ 퀀트 리포트 발송 성공!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run()
