import csv
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

import config
from sellers.musinsa import MusinsaSeller
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator
from utils.constants import BrandEnum


def get_kst_now():
    """현재 시간을 한국 시간(KST)으로 반환합니다."""
    utc_now = datetime.now(timezone.utc)
    kst_now = utc_now + timedelta(hours=9)
    return kst_now


class TestBrandSearch(unittest.TestCase):
    def setUp(self):
        self.musinsa_seller = MusinsaSeller()
        
        dutoken = config.POIZON_DUTOKEN
        cookie = config.POIZON_COOKIE
        if not dutoken or not cookie:
            print("\n[Warning] Poizon dutoken or cookie is not set. API calls may fail.")
        
        self.poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
        self.comparator = ProductComparator(self.musinsa_seller, self.poizon_seller)
        
        # 결과 저장 경로 (data/brand_search/)
        self.output_dir = Path(__file__).parent.parent / "data" / "brand_search"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.kst_now = get_kst_now()

    def test_search_nike_products(self):
        target_brand = BrandEnum.DESCENTE
        target_page = 2
        
        # 파일명에 브랜드 추가 (YYYY-MM-DD_HH-MM-SS_BRAND.csv)
        timestamp = self.kst_now.strftime("%Y-%m-%d_%H-%M-%S")
        output_file = self.output_dir / f"{timestamp}_{target_brand.name}.csv"
        
        print(f"\n[Step 1] Searching for {target_brand.value} (Page {target_page})...")
        
        # 1. 브랜드 검색
        product_infos = self.musinsa_seller.search_by_brand(target_brand, page=target_page)
        
        if not product_infos:
            print("No products found.")
            return

        print(f"Found {len(product_infos)} products. Starting comparison...")

        results = []
        # 테스트 목적상 상위 5개만 비교
        items_to_process = product_infos
        
        for i, item in enumerate(items_to_process):
            print(f"\n[{i+1}/{len(items_to_process)}] Processing: {item.title} ({item.model_no})")
            
            if not item.model_no:
                print("  -> Skip: No model number")
                continue
            
            # 2. 가격 비교 수행
            comparison_result = self.comparator.compare_product(item.model_no)
            
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
                    "Brand": target_brand.value,
                    "Product Name": item.title,
                    "Model No": item.model_no,
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

        # 3. 파일 저장
        if results:
            print(f"\n[Step 3] Saving results to {output_file}...")
            fieldnames = [
                "Brand", "Product Name", "Model No", "Size", "EU Size", "Color", 
                "Musinsa Price", "Musinsa Stock", "Poizon Price", "Poizon Stock", 
                "Profit", "Margin (%)", "Status", "Poizon Score", "Poizon Rank",
                "Image URL", "Musinsa URL", "Has Profit", "Updated At"
            ]
            
            with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
                
            print("Done!")
        else:
            print("No comparison results to save.")


if __name__ == "__main__":
    unittest.main()
