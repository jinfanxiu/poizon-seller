"""
특정 브랜드(무신사) 검색 후 Poizon과 비교해 `data/brand_search/`에 CSV를 저장합니다.
`main.py`의 `EXECUTION_MODE=brand_search`과 동일한 로직입니다.

예시:
  uv run python run_brand_search.py 브랜드          # 가능한 브랜드 목록만 출력
  uv run python run_brand_search.py 데상트 --pages 1
  uv run python run_brand_search.py 나이키,아디다스 -p 1-2
  TARGET_BRANDS=푸마 TARGET_PAGES=2 uv run python run_brand_search.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def run_brand_search(target_brands: str, target_pages: str) -> None:
    """환경을 설정한 뒤 `main.main()` (brand_search)을 실행합니다."""
    os.environ["EXECUTION_MODE"] = "brand_search"
    os.environ["TARGET_BRANDS"] = target_brands
    os.environ["TARGET_PAGES"] = str(target_pages)

    os.chdir(_ROOT)

    from main import main  # noqa: WPS433 — 실행 시에만 import

    main()


def _normalize_brands(s: str) -> str:
    return ",".join(p.strip() for p in s.split(",") if p.strip())


_LIST_KEYWORDS = frozenset(
    {"브랜드", "list", "목록", "-l", "--list", "brands", "help-brands"}
)


def print_available_brands() -> None:
    """BrandEnum에 등록된 한글 브랜드명을 stdout에 출력합니다."""
    from utils.constants import BrandEnum

    print("사용 가능 브랜드명 (한글, 무신사/코드와 정확히 일치):")
    for b in BrandEnum:
        print(f"  - {b.value}")


def cli() -> None:
    p = argparse.ArgumentParser(
        description="브랜드별 무신사 검색 → Poizon 비교, 결과는 data/brand_search/*.csv",
    )
    p.add_argument(
        "brands",
        nargs="?",
        default=None,
        help="BrandEnum 한글명(복수는 콤마). '브랜드'·list·목록 이면 가능 목록만 출력. 생략 시 TARGET_BRANDS",
    )
    p.add_argument(
        "--pages",
        "-p",
        default=None,
        help="페이지: 1 | 1-3 | 1,2,3 (기본: 환경변수 TARGET_PAGES 또는 1)",
    )
    p.add_argument(
        "--fail-fast",
        action="store_true",
        help="API 오류 감지 시 즉시 중단 (기본 동작)",
    )
    p.add_argument(
        "--continue-on-error",
        action="store_true",
        help="API 오류가 나도 다음 상품/브랜드로 계속 진행",
    )
    a = p.parse_args()

    env_b = os.environ.get("TARGET_BRANDS", "").strip()
    brands = a.brands if a.brands is not None and str(a.brands).strip() else env_b
    if not brands:
        print_available_brands()
        p.print_help()
        p.exit(
            1,
            "\nerror: brands 가 필요합니다. "
            "목록만 보려면: uv run python run_brand_search.py 브랜드\n"
            "예: uv run python run_brand_search.py 데상트 --pages 1\n",
        )

    b_key = brands.strip()
    if b_key in _LIST_KEYWORDS:
        print_available_brands()
        raise SystemExit(0)

    pages = a.pages if a.pages is not None else (os.environ.get("TARGET_PAGES", "1") or "1")
    env_fail_fast = (os.environ.get("FAIL_FAST_ON_API_ERROR", "1") or "1").strip().lower() in {"1", "true", "yes", "y"}
    fail_fast = env_fail_fast
    if a.continue_on_error:
        fail_fast = False
    elif a.fail_fast:
        fail_fast = True
    os.environ["FAIL_FAST_ON_API_ERROR"] = "1" if fail_fast else "0"
    run_brand_search(_normalize_brands(brands), str(pages))


if __name__ == "__main__":
    cli()
