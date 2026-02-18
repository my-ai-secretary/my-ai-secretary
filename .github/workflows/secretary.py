import os
import requests
import google.generativeai as genai
import smtplib
from email.message import EmailMessage

# 설정값 불러오기
NEWS_API_KEY = os.environ['NEWS_API_KEY']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
MY_EMAIL = os.environ['MY_EMAIL']
APP_PASSWORD = os.environ['APP_PASSWORD']

def run():
    # 뉴스 수집 및 AI 분석 (아까 성공한 코드와 동일)
    url = f"https://newsapi.org/v2/everything?q=AI+Bubble+Market&apiKey={NEWS_API_KEY}"
    news_data = requests.get(url).json().get('articles', [])[:5]
    news_text = "/n".join([f"- {a['title']}" for a in news_data])

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-3-flash-preview')
    report = model.generate_content(f"경제 비서로서 다음 뉴스를 심층 분석해줘: {news_text}").text

    # 메일 발송
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = "  새벽 6시 AI 시장 리포트"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL

    with smtplib.SMTP_SSL('smtp.gamil.com', 465) as smtp:
        smtp.login(MY_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

  if __name__ == "__main__":
     run()
