import csv
import time
import os
from pathlib import Path
from datetime import datetime

import config
from sellers.musinsa import MusinsaSeller, MusinsaRankingType
from sellers.poizon import PoizonSeller
from utils.comparator import ProductComparator


def main():
    print(f"[{datetime.now()}] Starting data collection...")

    # 1. 초기화
    musinsa_seller = MusinsaSeller()
    
    dutoken = config.POIZON_DUTOKEN
    cookie = config.POIZON_COOKIE
    
    if not dutoken or not cookie:
        print("[Error] Poizon credentials not found. Please check .env or config.py")
        return

    poizon_seller = PoizonSeller(dutoken=dutoken, cookie=cookie)
    comparator = ProductComparator(musinsa_seller, poizon_seller)

    # 결과 저장 경로 설정 (날짜별 파일)
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_file = output_dir / f"{today_str}.csv"

    # 2. 랭킹 수집 (중복 제거)
    target_brands = ["나이키", "아디다스", "데상트"]
    ranking_types = [
        MusinsaRankingType.NEW,
        MusinsaRankingType.RISING,
        MusinsaRankingType.ALL
    ]
    
    unique_products = {}  # product_id -> item
    
    print(f"Fetching rankings for {target_brands}...")
    for r_type in ranking_types:
        print(f"  - Fetching {r_type.name} ranking...")
        rankings = musinsa_seller.fetch_ranking(r_type, brand_names=target_brands)
        if rankings:
            for item in rankings:
                if item.product_id not in unique_products:
                    unique_products[item.product_id] = item
        time.sleep(1)

    if not unique_products:
        print("No items found.")
        return

    print(f"Found {len(unique_products)} unique items. Starting comparison...")

    # 3. 비교 및 결과 수집
    results = []
    items_to_process = list(unique_products.values())
    
    for i, item in enumerate(items_to_process):
        print(f"[{i+1}/{len(items_to_process)}] {item.brand_name} - {item.product_name}")
        
        try:
            # 상세 정보 조회 (모델 번호 획득)
            product_info = musinsa_seller.get_product_info(item.product_id)
            if not product_info or not product_info.model_no:
                print("  -> Skip: No model number")
                continue
            
            model_no = product_info.model_no
            
            # 비교 수행
            comparison_result = comparator.compare_product(model_no)
            if not comparison_result:
                print("  -> Skip: Comparison failed")
                continue
            
            # 결과 데이터 구성
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
                    "Updated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            time.sleep(1.5)
            
        except Exception as e:
            print(f"  -> Error: {e}")
            continue

    # 4. CSV 저장
    if results:
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
        print(f"Saved {len(results)} rows to {output_file}")
    else:
        print("No results to save.")

if __name__ == "__main__":
    main()
