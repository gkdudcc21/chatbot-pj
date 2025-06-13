import streamlit as st
from llm import get_ai_message


st.set_page_config(page_title='이혼 상담 챗봇', page_icon='🌟')
st.title("당신과 함께하는 도움챗봇🌟")

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

## 이전 채팅 내용 화면 출력 
for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])

## 채팅 메시지 ====================================================================
placeholder = '이혼과 관련된 질문을 작성해 주세요.'
if user_question := st.chat_input(placeholder=placeholder): ## prompt 창
    ## 사용자 메시지
    with st.chat_message('user'):
        ## 사용자 메시지 화면 출력
        st.write(user_question)
    st.session_state.message_list.append({'role': 'user', 'content': user_question})
    
    ## AI 메시지
    with st.spinner('조금만 기다려주세요. 제가 도와드리겠습니다.'):
        ai_message = get_ai_message(user_question)
        
        with st.chat_message('ai'):
            ## AI 메시지 화면 출력
            st.write(ai_message)
        st.session_state.message_list.append({'role': 'ai', 'content': ai_message})

print(f'after:{st.session_state.message_list}')

