import base64
import hashlib
import hmac
import time
import pandas as pd
import requests
import streamlit as st

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="대경엘이디 키워드 분석 도구",
    page_icon="💡",
    layout="wide",
)

st.title("💡 대경엘이디 스마트스토어 키워드 도구 (초고속 버전)")
st.markdown(
    "키워드를 입력하면 네이버 검색광고 연관키워드 및 PC/모바일 검색수, 클릭수, 클릭률을 단 1~2초 만에 즉시 분석합니다."
)

# 네이버 검색광고 API 키 (고정)
AD_API_KEY = (
    "0100000000371b479ab071d46548adf9fbd6ce01bdaee449d2d08c7d8345f4b45bd78861f9"
)
AD_SECRET_KEY = "AQAAAAA3G0easHHUZUit+fvWzgG9K2dGHqEN6alomTVepwhDhQ=="
AD_CUSTOMER_ID = "641071"


# 전자서명 생성 함수
def generate_signature(timestamp, method, uri, secret_key):
    message = f"{timestamp}.{method}.{uri}"
    hash = hmac.new(
        secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    )
    return base64.b64encode(hash.digest()).decode("utf-8")


# 메인 키워드 입력창
st.subheader("🔍 키워드 입력")
st.caption(
    "대표 키워드를 입력해 주세요. (예: LED바, 24vled바 / 세부 키워드는 대표 키워드와 함께 입력하면 연관키워드가 풍부하게 추출됩니다.)"
)

keyword_input_raw = st.text_area(
    "분석할 키워드를 입력하세요 (예: LED바, 24vled바)",
    value="LED바, 24vled바",
    height=100,
)

# 입력 키워드 추출
input_keywords = [
    k.strip()
    for k in keyword_input_raw.replace("\n", ",").split(",")
    if k.strip()
]

if st.button("🚀 키워드 분석 실행", type="primary"):
    if not input_keywords:
        st.warning("분석할 키워드를 입력해 주세요.")
    else:
        with st.spinner("단 1~2초 만에 연관키워드를 분석 중입니다..."):
            timestamp = str(int(time.time() * 1000))
            uri = "/keywordstool"
            method = "GET"

            # 입력된 모든 키워드를 쉼표로 연결하여 API 전달
            hint_keywords = ",".join([k.replace(" ", "") for k in input_keywords[:5]])
            params = {
                "hintKeywords": hint_keywords
            }

            sig = generate_signature(timestamp, method, uri, AD_SECRET_KEY)
            headers = {
                "X-Timestamp": timestamp,
                "X-API-KEY": AD_API_KEY,
                "X-Customer": str(AD_CUSTOMER_ID),
                "X-Signature": sig,
            }

            try:
                api_url = f"https://api.searchad.naver.com{uri}"
                response = requests.get(
                    api_url, headers=headers, params=params, timeout=10
                )

                if response.status_code == 200:
                    data = response.json().get("keywordList", [])

                    result_rows = []
                    total_items = min(len(data), 50)

                    for idx, item in enumerate(data[:total_items]):
                        kw = item.get("relKeyword")

                        qc_pc = item.get("monthlyPcQcCnt", 0)
                        qc_mobile = item.get("monthlyMobileQcCnt", 0)
                        clk_pc = item.get("monthlyAvePcClkCnt", 0)
                        clk_mobile = item.get("monthlyAveMobileClkCnt", 0)
                        ctr_pc = item.get("monthlyAvePcCtr", 0)
                        ctr_mobile = item.get("monthlyAveMobileCtr", 0)
                        comp = item.get("compIdx", "-")

                        result_rows.append(
                            {
                                "연관키워드": kw,
                                "월간검색수(PC)": (
                                    f"{qc_pc:,}"
                                    if isinstance(qc_pc, int)
                                    else str(qc_pc)
                                ),
                                "월간검색수(모바일)": (
                                    f"{qc_mobile:,}"
                                    if isinstance(qc_mobile, int)
                                    else str(qc_mobile)
                                ),
                                "월평균클릭수(PC)": str(clk_pc),
                                "월평균클릭수(모바일)": str(clk_mobile),
                                "월평균클릭률(PC)": f"{ctr_pc}%",
                                "월평균클릭률(모바일)": f"{ctr_mobile}%",
                                "경쟁정도": comp,
                            }
                        )

                    df = pd.DataFrame(result_rows)

                    st.success(
                        f"총 {len(df)}개의 연관키워드 분석이 완료되었습니다!"
                    )
                    st.dataframe(df, use_container_width=True, height=500)

                    # 엑셀 다운로드
                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="📥 분석 결과 엑셀(CSV) 다운로드",
                        data=csv,
                        file_name=(
                            f"대경엘이디_키워드분석_{input_keywords[0]}.csv"
                        ),
                        mime="text/csv",
                    )

                else:
                    st.error(
                        f"네이버 API 연동 실패 (상태 코드: {response.status_code})."
                    )
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
