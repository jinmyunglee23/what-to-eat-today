"""Streamlit Secrets에 APP_PASSWORD를 설정한 뒤 streamlit run app.py로 실행합니다."""
import hmac
import random
import re

import streamlit as st


# 실습용 메뉴표: 이름, 종류, 예상 가격(원), 매운맛 여부
MENU = [
    ("계란볶음밥", "밥", 7000, False), ("참치마요덮밥", "밥", 7500, False),
    ("소고기주먹밥", "밥", 6000, False), ("버섯덮밥", "밥", 8000, False),
    ("치킨마요덮밥", "밥", 8500, False), ("소불고기덮밥", "밥", 10000, False),
    ("연어덮밥", "밥", 13000, False), ("김치볶음밥", "밥", 7500, True),
    ("제육덮밥", "밥", 9000, True), ("낙지덮밥", "밥", 11000, True),
    ("잔치국수", "면", 7000, False), ("우동", "면", 7500, False),
    ("간장비빔국수", "면", 8000, False), ("칼국수", "면", 8500, False),
    ("콩국수", "면", 9500, False), ("쌀국수", "면", 10500, False),
    ("들기름막국수", "면", 10000, False), ("고추장비빔국수", "면", 7500, True),
    ("쫄면", "면", 8000, True), ("짬뽕", "면", 9500, True),
]
QUESTIONS = [
    ("오늘은 밥이 당겨요, 면이 당겨요?", ["밥", "면", "아무거나"]),
    ("한 끼 예산은 얼마예요?", ["8천 원 이하", "1만 원 이하", "상관없어"]),
    ("매운 음식도 괜찮아요?", ["순한 맛만", "매운 것도 좋아"]),
]


def normalize(text):
    return re.sub(r"[\s,.!?~]", "", text)


# 질문 단계별로 버튼과 짧은 채팅 답변을 같은 선택값으로 바꿉니다.
ALIASES = [
    [("밥", "밥이요", "밥으로"), ("면", "면이요", "면으로"), ("아무거나", "둘다", "상관없어")],
    [("8천원", "8천", "8000", "8000원", "8000원이하", "8천원이하"),
     ("만원", "1만원", "만 원 이하", "10000", "10000원", "10000원이하", "1만원이하"),
     ("상관없어", "상관없어요", "제한없음", "무관")],
    [("순한맛만", "순한맛", "안매운거", "안매운맛", "아니", "아니요"),
     ("매운것도좋아", "매운것도괜찮아", "괜찮아", "네", "응", "상관없어")],
]


def parse_answer(step, text):
    for label, aliases in zip(QUESTIONS[step][1], ALIASES[step]):
        if normalize(text) in {normalize(value) for value in (label, *aliases)}:
            return label
    return None


def restart():
    s.answers = []
    s.history = [("assistant", QUESTIONS[0][0])]
    s.remaining = []
    s.current = []
    s.chosen = None
    s.error_note = ""


def candidates(answers):
    # 세 조건을 모두 만족하는 후보만 모아 순서를 섞습니다.
    kind, budget, heat = answers
    limit = {"8천 원 이하": 8000, "1만 원 이하": 10000, "상관없어": float("inf")}[budget]
    result = [item for item in MENU if (kind == "아무거나" or item[1] == kind)
              and item[2] <= limit and (heat == "매운 것도 좋아" or not item[3])]
    random.shuffle(result)
    return result


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

if "answers" not in s:
    restart()
step = len(s.answers)
if step < 3:
    st.caption(f"질문 {step + 1}/3")
for role, message in s.history:
    with st.chat_message(role):
        st.text(message)

if step < 3:
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
    for name, kind, price, spicy in s.current:
        st.write(f"{name} · 예상 {price:,}원")
        taste = "매콤한" if spicy else "순한"
        reason = f"{taste} {kind} 요리예요."
        if s.answers[1] != "상관없어":
            reason += f" 선택한 예산({s.answers[1]})에 들어요."
        st.write(reason)
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
if step == 3:
    st.caption("가격은 실습용 예상 금액이에요.")
if step or len(s.history) > 1:
    if st.button("처음부터", width="stretch"):
        restart()
        st.rerun()
