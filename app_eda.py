import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                ### **Regional Population Trends 데이터셋**  
                - **제공처**: 대한민국 통계청 기반 공개 인구 통계 데이터  
                - **설명**:  
                전국 및 각 시·도의 연도별 인구, 출생아수, 사망자수를 포함한 시계열 통계로,  
                인구 구조의 변화 및 지역별 인구 흐름을 분석하는 데 활용됨  
                - **주요 변수**:  
                - `연도`: 기준 연도  
                - `지역`: 지역명  
                - `인구`: 총 인구 수  
                - `출생아수(명)`: 출생자 수  
                - `사망자수(명)`: 사망자 수  
                
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class PopulationEDA:
    def __init__(self):
        st.header("👥 인구 데이터 EDA")
        uploaded = st.file_uploader("population_trends.csv 파일 업로드", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드해주세요.")
            return

        df = pd.read_csv(uploaded)
        df.replace('-', 0, inplace=True)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)

        # 지역명 영어 변환 매핑
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju', '전국': 'National'
        }
        df['영문지역'] = df['지역'].map(region_map)

        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        with tabs[0]:
            st.subheader("📌 기초 통계")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())

        with tabs[1]:
            st.subheader("📈 연도별 전체 인구 추이")
            national_df = df[df['지역'] == '전국']
            recent = national_df.tail(3)
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.lineplot(x='연도', y='인구', data=national_df, marker='o', ax=ax)
            avg_delta = (recent['출생아수(명)'].mean() - recent['사망자수(명)'].mean())
            pred_2035 = national_df.iloc[-1]['인구'] + avg_delta * (2035 - national_df['연도'].max())
            ax.axhline(y=pred_2035, color='r', linestyle='--')
            ax.text(2034, pred_2035, f"Predicted 2035: {int(pred_2035):,}", color='red')
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)

            

        with tabs[2]:
            st.subheader("📊 지역별 최근 5년 인구 변화량")
            latest_year = df['연도'].max()
            recent_5 = df[df['연도'].between(latest_year - 4, latest_year)]
            pivot = recent_5.pivot(index='연도', columns='영문지역', values='인구')
            delta = pivot.loc[latest_year] - pivot.loc[latest_year - 4]
            delta = delta.drop("National").sort_values(ascending=False)

            fig1, ax1 = plt.subplots()
            sns.barplot(x=delta.values / 1000, y=delta.index, ax=ax1)
            ax1.bar_label(ax1.containers[0], fmt='%.0f')
            ax1.set_title("Population Change (Last 5 Years)")
            ax1.set_xlabel("Change (Thousands)")
            ax1.set_ylabel("Region")
            st.pyplot(fig1)

            rate = (pivot.loc[latest_year] / pivot.loc[latest_year - 4] - 1).drop("National") * 100
            fig2, ax2 = plt.subplots()
            sns.barplot(x=rate.values, y=rate.index, ax=ax2)
            ax2.set_title("Population Growth Rate (%)")
            ax2.set_ylabel("Region")
            st.pyplot(fig2)

            st.markdown(
                "> **해설:** 상위 지역들은 최근 5년간 유입 인구가 상대적으로 많거나, 지속적인 개발이 이뤄진 지역일 가능성이 높습니다."
                "> 반대로 하위 지역은 고령화나 인구 유출이 지속되었을 가능성이 있습니다."
                "> 변화율(%)을 함께 확인함으로써 단순 인구 변화량보다 더 명확한 성장/감소 흐름을 파악할 수 있습니다."
            )

        with tabs[3]:
            st.subheader("🔍 연도별 증감 상위 사례")
            df_no_total = df[df['지역'] != '전국']
            df_no_total['증감'] = df_no_total.groupby('지역')['인구'].diff()
            top100 = df_no_total.sort_values(by='증감', ascending=False).head(100).copy()
            top100['증감'] = top100['증감'].astype(int)
            top100['증감'] = top100['증감'].map(lambda x: f"{x:,}")
            styled = top100.style.applymap(
                lambda v: 'background-color: #add8e6' if isinstance(v, str) and '-' not in v else 
                          'background-color: #f4cccc' if isinstance(v, str) and '-' in v else '',
                subset=['증감']
            )
            st.dataframe(styled)

        with tabs[4]:
            st.subheader("📊 연도-지역 누적 영역 그래프")
            pivot = df.pivot(index='연도', columns='영문지역', values='인구').fillna(0)
            pivot = pivot.drop(columns='National', errors='ignore')

            sns.set_theme(style="whitegrid")
            fig, ax = plt.subplots(figsize=(12, 6))
            x = pivot.index.values
            y = pivot.values.T  # shape: (지역 수, 연도 수)
            labels = pivot.columns.tolist()
            ax.stackplot(x, y, labels=labels, alpha=0.9)
            ax.set_title("Population by Region (Stacked Area)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), title="Region")
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_PopulationEDA = st.Page(PopulationEDA, title="인구 분석", icon="👥", url_path="population")


# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_PopulationEDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()