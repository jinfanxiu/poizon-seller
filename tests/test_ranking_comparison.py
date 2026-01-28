import csv
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
from sellers.musinsa import MusinsaSeller, MusinsaRankingType
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator
from utils.constants import TARGET_BRANDS


def get_kst_now():
    """현재 시간을 한국 시간(KST)으로 반환합니다."""
    utc_now = datetime.now(timezone.utc)
    kst_now = utc_now + timedelta(hours=9)
    return kst_now


class TestRankingComparison(unittest.TestCase):
    def setUp(self):
        self.musinsa_seller = MusinsaSeller()
        
        dutoken = config.POIZON_DUTOKEN
        cookie = config.POIZON_COOKIE
        if not dutoken or not cookie:
            print("\n[Warning] Poizon dutoken or cookie is not set. API calls may fail.")
        
        self.poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
        self.comparator = ProductComparator(self.musinsa_seller, self.poizon_seller)
        
        # 결과 저장 경로 (data/ranking/)
        self.output_dir = Path(__file__).parent.parent / "data" / "ranking"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.kst_now = get_kst_now()
        timestamp = self.kst_now.strftime("%Y-%m-%d_%H-%M-%S")
        self.output_file = self.output_dir / f"{timestamp}.csv"

    def test_compare_ranking_items(self):
        # 1. 랭킹 가져오기 & 필터링
        print(f"\n[Step 1] Fetching ranking filtered by {TARGET_BRANDS}...")
        
        rankings = self.musinsa_seller.fetch_ranking(
            MusinsaRankingType.ALL, brand_names=TARGET_BRANDS
        )
        
        if not rankings:
            print("No items found in ranking.")
            return

        print(f"Found {len(rankings)} items. Starting comparison for top 5 items...")

        results = []
        # API 호출 제한 및 시간 관계상 상위 5개만 테스트
        for i, item in enumerate(rankings[:5]):
            print(f"\n[{i+1}/{min(len(rankings), 5)}] Processing: {item.brand_name} - {item.product_name}")
            
            # 2. 모델 번호 획득을 위해 상세 정보 조회
            product_info = self.musinsa_seller.get_product_info(item.product_id)
            
            if not product_info or not product_info.model_no:
                print("  -> Failed to get model number. Skipping.")
                continue
                
            model_no = product_info.model_no
            print(f"  -> Model No: {model_no}")
            
            # 3. 가격 비교 수행
            comparison_result = self.comparator.compare_product(model_no)
            
            if not comparison_result:
                print("  -> Comparison failed (Poizon match not found).")
                continue
                
            # 결과 수집
            has_profit = False
            for comp in comparison_result.comparisons:
                if comp.is_profitable:
                    has_profit = True
            
            for comp in comparison_result.comparisons:
                results.append({
                    "Brand": item.brand_name,
                    "Product Name": item.product_name,
                    "Model No": model_no,
                    "Size": comp.size,
                    "EU Size": comp.eu_size or "-",
                    "Color": comp.color,
                    "Musinsa Price": comp.musinsa_price,
                    "Musinsa Stock": comp.musinsa_stock_status,
                    "Poizon Price": comp.poizon_price,
                    "Poizon Stock": comp.poizon_stock_status,
                    "Profit": comp.price_diff,
                    "Margin (%)": comp.profit_margin,
                    "Status": "PROFIT" if comp.is_profitable else ("LOSS" if comp.musinsa_stock_status == "IN_STOCK" and comp.poizon_price > 0 else "N/A"),
                    "Poizon Score": comparison_result.poizon_sales_score,
                    "Poizon Rank": comparison_result.poizon_sales_rank,
                    "Image URL": comparison_result.image_url,
                    "Musinsa URL": comp.musinsa_url,
                    "Has Profit": has_profit,
                    "Updated At": self.kst_now.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            time.sleep(2)

        # 4. 파일 저장
        if results:
            print(f"\n[Step 4] Saving results to {self.output_file}...")
            fieldnames = [
                "Brand", "Product Name", "Model No", "Size", "EU Size", "Color", 
                "Musinsa Price", "Musinsa Stock", "Poizon Price", "Poizon Stock", 
                "Profit", "Margin (%)", "Status", "Poizon Score", "Poizon Rank",
                "Image URL", "Musinsa URL", "Has Profit", "Updated At"
            ]
            
            with open(self.output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
                
            print("Done!")
        else:
            print("No comparison results to save.")


if __name__ == "__main__":
    unittest.main()
