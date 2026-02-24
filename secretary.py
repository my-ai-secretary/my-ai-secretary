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

def get_quantitative_data():
    """핵심 지표와 주가를 소수점 단위까지 정밀하게 가져옵니다."""
    assets = {
        "10Y_Treasury": "^TNX",
        "Nvidia": "NVDA",
        "Samsung_Elec": "005930.KS",
        "TSMC": "TSM",
        "Microsoft": "MSFT",
        "Alphabet": "GOOGL"
    }
    stats = {}
    for name, ticker in assets.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="2d")
            if len(h) >= 2:
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                stats[name] = f"Price: {curr:.2f} | Change: {diff:+.2f} ({pct:+.2f}%)"
        except:
            stats[name] = "Data Fetch Error"
    return stats

def run():
    try:
        # 1. 정량 데이터 수집
        raw_data = get_quantitative_data()

        # 2. 공시 및 수치 위주 뉴스 수집
        query = "(Nvidia OR Samsung OR TSMC) AND (insider selling OR SEC filing OR Q1 earnings OR revenue guidance)"
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        articles = res.get('articles', [])[:7]
        news_str = "\n".join([f"- [{a['source']['name']}] {a['title']}" for a in articles])

        # 3. AI 분석 (창의성 0, 팩트 100 모드)
        genai.configure(api_key=GEMINI_API_KEY)
        # Temperature를 0으로 설정하여 헛소리를 원천 차단합니다.
        model = genai.GenerativeModel('gemini-1.5-flash', 
                                      generation_config={"temperature": 0})
        
        prompt = f"""
        [시스템 명령: 당신은 숫자에 미친 퀀트 애널리스트입니다.]
        아래 지침을 어길 시 보고서는 폐기됩니다.
        
        1. 금지어: '어르신', '65세', '투자자님', '조언', '신중', '지혜', '은퇴', '안전'.
        2. 말투: '~함', '~임', '~분석됨' 식의 건조한 개조식 문체만 사용.
        3. 필수 포함: 모든 분석 문장에는 반드시 숫자(%, $, 원)가 포함되어야 함.
        4. 내용: 격언이나 교훈은 일절 배제하고 오직 데이터의 '상관계수'와 '변동성'만 논할 것.

        [데이터 소스]
        - 현재 시장 지표: {raw_data}
        - 주요 공시 뉴스: {news_str}

        [보고서 형식]
        # 1. 시장 지표 요약 (Table)
        # 2. 주요 기업 내부자 거래 및 공시 수치 분석 (Fact)
        # 3. 금리 변동에 따른 밸류에이션 하락/상승폭 계산 (Calculated)
        # 4. 결론 (Data-driven only)
        """
        
        response = model.generate_content(prompt)
        report = response.text

        # 4. 메일 전송
        msg = EmailMessage()
        msg.set_content(report)
        msg['Subject'] = f"📊 [HARD DATA] {datetime.now().strftime('%Y-%m-%d')} 시장 수치 리포트"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ 데이터 리포트 발송 완료!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run()
