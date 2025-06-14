import os

from dotenv import load_dotenv
from langchain.chains import (create_history_aware_retriever,
                              create_retrieval_chain)
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()


def get_llm(model: str = "gpt-4o"):
    return ChatOpenAI(model=model, temperature=0.7)


## database 함수 정의 ==================================================================
def get_database():
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

    ## 임베딩 모델 지정
    embedding = OpenAIEmbeddings(model="text-embedding-3-large")
    Pinecone(api_key=PINECONE_API_KEY)
    index_name = 'chatbot'

    database = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding,
    )

    return database

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def get_history_retriever(llm, retriever):
    contextualize_q_system_prompt = (
    "다음은 이혼 상담 대화 내용입니다.\n"
    "사용자가 방금 입력한 질문은 이전 대화 내용을 참고하고 있을 수 있습니다.\n"
    "이 질문을 단독으로도 이해할 수 있도록 다시 작성해 주세요.\n"
    "단, 질문에 직접적으로 답하지는 마세요.\n"
    "질문을 재구성할 필요가 없다면 그대로 반환해 주세요."
)      
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
    history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

    return history_aware_retriever

def get_qa_prompt():
    system_prompt = (
    '''[identity]
- 당신은 이혼 전문 법률 전문가입니다.
- [context]를 참고하여 사용자의 질문에 답변하세요.
- 마음이 힘든 사용자의 마음을 위로해주며 부드러우면서 정확하게 답변하세요.
- 답변에는 해당 조항을 '(xx법 제 x조 제 x호, xx법 제 x조 제 x호)'형식으로 문단 마지막에 적어주세요.
- 항목별로 표시해서 답변해주세요.
- 이혼법률 이외에의 질문에는 '이혼과 관련된 질문을 해주세요.'로 답변하세요.
[Context]\n{context} 
'''
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    return qa_prompt

def build_conversational_chain(): 
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')

    llm = get_llm()

    ## vector store에서 index 정보
    database = get_database()
    retriever = database.as_retriever(search_kwargs={"k": 3})

    history_aware_retriever = get_history_retriever(llm, retriever)

    qa_prompt = get_qa_prompt()

    ## LLM 모델 
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key='answer',
    ).pick('answer')

    return conversational_rag_chain

def stream_ai_message(user_message, session_id='default'):

    qa_chain = build_conversational_chain()
    for chunk in qa_chain.stream(
        {"input": user_message},
        config={"configurable": {"session_id": session_id}}
    ):
        yield chunk
   
    print(f'대화 이력 >> { get_session_history(session_id)}\n\n')
