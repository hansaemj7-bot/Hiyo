import streamlit as st
import json
import os
from google import genai
from google.genai import types

모델 설정: Gemini 3.8 Flash
MODEL_NAME = "gemini-3.8-flash"

--- 데이터 저장 및 관리 모듈 ---
DATA_DIR = "story_data"
CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")
WORLDS_FILE = os.path.join(DATA_DIR, "worlds.json")
CHATS_DIR = os.path.join(DATA_DIR, "chats")
STATES_DIR = os.path.join(DATA_DIR, "states")

for path in [DATA_DIR, CHATS_DIR, STATES_DIR]:
os.makedirs(path, exist_ok=True)

def load_json(filepath, default):
if os.path.exists(filepath):
try:
with open(filepath, "r", encoding="utf-8") as f:
return json.load(f)
except Exception:
return default
return default

def save_json(filepath, data):
with open(filepath, "w", encoding="utf-8") as f:
json.dump(data, f, ensure_ascii=False, indent=2)

기본 세계관 및 캐릭터 데이터
default_worlds = {
"아카데미 판타지": "마법과 기계공학이 공존하는 왕립 루미나스 아카데미. 최근 교내 결계에 정체불명의 균열이 발생하고 있다.",
"사이버펑크 2180": "거대 기업 '네오코프'가 지배하는 네온 거리. 인간성과 사이보그 기술의 경계가 무너진 어두운 디스토피아."
}
default_chars = {
"엘레나 (아카데미 우등생)": {
"world": "아카데미 판타지",
"description": "아카데미 수석 연금술사. 겉으로는 차갑고 규칙을 철저히 지키지만 연구에 몰두하면 위험한 실험도 서슴지 않는다. 존댓말과 분석적 어조 사용.",
"first_message": "또 늦으셨네요. 결계 이상 현상 조사가 코앞인데... 준비는 다 끝내셨겠죠?"
},
"하이드 (정보 브로커)": {
"world": "사이버펑크 2180",
"description": "골목길 뒷골목 넷러너. 능글맞고 계산적이며 돈과 유익한 정보를 우선시한다. 거친 반말을 사용하며 냉소적인 태도.",
"first_message": "여, 조심해. 네오코프 드론이 방금 뒷골목을 훑고 지나갔어. 내게 줄 칩은 가져왔겠지?"
}
}

worlds = load_json(WORLDS_FILE, default_worlds)
characters = load_json(CHARACTERS_FILE, default_chars)

--- 실시간 상태 추출 함수 ---
def update_dynamic_state(client, char_name, world_name, current_state, user_msg, ai_reply):
"""대화 내용을 바탕으로 변화된 관계, 위치, 아이템, 주요 사건을 실시간 갱신"""
state_extraction_prompt = f"""
당신은 스토리 게임의 '기억 및 상태 기록 엔진'입니다.
기존 상태와 방금 오간 대화를 분석하여 최신 상태(JSON)를 업데이트하세요.

[캐릭터 & 세계관]
캐릭터: {char_name}, 세계관: {world_name}

[현재 누적 상태]
{json.dumps(current_state, ensure_ascii=False, indent=2)}

[방금 발생한 대화]
사용자: {user_msg}
캐릭터: {ai_reply}

[지침]
1. 기존 상태를 바탕으로 새롭게 밝혀진 사실, 변화된 관계/호감도, 현재 위치, 획득/상실한 아이템, 주요 사건을 업데이트하세요.
2. 불필요한 변경은 하지 말고, 오직 새롭게 확정되거나 변경된 사실만 반영하세요.
3. 반드시 아래 JSON 형식(마크다운 없이 순수 JSON)으로만 응답하세요:
{{
"current_location": "현재 위치",
"relationship_status": "유저와의 현재 관계 및 태도",
"inventory_and_items": ["소지품 또는 관련 단서 목록"],
"key_memories": ["기억해야 할 핵심 사건 또는 약속들"]
}}
"""
try:
res = client.models.generate_content(
model=MODEL_NAME,
contents=[state_extraction_prompt],
config=types.GenerateContentConfig(
response_mime_type="application/json",
temperature=0.2
)
)
return json.loads(res.text)
except Exception:
return current_state

--- UI 세팅 ---
st.set_page_config(page_title="Gemini 3.8 Flash 캐릭터 스토리 룸", page_icon="⚡", layout="wide")

사이드바
with st.sidebar:
st.header("⚙️️ 시스템 설정")
st.success(f"현재 구동 모델: {MODEL_NAME}")
api_key = st.text_input("Gemini API Key", type="password", placeholder="AI Studio 키 입력")

st.markdown("---")
st.header("🌍 세계관 및 캐릭터 관리")

with st.expander("➕ 새 세계관 등록"):
new_w_name = st.text_input("세계관 이름")
new_w_desc = st.text_area("세계관 설명 (배경, 분위기, 룰)")
if st.button("세계관 저장"):
if new_w_name and new_w_desc:
worlds[new_w_name] = new_w_desc
save_json(WORLDS_FILE, worlds)
st.success("세계관이 등록되었습니다.")
st.rerun()

