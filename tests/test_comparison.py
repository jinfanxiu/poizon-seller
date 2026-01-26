import unittest
import config
from sellers.musinsa import MusinsaSeller
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator


class TestProductComparison(unittest.TestCase):
    def setUp(self):
        # Musinsa Seller 초기화
        self.musinsa_seller = MusinsaSeller()
        
        # Poizon Seller 초기화
        dutoken = config.POIZON_DUTOKEN
        cookie = config.POIZON_COOKIE
        
        if not dutoken or not cookie:
            print("\n[Warning] Poizon dutoken or cookie is not set in config.py. API calls may fail.")
        
        self.poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
        
        self.comparator = ProductComparator(self.musinsa_seller, self.poizon_seller)
        # 테스트 키워드 변경 (색상별 비교가 필요한 모델)
        self.test_keyword = "SQ323RFT91"

    def test_compare_product(self):
        print(f"\n[Test] Comparing products for {self.test_keyword}...")
        
        result = self.comparator.compare_product(self.test_keyword)
        
        if not result:
            print("Comparison failed (Product not found on one or both platforms).")
            return

        print("\n" + "="*120)
        print(f"Comparison Result for: {result.keyword}")
        print(f"Musinsa: {result.musinsa_title}")
        print(f"Poizon : {result.poizon_title}")
        print(f"Poizon Sales Score: {result.poizon_sales_score} ({result.poizon_sales_rank})")
        print("="*120)
        
        # 헤더 출력 (EU Size 추가)
        print(f"{'Size':<8} | {'EU Size':<8} | {'Color':<15} | {'Musinsa (Buy)':<15} | {'Poizon (Sell)':<15} | {'Profit':<12} | {'Margin(%)':<10} | {'Status':<10}")
        print("-" * 120)
        
        for comp in result.comparisons:
            # Musinsa 가격 및 재고 표시
            m_price_str = f"{comp.musinsa_price:,}" if comp.musinsa_price > 0 else "N/A"
            if comp.musinsa_stock_status != "IN_STOCK":
                m_price_str += " (Sold Out)"
                
            # Poizon 가격 표시
            p_price_str = f"{comp.poizon_price:,}" if comp.poizon_price > 0 else "N/A"
            
            # 수익금 및 마진율 표시
            profit_str = f"{comp.price_diff:+,}" if comp.price_diff != 0 else "-"
            margin_str = f"{comp.profit_margin:+.2f}%" if comp.price_diff != 0 else "-"
            
            # 상태 표시 (이득/손해/불가)
            status = ""
            if comp.musinsa_stock_status == "IN_STOCK" and comp.poizon_price > 0:
                if comp.is_profitable:
                    status = "PROFIT ✅"
                else:
                    status = "LOSS ❌"
            else:
                status = "N/A"

            # 색상 표시 (너무 길면 자름)
            color_display = (comp.color[:13] + '..') if len(comp.color) > 15 else comp.color
            
            # EU Size 표시
            eu_size_str = comp.eu_size or '-'

            print(f"{comp.size:<8} | {eu_size_str:<8} | {color_display:<15} | {m_price_str:<15} | {p_price_str:<15} | {profit_str:<12} | {margin_str:<10} | {status:<10}")
            
        print("="*120 + "\n")
        
        # 검증
        self.assertEqual(result.keyword, self.test_keyword)
        self.assertTrue(len(result.comparisons) > 0)


if __name__ == "__main__":
    unittest.main()
