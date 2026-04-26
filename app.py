import streamlit as st
import pandas as pd
import os
import hashlib
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (로컬 실행 시 필요)
load_dotenv()

# 페이지 설정
st.set_page_config(page_title="Poizon Seller Dashboard", layout="wide")

# GitHub 설정
GITHUB_OWNER = "jinfanxiu"
GITHUB_REPO = "poizon-seller"
WORKFLOW_FILE = "schedule.yml"
GH_TOKEN = os.environ.get("GH_TOKEN")

# 타겟 브랜드 목록
TARGET_BRANDS = [
    "나이키", "아디다스", "데상트", "노스페이스", "코오롱스포츠", 
    "살로몬", "푸마", "뉴발란스", "수아레", "휠라", "아크테릭스"
]

# 세션 상태 초기화
if "is_updating" not in st.session_state:
    st.session_state["is_updating"] = False

# 1. 비밀번호 인증
def check_password():
    """Returns `True` if the user had the correct password."""
    correct_password = os.environ.get("PASSWORD")
    if not correct_password:
        try:
            correct_password = st.secrets.get("PASSWORD")
        except Exception:
            correct_password = None

    if not correct_password:
        st.error("비밀번호 설정이 되어있지 않습니다.")
        return False

    password_hash = hashlib.sha256(correct_password.encode()).hexdigest()
    query_params = st.query_params
    if "auth" in query_params and query_params["auth"] == password_hash:
        st.session_state["password_correct"] = True
        return True

    # 폼 제출로 검증 (on_change 콜백은 일부 Streamlit 버전에서 위젯 값이
    # session_state에 아직 없어 KeyError가 날 수 있음 — Render 등)
    if st.session_state.get("password_correct"):
        return True

    with st.form("password_form"):
        pwd = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("로그인")

    if submitted:
        if pwd == correct_password:
            st.session_state["password_correct"] = True
            st.query_params["auth"] = password_hash
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct") is False:
        st.error("😕 Password incorrect")

    return False

if not check_password():
    st.stop()

# GitHub API 함수
def get_workflow_status():
    """현재 워크플로우 실행 상태를 확인합니다."""
    if not GH_TOKEN:
        return "unknown", "GitHub Token not set"
        
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # in_progress 또는 queued 상태인 것 확인
    params = {"status": "in_progress"}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            runs = response.json().get("workflow_runs", [])
            for run in runs:
                if run["path"].endswith(WORKFLOW_FILE):
                    return "running", run["html_url"]
            
            # queued 상태도 확인
            params["status"] = "queued"
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                runs = response.json().get("workflow_runs", [])
                for run in runs:
                    if run["path"].endswith(WORKFLOW_FILE):
                        return "running", run["html_url"]
            
            return "idle", None
        else:
            return "error", f"API Error: {response.status_code}"
    except Exception as e:
        return "error", str(e)

def trigger_workflow(mode, brands=None, pages=None):
    """워크플로우 실행을 요청합니다."""
    if not GH_TOKEN:
        return False, "GitHub Token not set"
        
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    inputs = {"mode": mode}
    if mode == "brand_search":
        if brands:
            inputs["brands"] = brands # 단일 브랜드 문자열
        if pages:
            inputs["pages"] = pages
            
    data = {
        "ref": "main",
        "inputs": inputs
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 204:
            return True, "Success"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, str(e)

# 2. 데이터 로드 및 전처리
def get_data_types():
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    return [d.name for d in data_dir.iterdir() if d.is_dir()]

def get_available_files(data_type):
    data_dir = Path("data") / data_type
    if not data_dir.exists():
        return []
    files = sorted(data_dir.glob("*.csv"), reverse=True)
    return [f.name for f in files]

@st.cache_data(ttl=600)
def load_data(data_type, filename):
    csv_path = f"data/{data_type}/{filename}"
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path)
    if 'Image URL' in df.columns:
        df['Image URL'] = df['Image URL'].astype(str).str.replace('https:/images', 'https://image.msscdn.net/images', regex=False)
        df['Image URL'] = df['Image URL'].astype(str).str.replace('https://images', 'https://image.msscdn.net/images', regex=False)
    return df

