"""Streamlit Secrets에 APP_PASSWORD를 설정한 뒤 streamlit run app.py로 실행합니다."""
import hmac
import random
import re

import streamlit as st


# 이름, 장르, 예상 가격, 매운맛, 국물, 양, 어울리는 상황과 동행(실습용 분류)
MENU = [
    ("칼국수","한식",8500,0,"뜨끈한 국물","배부르게","비 오는 날|혼자|가족"),
    ("잔치국수","한식",7000,0,"뜨끈한 국물","가볍게","바쁜 날|혼자"),
    ("물냉면","한식",9500,0,"시원한 냉국물","적당히","평범한 날|친구"),
    ("제육덮밥","한식",8500,1,"국물 없이","배부르게","평범한 날|직장 동료|혼자"),
    ("매운 낙지볶음","한식",14000,2,"국물 없이","배부르게","나를 위한 보상|친구"),
    ("불고기 정식","한식",15000,0,"국물 없이","배부르게","생일/기념일|가족|직장 동료"),
    ("짜장면","중식",7500,0,"국물 없이","적당히","바쁜 날|혼자"),
    ("짬뽕","중식",9500,2,"뜨끈한 국물","배부르게","비 오는 날|친구|직장 동료"),
    ("새우볶음밥","중식",9000,0,"국물 없이","적당히","평범한 날|가족"),
    ("마파두부덮밥","중식",9500,1,"국물 없이","배부르게","혼자|직장 동료"),
    ("탕수육 세트","중식",16000,0,"국물 없이","배부르게","생일/기념일|가족|친구"),
    ("우동","일식",7500,0,"뜨끈한 국물","적당히","비 오는 날|혼자"),
    ("냉소바","일식",9500,0,"시원한 냉국물","가볍게","평범한 날|혼자"),
    ("매운 라멘","일식",11000,2,"뜨끈한 국물","배부르게","비 오는 날|친구"),
    ("연어초밥","일식",16000,0,"국물 없이","적당히","생일/기념일|나를 위한 보상|연인"),
    ("돈카츠","일식",11000,0,"국물 없이","배부르게","평범한 날|직장 동료|가족"),
    ("에그샌드위치","양식",6500,0,"국물 없이","가볍게","바쁜 날|혼자"),
    ("버섯크림수프와 빵","양식",9500,0,"뜨끈한 국물","가볍게","비 오는 날|연인"),
    ("마르게리타 피자","양식",14500,0,"국물 없이","배부르게","생일/기념일|가족|친구"),
    ("아라비아타 파스타","양식",13000,1,"국물 없이","적당히","나를 위한 보상|연인"),
    ("스테이크 플레이트","양식",19500,0,"국물 없이","배부르게","생일/기념일|연인|가족"),
    ("참치김밥","분식",5000,0,"국물 없이","가볍게","바쁜 날|혼자"),
    ("어묵국수","분식",6500,0,"뜨끈한 국물","적당히","비 오는 날|혼자"),
    ("떡볶이","분식",5500,1,"국물 없이","적당히","평범한 날|친구"),
    ("매운 쫄면","분식",8000,2,"국물 없이","적당히","나를 위한 보상|친구"),
    ("라볶이","분식",7500,1,"국물 없이","배부르게","평범한 날|친구"),
]
ANY = "아무거나"
LIMITS = {"8천 원 이하":8000, "1만 원 이하":10000, "1만 5천 원 이하":15000,
          "2만 원 이하":20000, ANY:float("inf")}
HEAT = ["순한 맛만","살짝 매콤하게","제대로 맵게"]
QUESTIONS = [
    ("오늘은 어떤 날이에요?", ["평범한 날","바쁜 날","비 오는 날","나를 위한 보상","생일/기념일",ANY]),
    ("오늘은 누구랑 먹어요?", ["혼자","친구","연인","가족","직장 동료",ANY]),
    ("어떤 종류의 음식이 당겨요?", ["한식","중식","일식","양식","분식",ANY]),
    ("한 사람당 예산은 얼마예요?", list(LIMITS)),
    ("매운맛은 어때요?", HEAT+[ANY]),
    ("국물은 어때요?", ["뜨끈한 국물","시원한 냉국물","국물 없이",ANY]),
    ("얼마나 든든하게 먹고 싶어요?", ["가볍게","적당히","배부르게",ANY]),
]
ALIASES = {"만원":"1만 원 이하","만원이하":"1만 원 이하","10000원":"1만 원 이하",
           "8000원":"8천 원 이하","8천원":"8천 원 이하","15000원":"1만 5천 원 이하",
           "20000원":"2만 원 이하","생일":"생일/기념일","기념일":"생일/기념일",
           "혼밥":"혼자","비오는날":"비 오는 날","순한맛":"순한 맛만",
           "맵게":"제대로 맵게","상관없어":ANY,"상관없음":ANY}

def parse_answer(step, text):
    key = re.sub(r"[\s,.!?~]", "", text)
    value = ALIASES.get(key,key).replace(" ", "")
    return next((label for label in QUESTIONS[step][1] if label.replace(" ","") == value), None)

def restart():
    s.answers = []
    s.history = [("assistant", QUESTIONS[0][0])]
    s.remaining = []
    s.current = []
    s.chosen = None



