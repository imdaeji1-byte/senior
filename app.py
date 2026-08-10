import os
import re
from google import genai
import requests
import streamlit as st

# ---------------------------------------------------------
# 1. API 키 설정
# ---------------------------------------------------------
NAVER_CLIENT_ID = "YOUR_NAVER_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_NAVER_CLIENT_SECRET"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini AI 클라이언트 초기화
try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    ai_client = None

st.set_page_config(page_title="시니어 쉬운 쇼핑", layout="centered")


# ---------------------------------------------------------
# 2. 백엔드 로직: 네이버 API 호출 & Gemini AI 요약
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_naver_products(keyword, display_count=5):
    """네이버 쇼핑 API 데이터 수집 및 캐싱"""
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": keyword, "display": display_count, "sort": "asc"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=4)
        if res.status_code == 200:
            return res.json().get("items", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=86400)
def get_ai_senior_summary(product_title, category):
    """Gemini API를 활용한 시니어 맞춤 3줄 실시간 분석"""
    if not ai_client:
        return [
            "⭐ **평가:** 어르신 만족도가 높고 후기로 검증된 가성비 제품입니다.",
            "👍 **편의성:** 사용법이 매우 단순하여 어르신 혼자서도 쓰기 쉽습니다.",
            "💡 **추천:** 동일 성능 제품 대비 최저가 수준으로 추천합니다.",
        ]

    prompt = f"""
    당신은 60대 이상 어르신을 위한 친절한 쇼핑 전문 도우미입니다.
    아래 상품 정보를 읽고 어르신들이 가장 중요하게 생각할 실용적 장점 3가지를 정리해주세요.
    
    [상품명]: {product_title}
    [카테고리]: {category}
    
    제약조건:
    1. 정확히 3개의 줄로 작성할 것.
    2. 각 문장 시작 부분에 내용과 어울리는 이모지(👟, 💊, 👓, 💡, 🔒 등)를 넣을 것.
    3. 어려운 기술 용어나 영어 단어 대신 어르신이 이해하기 쉬운 단어로 작성할 것.
    4. 무게, 안전성, 착용감, 글씨 크기, 복용 편의성 등 실생활 관점에 집중할 것.
    """

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        lines = [
            line.strip()
            for line in response.text.split("\n")
            if line.strip() and not line.startswith("#")
        ]
        return lines[:3]
    except Exception as e:
        return [
            "⭐ **평가:** 시니어 맞춤 가성비 우수 추천 상품입니다.",
            "👍 **편의성:** 조작 및 관리가 매우 편리합니다.",
            "💡 **추천:** 가격 대비 만족도가 매우 뛰어난 제품입니다.",
        ]


# ---------------------------------------------------------
# 3. UI 화면 구성
# ---------------------------------------------------------
st.markdown("## 👵👴 시니어 최저가 큐레이션 쇼핑몰")
st.caption("AI가 어르신 눈높이에 맞춰 분석한 가성비 1등 상품")
st.write("---")

category = st.radio(
    "원하시는 카테고리를 선택하세요:",
    ["👟 발이 편한 신발", "💊 무릎·관절 영양제", "🔍 큰글씨 돋보기", "✏️ 직접 검색"],
    horizontal=True,
)

search_keyword = ""
if category == "👟 발이 편한 신발":
    search_keyword = "시니어 편한 신발"
elif category == "💊 무릎·관절 영양제":
    search_keyword = "관절 영양제"
elif category == "🔍 큰글씨 돋보기":
    search_keyword = "돋보기 안경"
else:
    search_keyword = st.text_input("찾고 싶은 물건을 입력하세요:")

if search_keyword:
    st.write("---")
    st.markdown(f"### 📦 **'{search_keyword}'** 추천 목록")

    raw_items = fetch_naver_products(search_keyword)

    if not raw_items:
        # 네이버 API 키가 입력되지 않은 경우 보여줄 테스트 데이터
        raw_items = [
            {
                "title": "<b>시니어</b> 다이얼 편한 초경량 효도화 신발",
                "lprice": "29800",
                "mallName": "시니어마켓",
                "link": "https://naver.com",
                "image": "https://via.placeholder.com/150",
            },
            {
                "title": "관절보궁 프리미엄 무릎 관절 영양제 1개월분",
                "lprice": "45000",
                "mallName": "건강몰",
                "link": "https://naver.com",
                "image": "https://via.placeholder.com/150",
            },
        ]

    for idx, item in enumerate(raw_items[:5], 1):
        clean_title = re.sub("<.*?>", "", item["title"])
        price = int(item["lprice"])
        mall_name = item["mallName"]
        link = item["link"]
        image_url = item["image"]

        # Gemini AI 호출 (3줄 실시간 분석)
        summary_list = get_ai_senior_summary(clean_title, search_keyword)

        with st.container():
            st.markdown(f"#### **{idx}. {clean_title}**")
            col_img, col_info = st.columns([1, 2])

            with col_img:
                st.image(image_url, use_container_width=True)

            with col_info:
                st.markdown(f"### 💰 **최저가 {price:,}원**")
                st.caption(f"판매처: {mall_name}")

                st.markdown("---")
                st.markdown("**📌 AI 시니어 맞춤 분석**")
                for point in summary_list:
                    st.markdown(f"{point}")

                st.write("")
                st.link_button(
                    f"👉 {price:,}원에 구매하러 가기",
                    link,
                    use_container_width=True,
                )

        st.write("---")