st.title("👟 Poizon Seller Dashboard")
st.caption(
    "브랜드별 수집: `data/brand_search/` — 터미널 `uv run python run_brand_search.py 데상트 -p 1` → 아래 **Select Data Type**에서 `brand_search` 확인"
)

# --- 상단 컨트롤 패널 (UI 개선) ---
st.markdown("### 🔄 Data Update")

# 워크플로우 상태 확인 (캐싱하지 않고 매번 확인)
wf_status, run_url = get_workflow_status()

# 업데이트 요청 처리 (버튼 클릭 후 리런되었을 때 실행됨)
if st.session_state["is_updating"]:
    # 실제 API 호출
    mode_val = st.session_state.get("update_mode_val")
    brand_val = st.session_state.get("update_brand_val")
    page_val = st.session_state.get("update_page_val")
    
    with st.spinner("Requesting update..."):
        success, msg = trigger_workflow(mode_val, brand_val, page_val)
    
    if success:
        st.success("✅ 요청 완료! (약 5분 소요)")
    else:
        st.error(f"❌ 요청 실패: {msg}")
    
    # 상태 초기화 및 리런
    st.session_state["is_updating"] = False
    time.sleep(2)
    st.rerun()

if wf_status == "running":
    st.info(f"⚠️ 현재 데이터 업데이트가 진행 중입니다. 잠시만 기다려주세요. [진행 상황 보기]({run_url})")
elif wf_status == "error":
    st.error(f"GitHub API 상태 확인 실패: {run_url}")
else:
    # 실행 중이 아닐 때만 폼 표시
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            update_mode = st.radio("Mode", ["Ranking", "Brand Search"], key="mode_radio")
            
        with col2:
            if update_mode == "Brand Search":
                selected_brand = st.selectbox("Target Brand", TARGET_BRANDS, key="brand_select")
                target_pages = st.text_input("Pages (e.g. 1 or 1-5)", value="1", key="page_input")
            else:
                st.markdown("<br><p style='color:gray'>Collects data from NEW, RISING, ALL rankings.</p>", unsafe_allow_html=True)
                
        with col3:
            st.write("") # Spacer
            st.write("") # Spacer
            
            # 버튼 클릭 시 상태만 변경하고 즉시 리런
            if st.button("🚀 Start Update", type="primary", use_container_width=True, disabled=st.session_state["is_updating"]):
                st.session_state["is_updating"] = True
                st.session_state["update_mode_val"] = "brand_search" if update_mode == "Brand Search" else "ranking"
                st.session_state["update_brand_val"] = selected_brand if update_mode == "Brand Search" else None
                st.session_state["update_page_val"] = target_pages if update_mode == "Brand Search" else None
                st.rerun()

st.divider()

# --- 데이터 조회 ---
data_types = get_data_types()
if not data_types:
    st.warning(
        "아직 `data/` 아래에 수집된 폴더가 없습니다. "
        "랭킹: `uv run python main.py` · 브랜드: `uv run python run_brand_search.py <브랜드> -p 1`"
    )
    st.stop()

# 브랜드 검색 결과(brand_search)가 있으면 기본으로 선택(8501에서 바로 보기)
default_type_idx = 0
if "brand_search" in data_types:
    default_type_idx = data_types.index("brand_search")
elif "ranking" in data_types:
    default_type_idx = data_types.index("ranking")

col_type, col_date, col_ref = st.columns([1.2, 1.2, 0.4])

with col_type:
    selected_type = st.selectbox("Select Data Type", data_types, index=default_type_idx)
with col_ref:
    st.write("")  # align
    if st.button("캐시 갱신", help="같은 파일명이라도 방금 수집한 CSV를 읽을 때(기본 10분 캐시)"):
        load_data.clear()
        st.rerun()

with col_date:
    available_files = get_available_files(selected_type)
    if not available_files:
        st.warning("해당 타입의 데이터 파일이 없습니다.")
        st.stop()
    selected_file = st.selectbox("Select Date & Time", available_files)

