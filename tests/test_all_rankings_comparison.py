import csv
import time
import unittest
from datetime import datetime
from pathlib import Path

import config
from sellers.musinsa import MusinsaSeller, MusinsaRankingType
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator


class TestAllRankingsComparison(unittest.TestCase):
    def setUp(self):
        self.musinsa_seller = MusinsaSeller()
        
        dutoken = config.POIZON_DUTOKEN
        cookie = config.POIZON_COOKIE
        if not dutoken or not cookie:
            print("\n[Warning] Poizon dutoken or cookie is not set. API calls may fail.")
        
        self.poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
        self.comparator = ProductComparator(self.musinsa_seller, self.poizon_seller)
        
        # 결과 저장 경로
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 파일명에 날짜와 시간 추가
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.output_dir / f"all_rankings_comparison_result_{timestamp}.csv"

    def test_compare_all_rankings(self):
        target_brands = ["나이키", "아디다스", "데상트"]
        ranking_types = [
            MusinsaRankingType.NEW,
            MusinsaRankingType.RISING,
            MusinsaRankingType.ALL
        ]
        
        # 1. 모든 랭킹 수집 및 중복 제거
        unique_products = {}  # product_id -> item
        
        print(f"\n[Step 1] Fetching rankings for {target_brands}...")
        
        for r_type in ranking_types:
            print(f"  - Fetching {r_type.name} ranking...")
            rankings = self.musinsa_seller.fetch_ranking(
                r_type, brand_names=target_brands
            )
            
            if rankings:
                for item in rankings:
                    if item.product_id not in unique_products:
                        unique_products[item.product_id] = item
            
            # API 부하 방지
            time.sleep(1)
            
        if not unique_products:
            print("No items found in any ranking.")
            return

        print(f"Found {len(unique_products)} unique items across all rankings.")
        
        # 2. 가격 비교 수행
        results = []
        # 테스트 목적상 상위 10개만 비교 (전체 비교 시 제한 해제 필요)
        items_to_process = list(unique_products.values())[:10]
        
        print(f"\n[Step 2] Starting comparison for {len(items_to_process)} items...")

        for i, item in enumerate(items_to_process):
            print(f"\n[{i+1}/{len(items_to_process)}] Processing: {item.brand_name} - {item.product_name}")
            
            # 모델 번호 획득을 위해 상세 정보 조회
            product_info = self.musinsa_seller.get_product_info(item.product_id)
            
            if not product_info or not product_info.model_no:
                print("  -> Failed to get model number. Skipping.")
                continue
                
            model_no = product_info.model_no
            print(f"  -> Model No: {model_no}")
            
            # 가격 비교 수행
            comparison_result = self.comparator.compare_product(model_no)
            
            if not comparison_result:
                print("  -> Comparison failed (Poizon match not found).")
                continue
                
            # 결과 수집
            for comp in comparison_result.comparisons:
                results.append({
                    "Ranking Type": "Mixed", # 여러 랭킹에서 왔으므로 Mixed로 표기하거나, 원본 정보를 추적해야 함
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
                    "Margin (%)": f"{comp.profit_margin:.2f}%",
                    "Status": "PROFIT" if comp.is_profitable else ("LOSS" if comp.musinsa_stock_status == "IN_STOCK" and comp.poizon_price > 0 else "N/A"),
                    "Poizon Score": comparison_result.poizon_sales_score,
                    "Poizon Rank": comparison_result.poizon_sales_rank
                })
            
            # API 부하 방지를 위한 딜레이
            time.sleep(2)

        # 3. 파일 저장
        if results:
            print(f"\n[Step 3] Saving results to {self.output_file}...")
            fieldnames = [
                "Ranking Type", "Brand", "Product Name", "Model No", "Size", "EU Size", "Color", 
                "Musinsa Price", "Musinsa Stock", "Poizon Price", "Poizon Stock", 
                "Profit", "Margin (%)", "Status", "Poizon Score", "Poizon Rank"
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
