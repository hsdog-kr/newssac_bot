from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import requests

# --- [1. 설정 영역] ---
TARGET_URL = "https://newsac.kosac.re.kr/public/program/thumb?institutionId=117,109,100,108,107,135,126,134,125,124,133,116,110,132,99,123,122,98,97,131,93,106,96,115,119,130,113,111,118,127,92,105,95,121,101,120,91,104,94,103,129&programTypeCode=C0101&programRegionCode=C0504&targetCode=C0601&operationStatusCode=C1102&schoolLevelCode=G007"

# GitHub Secrets에서 보안 값을 가져옵니다.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
DB_FILE = "last_programs.txt"

def get_current_programs():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 깃허브 액션 환경에서는 드라이버를 자동으로 찾습니다.
    driver = webdriver.Chrome(options=chrome_options)
    titles = set()
    
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 사이트 접속 중...")
        driver.get(TARGET_URL)
        time.sleep(15) # 페이지 로딩 대기
        
        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            raw_text = el.text.strip()
            if raw_text and len(raw_text) > 10:
                lines = raw_text.split('\n')
                candidate = lines[0].strip()
                exclude = ["로그인", "회원가입", "공지사항", "Copyright", "신청 안내"]
                if not any(ex in candidate for ex in exclude):
                    clean_title = candidate.replace("(경상권)", "").strip()
                    if len(clean_title) > 5:
                        titles.add(clean_title)
        return titles
    except Exception as e:
        print(f"❌ 데이터 추출 오류: {e}")
        return set()
    finally:
        driver.quit()

def send_telegram_msg(new_items):
    text = f"🔔 [디지털 새싹] 새로운 프로그램 발견!\n\n"
    for item in new_items:
        text += f"- {item}\n"
    text += f"\n확인하러 가기: {TARGET_URL}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text}
    
    try:
        requests.post(url, data=payload)
        print(f"[{time.strftime('%H:%M:%S')}] 텔레그램 알림 전송 완료!")
    except Exception as e:
        print(f"❌ 텔레그램 오류: {e}")

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 모니터링 시작")
    current_titles = get_current_programs()
    
    if not current_titles:
        print("가져온 데이터가 없습니다.")
        return

    # 파일 기반 DB 비교
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            for t in current_titles: f.write(t + "\n")
        print("초기 데이터 저장 완료.")
    else:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            prev_titles = set([line.strip() for line in f.readlines()])
        
        new_items = current_titles - prev_titles
        if new_items:
            send_telegram_msg(list(new_items))
            with open(DB_FILE, "w", encoding="utf-8") as f:
                for t in current_titles: f.write(t + "\n")
        else:
            print("변동 사항 없음.")

if __name__ == "__main__":

    main()
