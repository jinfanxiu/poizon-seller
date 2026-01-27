import re
from models.comparison import ProductComparisonResult, SizeComparison
from models.product import ProductInfo
from sellers.musinsa import MusinsaSeller
from sellers.poizon import PoizonSeller
from utils.normalizer import DataNormalizer
from utils.constants import KR_TO_CLOTHING_SIZE_MAP


class ProductComparator:
    def __init__(self, musinsa_seller: MusinsaSeller, poizon_seller: PoizonSeller):
        self.musinsa = musinsa_seller
        self.poizon = poizon_seller

    def _normalize_color(self, color: str) -> str:
        """
        색상 문자열을 정규화합니다.
        """
        if not color or color.upper() == "ONE COLOR":
            return "onecolor"
        
        # 1. 전처리: 소문자 변환
        norm_color = color.lower()
        
        # 2. 무신사 패턴 처리 (예: BLK0_BLACK -> black, BGBK_BEIGE-BLACK -> beige-black)
        if "_" in norm_color:
            parts = norm_color.split("_")
            norm_color = parts[-1]

        # 3. 특수문자 제거 및 공백 처리
        clean_color = re.sub(r"[^a-z]", "", norm_color)
        
        # 4. 매핑 테이블 조회
        from utils.constants import COLOR_MAP
        
        for standard, synonyms in COLOR_MAP.items():
            for syn in synonyms:
                if syn in clean_color:
                    return standard
        
        return clean_color

    def compare_product(self, keyword: str) -> ProductComparisonResult | None:
        """
        키워드(모델 번호)로 무신사와 Poizon 상품을 검색하고 가격을 비교합니다.
        입력된 키워드가 복합 모델 번호(예: SQ313RPD91_BLK0)인 경우, 
        기본 모델 번호(SQ313RPD91)로 변환하여 검색을 시도합니다.
        """
        search_keyword = keyword
        
        # 모델 번호 정제 (예: SQ313RPD91_BLK0 -> SQ313RPD91)
        # 데상트 등 일부 브랜드는 모델 번호 뒤에 색상 코드가 붙음
        if "_" in keyword:
            parts = keyword.split("_")
            # 앞부분이 모델 번호일 가능성이 높음 (단, 너무 짧으면 제외)
            if len(parts[0]) > 3:
                search_keyword = parts[0]
                print(f"[Comparator] Refined keyword: {keyword} -> {search_keyword}")

        print(f"[Comparator] Comparing for keyword: {search_keyword}")

        # 1. Fetch Data
        musinsa_infos = self.musinsa.search_product(search_keyword)
        poizon_info = self.poizon.get_product_info(search_keyword)

        if not musinsa_infos or not poizon_info:
            print("[Comparator] Failed to fetch product info from one or both platforms.")
            if not musinsa_infos:
                print("  - Musinsa: Not Found")
            if not poizon_info:
                print("  - Poizon: Not Found")
            return None

        # 대표 상품 정보
        musinsa_main_info = musinsa_infos[0]
        print(f"[Comparator] Found products:\n  - Musinsa: {len(musinsa_infos)} items found (Main: {musinsa_main_info.title})\n  - Poizon: {poizon_info.title}")

        # 2. Map Options by (Normalized Size, Normalized Color)
        musinsa_map = {}
        for info in musinsa_infos:
            for opt in info.options:
                norm_size = DataNormalizer.normalize_size(opt.size)
                norm_color = self._normalize_color(opt.color)
                key = (norm_size, norm_color)
                
                if key not in musinsa_map:
                    musinsa_map[key] = opt
                else:
                    existing = musinsa_map[key]
                    if existing.stock_status != "IN_STOCK" and opt.stock_status == "IN_STOCK":
                        musinsa_map[key] = opt
                    elif existing.stock_status == "IN_STOCK" and opt.stock_status == "IN_STOCK":
                        if opt.price < existing.price:
                            musinsa_map[key] = opt
                    elif existing.stock_status != "IN_STOCK" and opt.stock_status != "IN_STOCK":
                        if opt.price < existing.price:
                            musinsa_map[key] = opt

        poizon_map = {}
        for opt in poizon_info.options:
            norm_size = DataNormalizer.normalize_size(opt.size)
            norm_color = self._normalize_color(opt.color)
            key = (norm_size, norm_color)
            
            if key not in poizon_map:
                poizon_map[key] = opt
            else:
                if opt.price < poizon_map[key].price:
                    poizon_map[key] = opt

        # 3. Compare & Merge Logic
        merged_keys = set(musinsa_map.keys()) | set(poizon_map.keys())
        final_comparisons = {}
        
        processed_poizon_keys = set()

        # 1차: 정확한 매칭
        for key in list(merged_keys):
            if key in musinsa_map and key in poizon_map:
                final_comparisons[key] = (musinsa_map[key], poizon_map[key])
                processed_poizon_keys.add(key)
                merged_keys.remove(key)

        # 2차: 유연한 매칭
        for m_key in list(musinsa_map.keys()):
            if m_key in final_comparisons: continue
            
            m_size, m_color = m_key
            m_opt = musinsa_map[m_key]
            
            best_p_match = None
            candidates = [k for k in poizon_map.keys() if k not in processed_poizon_keys]
            
            for p_key in candidates:
                p_size, p_color = p_key
                p_opt_candidate = poizon_map[p_key]
                
                # 사이즈 매칭 로직
                is_size_match = False
                if m_size == p_size:
                    is_size_match = True
                elif m_size in KR_TO_CLOTHING_SIZE_MAP:
                    converted_size = KR_TO_CLOTHING_SIZE_MAP[m_size]
                    if converted_size == p_size:
                        is_size_match = True
                    elif p_opt_candidate.eu_size and converted_size == p_opt_candidate.eu_size:
                        is_size_match = True
                
                if not is_size_match:
                    continue

                # 색상 매칭 로직
                is_color_match = False
                if m_color == p_color or m_color == "onecolor" or p_color == "onecolor" or \
                   m_color in p_color or p_color in m_color:
                    is_color_match = True
                
                if is_color_match:
                    best_p_match = p_key
                    break
            
            if best_p_match:
                final_comparisons[m_key] = (m_opt, poizon_map[best_p_match])
                processed_poizon_keys.add(best_p_match)
                if m_key in merged_keys: merged_keys.remove(m_key)
                if best_p_match in merged_keys: merged_keys.remove(best_p_match)
            else:
                final_comparisons[m_key] = (m_opt, None)
                if m_key in merged_keys: merged_keys.remove(m_key)

        # 남은 Poizon 키 처리
        for p_key in merged_keys:
            if p_key in poizon_map and p_key not in processed_poizon_keys:
                final_comparisons[p_key] = (None, poizon_map[p_key])

        # 4. Generate Result List
        comparisons = []
        sorted_keys = sorted(final_comparisons.keys(), key=lambda k: (k[1], DataNormalizer.size_to_float(k[0])))

        for key in sorted_keys:
            size, color_key = key
            m_opt, p_opt = final_comparisons[key]

            m_price = m_opt.price if m_opt else 0
            p_price = p_opt.price if p_opt else 0
            
            m_stock = m_opt.stock_status if m_opt else "N/A"
            p_stock = p_opt.stock_status if p_opt else "N/A"
            
            display_color = m_opt.color if m_opt else (p_opt.color if p_opt else color_key)
            if display_color == "onecolor":
                display_color = "ONE COLOR"
                
            eu_size = p_opt.eu_size if p_opt and p_opt.eu_size else None

            # 비교 로직
            diff = 0
            margin = 0.0
            is_profitable = False

            if m_price > 0 and p_price > 0 and m_stock == "IN_STOCK":
                diff = p_price - m_price
                if diff > 0:
                    is_profitable = True
                    margin = (diff / m_price) * 100
                else:
                    is_profitable = False
                    margin = (diff / m_price) * 100

            comparisons.append(SizeComparison(
                size=size,
                eu_size=eu_size,
                color=display_color,
                musinsa_price=m_price,
                musinsa_stock_status=m_stock,
                musinsa_url=musinsa_main_info.product_url if m_opt else None,
                poizon_price=p_price,
                poizon_stock_status=p_stock,
                poizon_url=None,
                price_diff=diff,
                is_profitable=is_profitable,
                profit_margin=round(margin, 2)
            ))

        return ProductComparisonResult(
            keyword=keyword,
            musinsa_title=musinsa_main_info.title,
            poizon_title=poizon_info.title,
            image_url=musinsa_main_info.image_url,
            poizon_sales_score=poizon_info.sales_metrics.velocity_score if poizon_info.sales_metrics else 0.0,
            poizon_sales_rank=poizon_info.sales_metrics.rank if poizon_info.sales_metrics else "N/A",
            comparisons=comparisons
        )
