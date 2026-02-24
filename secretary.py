import os
import requests
import google.generativeai as genai
import smtplib
import yfinance as yf
from email.message import EmailMessage
from datetime import datetime

# 깃허브 Secrets 설정
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MY_EMAIL = os.environ.get('MY_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

def get_market_data():
    """국채 금리 및 주요 지수 수치를 가져옵니다."""
    try:
        # 미국 10년물 국채 금리 (^TNX)
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="2d")
        if len(hist) >= 2:
            today_y = hist['Close'].iloc[-1]
            yesterday_y = hist['Close'].iloc[-2]
            change = today_y - yesterday_y
            return today_y, yesterday_y, change
        return None, None, None
    except:
        return None, None, None

def run():
    try:
        # 1. 객관적 수치 데이터 수집 (금리)
        today_y, yesterday_y, change = get_market_data()
        yield_data = f"현재: {today_y:.3f}%, 전일 대비: {change:+.3f}%p" if today_y else "수치 데이터 확보 실패"

        # 2. 주요 기업 타겟 뉴스 수집
        companies = "Nvidia, Google, Microsoft, Samsung Electronics, SK Hynix, TSMC"
        query = f"({companies}) AND (financial result OR disclosure OR insider trading OR guidance)"
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        
        res = requests.get(url).json()
        articles = res.get('articles', [])[:10]
        news_context = "\n".join([f"[{a['source']['name']}] {a['title']}" for a in articles])

        # 3. Gemini AI 분석 (냉철한 데이터 분석가 페르소나)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        당신은 데이터 중심의 냉철한 퀀트 애널리스트입니다. 
        다음 입력 데이터를 바탕으로 '객관적 수치 기반 전략 보고서'를 작성하십시오.

        [수행 지침 - 절대 준수]
        1. 모든 형태의 '투자 격언', '교훈적 문구', '훈계조 표현'을 엄격히 금지합니다.
        2. '어르신', '나이', '신상'과 관련된 어떠한 단어도 언급하지 마십시오.
        3. 모든 분석은 제공된 수치와 사실에 근거해야 하며, 감정적인 형용사를 배제하십시오.
        4. 추상적인 조언 대신 데이터에 기반한 향후 전망과 리스크를 논리적으로 서술하십시오.

        [데이터 입력]
        - 미 10년물 국채 금리 변동: {yield_data}
        - 주요 기업 최신 동향:
        {news_context}

        [보고서 구성 요소]
        1. 핵심 수치 요약: 금리 및 주요 기업 뉴스 중 수치적 의미가 큰 사건 3가지 요약.
        2. 금리 변동 분석: 금리 변동 폭이 반도체 기업의 밸류에이션 및 자금 조달 비용에 미치는 정량적 영향.
        3. 기업 공시 및 지분 변동: 주요 인사들의 매도 수량, 공시된 실적 수치 등 객관적 사실 기록 및 분석.
        4. 전문가 및 기관 견해: 애널리스트들의 목표주가 하향/상향 수치 및 구체적인 기술적 발표 내용 요약.
        5. 결론: 수치 분석 결과에 따른 단기적 대응 전략.
        """
        
        response = model.generate_content(prompt)
        report = response.text

        # 4. 메일 전송
        msg = EmailMessage()
        msg.set_content(report)
        msg['Subject'] = f"📈 [Data Report] {datetime.now().strftime('%Y-%m-%d')} 시장 분석"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ 데이터 중심 보고서 발송 성공!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run()