with st.expander("➕ 새 캐릭터 등록"):
new_c_name = st.text_input("캐릭터 이름")
new_c_world = st.selectbox("소속 세계관", options=list(worlds.keys()))
new_c_desc = st.text_area("성격, 말투, 관계 설정")
new_c_intro = st.text_area("첫 대화(오프닝 멘트)")
if st.button("캐릭터 저장"):
if new_c_name and new_c_desc:
characters[new_c_name] = {
"world": new_c_world,
"description": new_c_desc,
"first_message": new_c_intro or "안녕하세요."
}
save_json(CHARACTERS_FILE, characters)
st.success("캐릭터가 등록되었습니다.")
st.rerun()

st.markdown("---")
selected_char = st.selectbox("대화할 캐릭터 선택", options=list(characters.keys()))

if not selected_char:
st.info("사이드바에서 캐릭터를 선택해주세요.")
st.stop()

char_info = characters[selected_char]
world_name = char_info.get("world", "미지정")
world_desc = worlds.get(world_name, "설정 없음")

파일 경로
chat_file = os.path.join(CHATS_DIR, f"{selected_char}.json")
state_file = os.path.join(STATES_DIR, f"{selected_char}_state.json")

초기 상태 구조
initial_state = {
"current_location": "초기 대화 장소",
"relationship_status": "초기 대면 관계",
"inventory_and_items": [],
"key_memories": ["이야기가 막 시작되었습니다."]
}

데이터 로드
messages = load_json(chat_file, [
{"role": "assistant", "content": char_info.get("first_message", "대화를 시작합니다.")}
])
live_state = load_json(state_file, initial_state)

--- 메인 레이아웃 (좌측: 채팅 / 우측: 실시간 저장 상태창) ---
col_chat, col_state = st.columns([7, 3])

with col_state:
st.subheader("🧠 실시간 저장된 정보 (메모리)")
st.caption("대화할 때마다 변동 사항이 JSON 파일로 자동 기록·갱신됩니다.")
st.markdown(f"📍 현재 위치:{live_state.get('current_location', '알 수 없음')}")
st.markdown(f"🤝 관계/태도: {live_state.get('relationship_status', '초기')}")

st.markdown("🎒 소지품 / 획득 단서:")
items = live_state.get("inventory_and_items", [])
if items:
for it in items:
st.markdown(f"- {it}")
else:
st.markdown("없음")

st.markdown("📌 핵심 기억 / 확정된 사건:")
mems = live_state.get("key_memories", [])
for m in mems:
st.markdown(f"- {m}")

st.markdown("---")
if st.button("🔄 대화 & 상태 완전 초기화"):
messages = [{"role": "assistant", "content": char_info.get("first_message", "대화를 시작합니다.")}]
live_state = initial_state
save_json(chat_file, messages)
save_json(state_file, live_state)
st.rerun()

with col_chat:
st.title(f"📖 {selected_char}")
st.caption(f"세계관: {world_name} | {world_desc}")

# 메시지 표시
for msg in messages:
with st.chat_message(msg["role"]):
st.markdown(msg["content"])

# 입력 처리
if prompt := st.chat_input("행동이나 대화를 입력하세요... (예: 가방에서 낡은 열쇠를 꺼내 건네며 이거 찾아왔어.)"):
if not api_key:
st.error("사이드바에 Gemini API 키를 입력해주세요.")
st.stop()

# 유저 메시지 저장 및 렌더
messages.append({"role": "user", "content": prompt})
with st.chat_message("user"):
st.markdown(prompt)

client = genai.Client(api_key=api_key)

# 시스템 인스트럭션 구성 (실시간 상태가 매 턴 자동 주입됨)
system_prompt = f"""
당신은 TRPG 및 캐릭터 롤플레잉의 '{selected_char}'입니다.
설정된 세계관과 아래의 [실시간 누적 상태]를 철저히 지키며 사용자와 상호작용하세요.

[세계관: {world_name}]
{world_desc}

[캐릭터 기본 프로필]
{char_info['description']}

[실시간 누적 상태 및 기억]
• 현재 위치: {live_state.get('current_location')}
• 현재 유저와의 관계/호감도: {live_state.get('relationship_status')}
• 소지품/단서: {', '.join(live_state.get('inventory_and_items', []))}
• 과거 핵심 사건/기억: {'; '.join(live_state.get('key_memories', []))}

[행동 규칙]
1. AI 언어모델임을 절대 드러내지 말고, 캐릭터의 1인칭으로만 반응합니다.
2. 상대방의 행동이나 전달 물품에 적절히 반응하고, 필요시 행동 지문(지문)을 작성하세요.
3. 누적된 기억과 관계 변화를 자연스럽게 반영하여 대화하세요.
"""

# 대화 히스토리 구성
contents = []
for m in messages:
role = "user" if m["role"] == "user" else "model"
contents.append(types.Content(
role=role,
parts=[types.Part.from_text(text=m["content"])]
))

with st.chat_message("assistant"):
with st.spinner("생각 중..."):
response = client.models.generate_content(
model=MODEL_NAME,
contents=contents,
config=types.GenerateContentConfig(
system_instruction=system_prompt,
temperature=0.85
)
)
reply = response.text
st.markdown(reply)

messages.append({"role": "assistant", "content": reply})
save_json(chat_file, messages)

# 백그라운드: 실시간 상태 추출 및 동기화 저장
with st.spinner("실시간 상태 및 기억 저장 중..."):
updated_state = update_dynamic_state(
client=client,
char_name=selected_char,
world_name=world_name,
current_state=live_state,
user_msg=prompt,
ai_reply=reply
)
save_json(state_file, updated_state)

st.rerun()