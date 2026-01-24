import unittest
from sellers.poizon import PoizonSeller


class TestPoizonSeller(unittest.TestCase):
    def setUp(self):
        # config.py에서 설정을 자동으로 가져옵니다.
        self.seller = PoizonSeller()
        self.test_model_no = "FN3889-010"

    def test_search_product(self):
        """상품 검색 테스트"""
        print(f"\n[Test] Searching for {self.test_model_no}...")
        result = self.seller.search_product(self.test_model_no)
        self.assertIsNotNone(result)
        self.assertEqual(result.get('code'), 200)
        
        data = result.get('data', {})
        product_list = data.get('merchantSpuDtoList', [])
        self.assertTrue(len(product_list) > 0)
        
        # 매칭 테스트
        matched = self.seller.find_matching_product(product_list, self.test_model_no)
        self.assertIsNotNone(matched)
        print(f"  Found: {matched.get('title')} (GID: {matched.get('globalSpuId')})")

    def test_get_product_info(self):
        """상품 상세 정보 조회 테스트"""
        print(f"\n[Test] Getting product info for {self.test_model_no}...")
        product_info = self.seller.get_product_info(self.test_model_no)
        
        self.assertIsNotNone(product_info)
        if product_info:
            print(f"  Title: {product_info.title}")
            print(f"  Model No: {product_info.model_no}")
            self.assertTrue(product_info.options)
            
            first_opt = product_info.options[0]
            print(f"  Option 1: {first_opt.size} / {first_opt.color} - {first_opt.price} KRW")
            self.assertTrue(first_opt.price >= 0)


if __name__ == "__main__":
    unittest.main()
