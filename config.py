import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 환경 변수에서 설정 가져오기
POIZON_DUTOKEN = os.getenv("POIZON_DUTOKEN", "")
POIZON_COOKIE = os.getenv("POIZON_COOKIE", "")

# Musinsa 설정
MUSINSA_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
