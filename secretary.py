import os
import requests
import google.generativeai as genai
import smtplib
import yfinance as yf
from email.message import EmailMessage
from datetime import datetime, timedelta

# 깃허브 Secrets 설정
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MY_EMAIL = os.environ.get('MY_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

def get_treasury_yields():
    """미국 10년물 국채 금리 데이터를 가져옵니다."""
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="2d")
        if len(hist) >= 2:
            today_yield = hist['Close'].iloc[-1]
            yesterday_yield = hist['Close'].iloc[-2]
            return today_yield, yesterday_yield
        return None, None
    except:
        return None, None

def run():
    try:
        # 1. 미국 국채 금리 수집
        today_y, yesterday_y = get_treasury_yields()
        yield_info = f"어제: {yesterday_y:.2f}%, 오늘: {today_y:.2f}%" if today_y else "데이터 불러오기 실패"

        # 2. 주요 기업 타겟 뉴스 수집 (NVIDIA, Google, MS, Samsung, SK, TSMC 등)
        target_companies = "Nvidia, Google, Microsoft, Samsung Electronics, SK Hynix, TSMC"
        query = f"({target_companies}) AND (earnings OR disclosure OR insider selling OR AI analyst)"
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        
        res = requests.get(url).json()
        articles = res.get('articles', [])[:10]
        news_context = "\n".join([f"- {a['title']} (출처: {a['source']['name']})" for a in articles])

        # 3. Gemini AI 분석 (스마트 투자자 페르소나 주입)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash') # 최신 모델 사용 권장
        
        prompt = f"""
        당신은 세계 최고의 금융 분석가이자 신중하고 스마트한 투자 전략가입니다.
        다음 정보를 바탕으로 전문적인 '글로벌 반도체 & AI 산업 심층 보고서'를 작성하세요.

        [분석 지침]
        - 절대 '어르신', '65세' 등 개인 신상이나 특정 연령대를 언급하지 마십시오.
        - 대상 독자는 매우 냉철하고 지적인 전문 투자자입니다.
        - 언어는 한국어로 작성하되, 전문 금융 용어를 적절히 사용하십시오.

        [데이터 입력]
        1. 국채 금리 상황: {yield_info}
        2. 관련 주요 뉴스 요약:
        {news_context}

        [보고서 필수 포함 내용]
        1. **미국 중심 반도체/AI 뉴스 요약 (3가지 핵심)**: 수집된 뉴스 중 가장 파괴력 있는 3가지를 골라 깊이 있게 분석하십시오.
        2. **금리 분석 및 전망**: 어제와 오늘의 금리 변화가 기술주 및 반도체 기업 자금 조달에 미칠 영향과 향후 전망을 서술하십시오.
        3. **기업별 주요 공시 및 전략 분석**: 엔비디아, 삼성, TSMC 등 주요 기업의 최근 행보와 공시 내용을 구체적으로 짚어주십시오.
        4. **내부자 거래 및 지분 변동**: 주요 임원들의 주식 매도 현황과 그 속에 숨겨진 의미를 분석하십시오.
        5. **석학 및 애널리스트 견해**: 최근 저명한 교수나 분석가들이 발표한 기술 전망 및 회의 내용을 요약하여 투자 포인트로 제시하십시오.

        결론은 항상 신중하고 보수적인 관점에서의 투자 조언으로 마무리하십시오.
        """
        
        response = model.generate_content(prompt)
        report = response.text

        # 4. 메일 전송
        msg = EmailMessage()
        msg.set_content(report)
        msg['Subject'] = f"📊 [Smart Investor] {datetime.now().strftime('%Y-%m-%d')} AI/반도체 심층 전략 보고서"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ 고도화된 리포트 발송 성공!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run()