df = load_data(selected_type, selected_file)

if df is None:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

last_updated = df['Updated At'].iloc[0] if 'Updated At' in df.columns else selected_file.replace(".csv", "")
st.caption(f"Data Loaded: {selected_type} / {selected_file} (Last Updated: {last_updated})")

if "Brand" not in df.columns:
    st.error("CSV에 Brand 열이 없어 필터/표를 표시할 수 없습니다.")
    st.dataframe(df, use_container_width=True)
    st.stop()

with st.expander("🔍 Filter Options", expanded=False):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        show_profit_only = st.checkbox("Show Profit Items Only", value=False)
    with col_f2:
        selected_brands_filter = st.multiselect("Brand Filter", df['Brand'].unique(), default=df['Brand'].unique())
    
    if 'Poizon Rank' in df.columns:
        all_ranks = sorted(df['Poizon Rank'].astype(str).unique())
        selected_ranks = st.multiselect("Poizon Rank Filter", all_ranks, default=all_ranks)

# 필터 적용
filtered_df = df[df['Brand'].isin(selected_brands_filter)]

if show_profit_only:
    filtered_df = filtered_df[filtered_df['Status'] == 'PROFIT']

if 'Poizon Rank' in df.columns and selected_ranks:
    filtered_df = filtered_df[filtered_df['Poizon Rank'].isin(selected_ranks)]

# 데이터프레임 정렬
filtered_df = filtered_df.sort_values(by=['Has Profit', 'Profit', 'Model No', 'Size'], ascending=[False, False, True, True])

# 컬럼 순서 및 이름 정리
display_cols = [
    "Status", "Musinsa Price", "Poizon Price", "Profit", "Size", "Margin (%)", 
    "EU Size", "Color", "Poizon Stock", "Musinsa URL",
    "Brand", "Product Name", "Model No", "Image URL", "Poizon Score", "Poizon Rank"
]

# 포맷팅 함수
def format_currency(val):
    try:
        return f"{int(val):,}"
    except:
        return val

def format_percent(val):
    try:
        return f"{float(val):.2f}%"
    except:
        return val

def format_status(val):
    if val == "PROFIT":
        return "✅ PROFIT"
    elif val == "LOSS":
        return "❌ LOSS"
    return val

display_df = filtered_df.copy()
display_df['Musinsa Price'] = display_df['Musinsa Price'].apply(format_currency)
display_df['Poizon Price'] = display_df['Poizon Price'].apply(format_currency)
display_df['Profit'] = display_df['Profit'].apply(format_currency)
display_df['Margin (%)'] = display_df['Margin (%)'].apply(format_percent)
display_df['Status'] = display_df['Status'].apply(format_status)

# 테이블 표시
unique_models = filtered_df[['Model No', 'Has Profit', 'Profit']].drop_duplicates(subset=['Model No'])['Model No'].tolist()

for model_no in unique_models:
    model_group = display_df[display_df['Model No'] == model_no]
    first_row = model_group.iloc[0]
    
    with st.expander(f"[{first_row['Brand']}] {first_row['Product Name']} ({model_no}) - {first_row['Poizon Rank']}", expanded=True):
        col1, col2 = st.columns([1, 3])
        
        img_url = filtered_df[filtered_df['Model No'] == model_no]['Image URL'].iloc[0]
        
        with col1:
            if pd.notna(img_url) and img_url.startswith("http"):
                st.image(img_url, use_container_width=True)
            else:
                st.text("No Image")
            st.code(model_no, language=None)
        
        with col2:
            cols_to_show = [
                "Status", "Musinsa Price", "Poizon Price", "Profit", 
                "Size", "Margin (%)", "EU Size", "Color", "Poizon Stock", "Musinsa URL"
            ]
            
            st.dataframe(
                model_group[cols_to_show],
                use_container_width=True,
                hide_index=True,
                column_order=cols_to_show,
                column_config={
                    "Musinsa URL": st.column_config.LinkColumn("Link"),
                    "Status": st.column_config.TextColumn("Status", help="Profit status")
                }
            )
