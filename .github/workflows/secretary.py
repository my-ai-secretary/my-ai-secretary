import os
import requests
import google.generativeai as genai
import smtplib
from email.message import EmailMessage

# [핵심] 깃허브의 금고(Secrets)에서 정보를 가져오는 설정입니다.
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MY_EMAIL = os.environ.get('MY_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

def run():
    # 1. 뉴스 수집
    query = "AI Bubble profitability Samsung Nvidia insider selling"
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    res = requests.get(url).json()
    articles = res.get('articles', [])[:5]
    news_text = "\n".join([f"- {a['title']}" for a in articles])

    # 2. AI 분석 (선생님이 성공하셨던 모델 이름 사용)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    
    prompt = f"경제 전문가로서 다음 뉴스를 심층 분석해서 투자 보고서를 써줘:\n{news_text}"
    response = model.generate_content(prompt)
    report = response.text

    # 3. 메일 전송
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = "📊 [자동발송] 오늘의 AI 시장 심층 분석 보고서"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(MY_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    run()
