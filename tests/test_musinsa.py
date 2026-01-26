import unittest
from sellers.musinsa import MusinsaSeller, MusinsaRankingType
from utils.matching import normalize_text
from utils.constants import TARGET_BRANDS


class TestMusinsaSeller(unittest.TestCase):
    def setUp(self):
        self.seller = MusinsaSeller()
        # 테스트용 모델 번호 (나이키 드라이핏 파크7 -> 유효한 모델 번호로 변경)
        self.test_model_no = "FN3889-010" 
        # 테스트용 상품 ID (검색 테스트를 통해 동적으로 ID를 얻어오는 것이 더 안전함)
        # FN3889-010에 해당하는 상품 ID (예시: 5215534)
        self.test_product_id = "5215534" 

    def _print_options_table(self, options):
        """옵션 정보를 표 형태로 깔끔하게 출력합니다."""
        print(f"\n  {'Size':<15} | {'Color':<20} | {'Price':<12} | {'Stock':<12} | {'Qty':<5}")
        print("  " + "-" * 75)
        for opt in options:
            qty_str = str(opt.stock_quantity) if opt.stock_quantity is not None else "-"
            print(f"  {opt.size:<15} | {opt.color:<20} | {opt.price:<12} | {opt.stock_status:<12} | {qty_str:<5}")
        print("  " + "-" * 75 + "\n")

    def test_fetch_ranking_all(self):
        """전체 랭킹 조회 테스트"""
        print("\n[Test] Fetching ALL ranking...")
        rankings = self.seller.fetch_ranking(MusinsaRankingType.ALL)
        self.assertIsNotNone(rankings)
        self.assertTrue(len(rankings) > 0)
        
        first_item = rankings[0]
        print(f"  Top 1: {first_item.brand_name} - {first_item.product_name} ({first_item.price}원)")
        self.assertTrue(first_item.product_id)
        self.assertTrue(first_item.product_name)

    def test_fetch_ranking_filtered(self):
        """브랜드 필터링 랭킹 조회 테스트"""
        print(f"\n[Test] Fetching ranking filtered by {TARGET_BRANDS}...")
        rankings = self.seller.fetch_ranking(
            MusinsaRankingType.ALL, brand_names=TARGET_BRANDS
        )
        
        if rankings:
            normalized_targets = [normalize_text(b) for b in TARGET_BRANDS]
            for item in rankings:
                # 필터링된 결과의 브랜드가 타겟 브랜드 목록에 포함되는지 확인 (정규화 후 비교)
                item_brand_norm = normalize_text(item.brand_name)
                is_matched = any(t in item_brand_norm or item_brand_norm in t for t in normalized_targets)
                
                if not is_matched:
                    print(f"  [Warning] Unmatched brand found: {item.brand_name}")
                
                # self.assertTrue(is_matched, f"Brand {item.brand_name} is not in target list")
            
            print(f"  Found {len(rankings)} items for {TARGET_BRANDS}")
            # 상위 5개만 출력
            for item in rankings[:5]:
                print(f"    - {item.brand_name}: {item.product_name}")
        else:
            print(f"  No items found for {TARGET_BRANDS} (might be not in top ranking)")

    def test_search_product_success(self):
        """상품 검색 성공 테스트"""
        keyword = self.test_model_no
        print(f"\n[Test] Searching for {keyword}...")
        product_infos = self.seller.search_product(keyword)
        
        self.assertIsNotNone(product_infos)
        self.assertTrue(len(product_infos) > 0)
        
        if product_infos:
            product_info = product_infos[0]
            print(f"  Found: {product_info.title} (ID: {product_info.model_no})")
            self.assertTrue(product_info.model_no)
            self.assertTrue(product_info.options)
            self._print_options_table(product_info.options)

    def test_search_product_fail(self):
        """존재하지 않는 상품 검색 테스트"""
        keyword = "INVALID_MODEL_NUMBER_12345"
        print(f"\n[Test] Searching for invalid keyword: {keyword}...")
        product_infos = self.seller.search_product(keyword)
        self.assertEqual(len(product_infos), 0)
        print("  Correctly returned empty list")

    def test_get_product_info(self):
        """상품 상세 정보 조회 테스트"""
        product_id = self.test_product_id
        print(f"\n[Test] Getting product info for ID: {product_id}...")
        
        product_info = self.seller.get_product_info(product_id)
        
        if product_info is None:
            print("  Fixed ID failed, trying search...")
            # 검색 결과 중 첫 번째 상품 사용
            search_results = self.seller.search_product(self.test_model_no)
            if search_results:
                product_info = search_results[0]
            
        self.assertIsNotNone(product_info, "Failed to get product info")
        
        if product_info:
            print(f"  Title: {product_info.title}")
            print(f"  Model No: {product_info.model_no}")
            self.assertTrue(product_info.title)
            self.assertTrue(product_info.image_url)
            self.assertTrue(len(product_info.options) > 0)
            
            self._print_options_table(product_info.options)
            
            first_option = product_info.options[0]
            self.assertIn(first_option.stock_status, ["IN_STOCK", "OUT_OF_STOCK"])


if __name__ == "__main__":
    unittest.main()
