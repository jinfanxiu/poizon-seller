import difflib
import re
from typing import Any


def normalize_text(text: str) -> str:
    """
    문자열에서 영문자와 숫자만 남기고 소문자로 변환합니다.
    """
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def find_best_match(
    candidates: list[dict[str, Any]],
    target_keyword: str,
    key_field: str = "articleNumber",
    threshold: float = 0.8,
) -> dict[str, Any] | None:
    """
    후보군 리스트에서 타겟 키워드(모델 번호 등)와 가장 일치하는 항목을 찾습니다.

    Args:
        candidates: 검색 대상 리스트 (dict 형태)
        target_keyword: 찾고자 하는 키워드
        key_field: dict에서 비교할 필드명 (기본값: articleNumber)
        threshold: 유사도 임계값 (0.0 ~ 1.0)

    Returns:
        가장 일치하는 항목의 dict, 없으면 None
    """
    if not candidates or not target_keyword:
        return None

    normalized_target = normalize_text(target_keyword)
    if not normalized_target:
        return None

    # 1. 정확히 일치하는 경우 (Exact Match)
    for item in candidates:
        value = item.get(key_field)
        if value and normalize_text(str(value)) == normalized_target:
            return item

    # 2. 부분 일치 (Token Match) - 특수문자 기준으로 쪼개서 포함 여부 확인
    for item in candidates:
        value = str(item.get(key_field, ""))
        if not value:
            continue
        
        # 특수문자 기준으로 분리 (예: "FN3889-010" -> ["fn3889", "010"])
        parts = re.split(r"[^a-zA-Z0-9]", value)
        normalized_parts = [normalize_text(p) for p in parts]
        
        if normalized_target in normalized_parts:
            return item

    # 키워드가 너무 짧으면 유사도 비교는 생략 (오탐 방지)
    if len(normalized_target) <= 4:
        return None

    # 3. 유사도 비교 (Sequence Matcher)
    best_match: dict[str, Any] | None = None
    highest_score: float = 0.0

    for item in candidates:
        value = str(item.get(key_field, ""))
        if not value:
            continue
        
        normalized_value = normalize_text(value)
        score = difflib.SequenceMatcher(None, normalized_target, normalized_value).ratio()
        
        if score >= threshold and score > highest_score:
            highest_score = score
            best_match = item

    return best_match
