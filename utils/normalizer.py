import re
from utils.constants import COLOR_MAP, EU_TO_KR_MAP, CLOTHING_SIZE_MAP


class DataNormalizer:
    @staticmethod
    def normalize_color(raw_color: str) -> str:
        """
        입력된 색상 문자열을 표준 영어 색상명으로 변환합니다.
        """
        if not raw_color or raw_color.upper() == "ONE COLOR":
            return "onecolor"

        # 1. 전처리: 소문자 변환, 공백 제거
        norm_color = raw_color.lower().replace(" ", "")
        
        if norm_color == "onecolor":
            return "onecolor"

        # 2. 무신사 패턴 처리 (예: BLK0_BLACK -> black)
        if "_" in norm_color:
            parts = norm_color.split("_")
            norm_color = parts[-1]

        # 3. 매핑 테이블 조회
        for standard, synonyms in COLOR_MAP.items():
            for syn in synonyms:
                if syn in norm_color:
                    return standard
        
        return norm_color

    @staticmethod
    def normalize_size(raw_size: str) -> str:
        """
        입력된 사이즈 문자열을 표준 KR mm 사이즈(문자열)로 변환합니다.
        """
        if not raw_size:
            return "N/A"
            
        s = str(raw_size).upper().strip()
        
        # 0. 특수 패턴 처리 (예: A/XS -> XS)
        if "/" in s:
            parts = s.split("/")
            # 분리된 부분 중 의류 사이즈 맵에 있는 것이 있으면 사용
            for part in parts:
                part = part.strip()
                if part in CLOTHING_SIZE_MAP:
                    s = part
                    break
                # 혹은 숫자만 있는 경우 (예: KR/260)
                if part.isdigit():
                    s = part
                    break
            # 매칭되는게 없으면 마지막 부분 사용 (보통 뒤쪽이 실제 사이즈)
            else:
                s = parts[-1].strip()
        
        # 1. 의류 사이즈 매핑
        if s in CLOTHING_SIZE_MAP:
            return CLOTHING_SIZE_MAP[s]
            
        # 2. 숫자 추출
        nums = re.findall(r"[\d\.]+", s)
        if not nums:
            return s  # 숫자가 없으면 원본 반환
            
        val_str = nums[0]
        try:
            val = float(val_str)
        except ValueError:
            return s

        # 3. 범위 기반 판단 (신발 사이즈)
        # 200 이상: 이미 KR(mm)
        if val >= 200:
            return str(int(val))
            
        # 30 ~ 50: EU 사이즈로 간주하고 변환 시도
        if 30 <= val <= 50:
            # 정확한 매핑이 있으면 사용
            if val_str in EU_TO_KR_MAP:
                return EU_TO_KR_MAP[val_str]
            # 없으면 근사치 계산 (EU -> KR 공식: (EU - 32) * 10 ? 브랜드마다 다름)
            # 여기서는 매핑 테이블에 없으면 원본 반환하거나 보수적으로 처리
            return val_str
            
        # 15 이하: US/UK 사이즈 (변환 로직 필요하지만 복잡하므로 일단 원본 반환)
        
        return str(int(val)) if val.is_integer() else str(val)

    @staticmethod
    def size_to_float(size_str: str) -> float:
        """정렬을 위한 사이즈 숫자 변환"""
        try:
            # 이미 정규화된 사이즈(KR mm)라면 바로 변환
            if size_str.isdigit():
                return float(size_str)
                
            # 의류 사이즈 매핑
            norm_size = size_str.upper().strip()
            if norm_size in CLOTHING_SIZE_MAP:
                return float(CLOTHING_SIZE_MAP[norm_size])
            
            # 숫자 추출
            nums = re.findall(r"[\d\.]+", size_str)
            if nums:
                return float(nums[0])
            
            return 9999.0
        except:
            return 9999.0
