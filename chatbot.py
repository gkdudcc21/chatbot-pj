import time
import uuid
import streamlit as st
from llm import stream_ai_message
import yaml

st.set_page_config(page_title='이혼 상담 챗봇', page_icon='🌟')
st.markdown("""
    <h1 style='text-align: center; color: #4b0082;'> 당신과 함께하는 도움챗봇 🌟 </h1>
    <p style='text-align: center; font-size: 18px; color: gray;'> 혼자가 아닙니다. 마음이 힘든 당신을 도와드립니다.</p>
""", unsafe_allow_html=True)


FAQ_LIST = [
    "이혼하려면 어떻게 해야 하나요?",
    "양육권은 누가 가지게 되나요?",
    "재산 분할은 어떻게 진행되나요?"
]

query_params = st.query_params

if 'session_id' in query_params:
    session_id = query_params['session_id']
else:
    session_id = str(uuid.uuid4())
    st.query_params.update({'session_id':session_id})

if 'session_id' not in st.session_state:
    st.session_state['session_id'] = session_id
else:
    session_id = st.session_state['session_id']

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

## 이전 채팅 내용 화면 출력 
for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def load_faq_list(file_path="faq.yaml"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("faq", [])

## FAQ 버튼 영역
st.subheader("🔎 자주 묻는 질문")
user_question = None
for faq in FAQ_LIST:
    if st.button(faq):
        user_question = faq

## 채팅 메시지 ====================================================================
placeholder = '이혼과 관련된 질문을 작성해 주세요.'
chat_input = st.chat_input(placeholder=placeholder)
if chat_input:
    user_question = chat_input
    
if user_question:  
    with st.chat_message('user'):
        ## 사용자 메시지 화면 출력
        st.markdown(user_question)
    st.session_state.message_list.append({'role': 'user', 'content': user_question})
    
    ## AI 메시지
    with st.spinner('💬 조금만 기다려주세요. 제가 도와드리겠습니다.'):
        session_id = st.session_state.session_id
        
        with st.chat_message('ai'):
            ## AI 메시지 화면 출력
            ai_response_box = st.empty()
            ai_message = ""

            for chunk in stream_ai_message(user_question, session_id=session_id):
                ai_message += chunk
                ai_response_box.markdown(ai_message + "▌")  
                time.sleep(0.05)  
            ai_response_box.markdown(ai_message)

    st.session_state.message_list.append({
        'role': 'ai',
        'content': ai_message
    })

print(f'after:{st.session_state.message_list}')
print("현재 세션 ID:", session_id)