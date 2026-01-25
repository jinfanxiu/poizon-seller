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

# 1. 비밀번호 인증 (세션 유지 기능 추가)
def check_password():
    """Returns `True` if the user had the correct password."""

    # 환경 변수에서 비밀번호 가져오기
    correct_password = os.environ.get("PASSWORD")
    if not correct_password:
        try:
            correct_password = st.secrets.get("PASSWORD")
        except Exception:
            correct_password = None

    if not correct_password:
        st.error("비밀번호 설정이 되어있지 않습니다. (환경 변수 PASSWORD 또는 secrets.toml)")
        return False

    # 비밀번호 해시 생성 (URL에 노출되므로 원본 대신 해시 사용)
    password_hash = hashlib.sha256(correct_password.encode()).hexdigest()

    # URL 쿼리 파라미터 확인 (새로고침 시 유지용)
    query_params = st.query_params
    if "auth" in query_params and query_params["auth"] == password_hash:
        st.session_state["password_correct"] = True
        return True

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
            # URL에 인증 토큰 추가
            st.query_params["auth"] = password_hash
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

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
    params = {
        "status": "in_progress" # 실행 중인 것만 조회
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            runs = response.json().get("workflow_runs", [])
            # schedule.yml 워크플로우인지 확인
            for run in runs:
                if run["path"].endswith(WORKFLOW_FILE):
                    return "running", run["html_url"]
            return "idle", None
        else:
            return "error", f"API Error: {response.status_code}"
    except Exception as e:
        return "error", str(e)

def trigger_workflow():
    """워크플로우 실행을 요청합니다."""
    if not GH_TOKEN:
        return False, "GitHub Token not set"
        
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "ref": "main" # 실행할 브랜치
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
def get_available_dates():
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    files = sorted(data_dir.glob("*.csv"), reverse=True)
    return [f.name for f in files]

@st.cache_data(ttl=600)
def load_data(filename):
    csv_path = f"data/{filename}"
    if not os.path.exists(csv_path):
        return None
    
    df = pd.read_csv(csv_path)
    
    # 이미지 URL 보정
    if 'Image URL' in df.columns:
        df['Image URL'] = df['Image URL'].astype(str).str.replace('https:/images', 'https://image.msscdn.net/images', regex=False)
        df['Image URL'] = df['Image URL'].astype(str).str.replace('https://images', 'https://image.msscdn.net/images', regex=False)
        
    return df

st.title("👟 Poizon Seller Dashboard")

# 상단 컨트롤 패널 (업데이트 버튼 등)
col_title, col_btn = st.columns([3, 1])

with col_btn:
    # 워크플로우 상태 확인
    status, run_url = get_workflow_status()
    
    if status == "running":
        st.info("🔄 업데이트 진행 중...")
        if run_url:
            st.markdown(f"[진행 상황 보기]({run_url})")
    elif status == "error":
        st.error("GitHub API 오류")
    else:
        if st.button("🔄 데이터 업데이트 요청"):
            success, msg = trigger_workflow()
            if success:
                st.success("업데이트 요청 완료! (약 5분 소요)")
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"요청 실패: {msg}")

# 날짜 선택
available_files = get_available_dates()
if not available_files:
    st.warning("아직 데이터가 수집되지 않았습니다.")
    st.stop()

selected_file = st.selectbox("Select Data (Date & Time)", available_files)
df = load_data(selected_file)

if df is None:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

last_updated = df['Updated At'].iloc[0] if 'Updated At' in df.columns else selected_file.replace(".csv", "")
st.write(f"Data Loaded: {selected_file} (Last Updated: {last_updated})")

# 3. 데이터 가공 (정렬 및 포맷팅)
# 필터링 옵션
st.sidebar.header("Filters")
show_profit_only = st.sidebar.checkbox("Show Profit Items Only", value=False)
selected_brands = st.sidebar.multiselect("Brand", df['Brand'].unique(), default=df['Brand'].unique())

# 필터 적용
filtered_df = df[df['Brand'].isin(selected_brands)]

if show_profit_only:
    filtered_df = filtered_df[filtered_df['Status'] == 'PROFIT']

# 데이터프레임 정렬
filtered_df = filtered_df.sort_values(by=['Has Profit', 'Profit', 'Model No', 'Size'], ascending=[False, False, True, True])

# 컬럼 순서 및 이름 정리
display_cols = [
    "Status",
    "Musinsa Price",
    "Poizon Price",
    "Profit",
    "Size",
    "Margin (%)",
    "EU Size",
    "Color",
    "Poizon Stock",
    "Musinsa URL",
    # 내부 정렬용 컬럼들 (표시 안함)
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

# 표시용 데이터프레임 생성
display_df = filtered_df.copy()
display_df['Musinsa Price'] = display_df['Musinsa Price'].apply(format_currency)
display_df['Poizon Price'] = display_df['Poizon Price'].apply(format_currency)
display_df['Profit'] = display_df['Profit'].apply(format_currency)
display_df['Margin (%)'] = display_df['Margin (%)'].apply(format_percent)
display_df['Status'] = display_df['Status'].apply(format_status)

# 4. 테이블 표시 (모델별 그룹화 효과)
unique_models = filtered_df[['Model No', 'Has Profit', 'Profit']].drop_duplicates(subset=['Model No'])['Model No'].tolist()

for model_no in unique_models:
    model_group = display_df[display_df['Model No'] == model_no]
    first_row = model_group.iloc[0]
    
    # 헤더 (상품 정보)
    with st.expander(f"[{first_row['Brand']}] {first_row['Product Name']} ({model_no}) - {first_row['Poizon Rank']}", expanded=True):
        # 이미지와 정보 표시
        col1, col2 = st.columns([1, 3])
        
        # 원본 df에서 이미지 URL 가져오기
        img_url = filtered_df[filtered_df['Model No'] == model_no]['Image URL'].iloc[0]
        
        with col1:
            if pd.notna(img_url) and img_url.startswith("http"):
                st.image(img_url, use_container_width=True)
            else:
                st.text("No Image")
            
            # 모델 번호 복사 버튼
            st.code(model_no, language=None)
        
        with col2:
            # 요청한 컬럼만 선택하여 표시
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
                    "Status": st.column_config.TextColumn(
                        "Status",
                        help="Profit status"
                    )
                }
            )
