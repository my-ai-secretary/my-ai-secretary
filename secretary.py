import os
import requests
import google.generativeai as genai
import smtplib
from email.message import EmailMessage

# 깃허브 Secrets 금고에서 정보 가져오기
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MY_EMAIL = os.environ.get('MY_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

def run():
    try:
        # 1. 뉴스 수집
        query = "AI Bubble profitability Samsung Nvidia insider selling US Treasury yield"
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        articles = res.get('articles', [])[:5]
        news_text = "\n".join([f"- {a['title']}" for a in articles])

        if not news_text:
            news_text = "수집된 뉴스가 없습니다."

        # 2. AI 분석 (선생님 계정에서 확인된 최신 모델)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-3-flash-preview')
        
        prompt = f"""
        너는 베테랑 금융 전략가야. 다음 뉴스를 바탕으로 투자 보고서를 작성해줘.
        대상: 65세 개인투자자 (아주 쉽고 명확하게)
        내용: AI 수익성(ROI), 미 국채 금리 영향, 내부자 매도 현황 포함.
        뉴스 데이터:
        {news_text}
        """
        
        response = model.generate_content(prompt)
        report = response.text

        # 3. 메일 전송
        msg = EmailMessage()
        msg.set_content(report)
        msg['Subject'] = "📊 [성공] 오늘의 AI 시장 심층 분석 보고서"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ 메일 발송 성공!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    run()
