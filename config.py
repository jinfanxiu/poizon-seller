import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 환경 변수에서 설정 가져오기
POIZON_DUTOKEN = os.getenv("POIZON_DUTOKEN", "")
POIZON_COOKIE = os.getenv("POIZON_COOKIE", "")
# 브라우저 Network → merchant/search 요청에 있는 shumeiid(수美 리스크). 없으면 passport 401이 날 수 있음
POIZON_SHUMEIID = os.getenv("POIZON_SHUMEIID", "")
# 검색 API는 보통 상품검색 페이지 referer; 필요 시 .env로 덮어쓰기
POIZON_REFERER = os.getenv(
    "POIZON_REFERER",
    "https://seller.poizon.com/main/goods/search",
)

# Musinsa 설정
MUSINSA_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
