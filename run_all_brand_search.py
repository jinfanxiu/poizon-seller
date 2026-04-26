"""
등록된 모든 브랜드(BrandEnum)를 순회 검색하여 Poizon 비교 결과를 저장합니다.

예시:
  uv run python run_all_brand_search.py
  uv run python run_all_brand_search.py --pages 2
  uv run python run_all_brand_search.py --continue-on-error
  TARGET_PAGES=3 uv run python run_all_brand_search.py
"""
from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from run_brand_search import run_brand_search
from utils.constants import BrandEnum


def _all_brands_csv() -> str:
    """BrandEnum 전체를 콤마 문자열로 반환합니다."""
    return ",".join(brand.value for brand in BrandEnum)


def cli() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="BrandEnum에 등록된 모든 브랜드를 검색/비교하여 data/brand_search/*.csv 저장",
    )
    parser.add_argument(
        "--pages",
        "-p",
        default=None,
        help="페이지: 1 | 1-3 | 1,2,3 (기본: 환경변수 TARGET_PAGES 또는 1)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="API 오류 감지 시 즉시 중단 (기본 동작)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="API 오류가 나도 다음 브랜드/상품으로 계속 진행",
    )
    args = parser.parse_args()

    pages = args.pages if args.pages is not None else (os.environ.get("TARGET_PAGES", "1") or "1")
    all_brands = _all_brands_csv()
    env_fail_fast = (os.environ.get("FAIL_FAST_ON_API_ERROR", "1") or "1").strip().lower() in {"1", "true", "yes", "y"}
    fail_fast = env_fail_fast
    if args.continue_on_error:
        fail_fast = False
    elif args.fail_fast:
        fail_fast = True
    os.environ["FAIL_FAST_ON_API_ERROR"] = "1" if fail_fast else "0"

    print(f"총 {len(BrandEnum)}개 브랜드 수집 시작 (pages={pages}, fail_fast={fail_fast})")
    run_brand_search(all_brands, str(pages))


if __name__ == "__main__":
    cli()