def matches(item, answers):
    day, company, genre, budget, heat, soup, portion = answers
    tags = item[6].split("|")
    return [choice for choice, matched in [
        (day, day in tags), (company, company in tags),
        (heat, heat == HEAT[item[3]]), (soup, soup == item[4]), (portion, portion == item[5])
    ] if matched]


def candidates(answers):
    # 예산·장르·순한 맛은 지키고, 나머지 취향은 일치한 개수로 순위를 매깁니다.
    _, _, genre, budget, heat, _, _ = answers
    pool = [item for item in MENU if item[2] <= LIMITS[budget]
            and (genre == ANY or genre == item[1]) and (heat != HEAT[0] or item[3] == 0)]
    random.shuffle(pool)
    return sorted(pool, key=lambda item: len(matches(item, answers)), reverse=True)

def next_pair():
    # 이미 보여준 후보는 남은 목록에서 빼서 중복 추천을 막습니다.
    s.current, s.remaining = s.remaining[:2], s.remaining[2:]


def submit(text):
    step = len(s.answers)
    answer = parse_answer(step, text)
    s.history.append(("user", text))
    if answer is None:
        s.history.append(("assistant", "이렇게 답해 주세요: " + " / ".join(QUESTIONS[step][1])
                          + "\n\n" + QUESTIONS[step][0]))
    else:
        s.answers.append(answer)
        if len(s.answers) < len(QUESTIONS):
            s.history.append(("assistant", QUESTIONS[len(s.answers)][0]))
        else:
            s.remaining = candidates(s.answers)
            next_pair()
    st.rerun()


st.set_page_config(page_title="오늘 뭐 먹지?", page_icon="🍚")
st.markdown("""<style>
.stApp,[data-testid="stBottomBlockContainer"] {background:#fff9ed;color:#352a24}
[data-testid="stMainBlockContainer"] {max-width:46rem;padding-top:3rem}
.stApp h1,.stApp h2,.stApp h3 {color:#643015}
.stApp .stButton button,.stApp .stFormSubmitButton button {background:#fff0db;color:#51270d;
border:1px solid #cd8549;border-radius:.75rem;min-height:2.8rem}
.stApp .stButton button:hover {background:#ffe1b5;color:#51270d}
</style>""", unsafe_allow_html=True)
st.title("🍚 오늘 뭐 먹지?")
s = st.session_state
if not s.get("authenticated"):
    try:
        password = st.secrets["APP_PASSWORD"]
    except (FileNotFoundError, KeyError):
        st.error("앱 설정의 Secrets에 APP_PASSWORD를 먼저 등록해 주세요.")
        st.stop()
    with st.form("login", clear_on_submit=True):
        entry = st.text_input("접속 비밀번호", type="password")
        if st.form_submit_button("시작하기"):
            if password and hmac.compare_digest(entry.encode(), str(password).encode()):
                s.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호를 다시 확인해 주세요.")
    st.stop()

if s.get("menu_version") != 2:
    s.menu_version = 2
    restart()
step = len(s.answers)
if step < len(QUESTIONS):
    st.caption(f"질문 {step + 1}/{len(QUESTIONS)}")
for role, message in s.history:
    with st.chat_message(role):
        st.text(message)

if step < len(QUESTIONS):
    if step == 0 and st.button("🎲 그냥 하나 골라줘", width="stretch"):
        s.answers = [ANY] * len(QUESTIONS)
        s.chosen = random.choice(MENU)
        s.history = [("user", "그냥 하나 골라줘!")]
        st.rerun()
    for label in QUESTIONS[step][1]:
        if st.button(label, width="stretch"):
            submit(label)
    typed = st.chat_input("답을 짧게 입력해 주세요", max_chars=100)
    if typed:
        submit(typed)
elif s.chosen:
    st.subheader(f"오늘 점심은 {s.chosen[0]}!")
    st.write(f"예상 가격 {s.chosen[2]:,}원")
elif s.current:
    st.subheader("이 메뉴는 어때요?")
    for item in s.current:
        name, genre, price, heat, soup, portion, _ = item
        st.subheader(name)
        st.write(f"{genre} · 1인 예상 {price:,}원")
        st.write(f"{['순한 맛', '살짝 매콤한 맛', '매운맛'][heat]} · {soup} · {portion}")
        reasons = matches(item, s.answers)
        if reasons:
            st.caption("내 답변과 맞는 점: " + " · ".join(reasons))
    if st.button("그냥 골라줘!", width="stretch"):
        s.chosen = random.choice(s.current)
        st.rerun()
    if s.remaining:
        if st.button("다른 메뉴 보기", width="stretch"):
            next_pair()
            st.rerun()
    else:
        st.info("이 조건의 후보를 모두 보여드렸어요. 조건을 바꾸려면 ‘처음부터’를 눌러 주세요.")
else:
    st.info("맞는 메뉴가 없어요. ‘처음부터’를 눌러 예산이나 취향을 바꿔 보세요.")
if step == len(QUESTIONS):
    st.caption("가격은 실습용 예상 금액이에요.")
if step or len(s.history) > 1:
    if st.button("처음부터", width="stretch"):
        restart()
        st.rerun()

