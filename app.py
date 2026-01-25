import streamlit as st
import pandas as pd
import os
from pathlib import Path

# 페이지 설정
st.set_page_config(page_title="Poizon Seller Dashboard", layout="wide")

# 1. 비밀번호 인증
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Streamlit Cloud의 st.secrets 또는 환경 변수(Render)에서 비밀번호 가져오기
        if "PASSWORD" in st.secrets:
            correct_password = st.secrets["PASSWORD"]
        else:
            correct_password = os.environ.get("PASSWORD")

        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
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

# 2. 데이터 로드 및 전처리
def get_available_dates():
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    files = sorted(data_dir.glob("*.csv"), reverse=True)
    return [f.stem for f in files]

@st.cache_data(ttl=600)
def load_data(date_str):
    csv_path = f"data/{date_str}.csv"
    if not os.path.exists(csv_path):
        return None
    
    df = pd.read_csv(csv_path)
    return df

st.title("👟 Poizon Seller Dashboard")

# 날짜 선택
available_dates = get_available_dates()
if not available_dates:
    st.warning("아직 데이터가 수집되지 않았습니다.")
    st.stop()

selected_date = st.selectbox("Select Date", available_dates)
df = load_data(selected_date)

if df is None:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

st.write(f"Data Loaded: {selected_date} (Last Updated: {df['Updated At'].iloc[0]})")

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
    "Brand", "Product Name", "Model No", "Size", "EU Size", "Color",
    "Musinsa Price", "Musinsa Stock", "Poizon Price", "Poizon Stock",
    "Profit", "Margin (%)", "Status", "Poizon Score", "Poizon Rank", "Musinsa URL"
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

# 표시용 데이터프레임 생성
display_df = filtered_df[display_cols].copy()
display_df['Musinsa Price'] = display_df['Musinsa Price'].apply(format_currency)
display_df['Poizon Price'] = display_df['Poizon Price'].apply(format_currency)
display_df['Profit'] = display_df['Profit'].apply(format_currency)
display_df['Margin (%)'] = display_df['Margin (%)'].apply(format_percent)

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
                st.image(img_url, width=150)
            else:
                st.text("No Image")
        
        with col2:
            # 스타일링된 데이터프레임 표시
            st.dataframe(
                model_group.drop(columns=['Brand', 'Product Name', 'Model No', 'Image URL', 'Poizon Score', 'Poizon Rank'], errors='ignore'),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Musinsa URL": st.column_config.LinkColumn("Link"),
                    "Status": st.column_config.TextColumn(
                        "Status",
                        help="Profit status",
                        validate="^PROFIT|LOSS|N/A$"
                    )
                }
            )
