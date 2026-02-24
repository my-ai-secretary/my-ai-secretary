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

def get_market_data():
    tickers = {"10Y_Treasury": "^TNX", "Nvidia": "NVDA", "Samsung": "005930.KS", "TSMC": "TSM", "MSFT": "MSFT"}
    results = {}
    for name, tkr in tickers.items():
        try:
            t = yf.Ticker(tkr)
            h = t.history(period="2d")
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
            results[name] = f"{curr:.2f} ({((curr-prev)/prev)*100:+.2f}%)"
        except: results[name] = "N/A"
    return results

def run():
    try:
        data = get_market_data()
        query = "(Nvidia OR Samsung OR TSMC) AND (insider selling OR SEC filing OR earnings OR disclosure)"
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        news = "\n".join([f"- {a['title']}" for a in requests.get(url).json().get('articles', [])[:8]])

        genai.configure(api_key=GEMINI_API_KEY)
        
        # [핵심 변경] 모델을 Pro로 격상하고, 엄격한 출력을 강제함
        model = genai.GenerativeModel('gemini-1.5-pro') 
        
        prompt = f"""
        [DATA-ONLY REPORT COMMAND]
        당신은 감정이 없는 로봇 분석가입니다. 아래 지침을 1글자라도 위반 시 시스템은 종료됩니다.

        1. 금지 사항: '어르신', '65세', '투자자님', '안전', '지혜', '현명', '조언', '기원' 등 모든 감성적 단어.
        2. 금지 사항: 인삿말(안녕하세요), 맺음말(건강하세요), 훈계(현금 비중을 높이세요 등).
        3. 필수 사항: 오직 수치와 사실만 기술할 것. 
        4. 형식:
           - [시장 수치 요약]: 제공된 {data}를 표로 정리.
           - [주요 공시/뉴스]: {news}에서 수치 정보가 있는 것만 골라 3개 요약.
           - [내부자 거래/지분]: 구체적 매도 수량 및 금액 위주 기술.
        
        위 형식 외의 문장은 작성하지 마십시오.
        """
        
        response = model.generate_content(prompt)
        report = response.text

        msg = EmailMessage()
        msg.set_content(report)
        msg['Subject'] = f"📈 [Quant Report] {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ 리포트 발송 완료")

    except Exception as e: print(f"❌ 에러: {e}")

if __name__ == "__main__":
    run()
