
import streamlit as st
from PyPDF2 import PdfReader

from langchain.text_splitter import CharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

#from langchain_community.embeddings import HuggingFaceInstructEmbeddings
#from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
#from langchain_community.llms.huggingface_hub import HuggingFaceHub
from htmlTemplates import css, bot_template, user_template

from langchain_groq import ChatGroq


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size = 1000,
        chunk_overlap = 200,
        length_function = len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    #embeddings = HuggingFaceInstructEmbeddings(model_name= "hkunlp/instructor-xl")
    embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts = text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    llm = ChatGroq(
    groq_api_key='Groq_API_KEY',
    model_name= 'gemma2-9b-it'
    )
    #llm = HuggingFaceHub(repo_id = "distilbert/distilgpt2" ,model_kwargs={"temperature":0.5, "max_length" : 512})
    memory = ConversationBufferMemory(memory_key = "chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever = vectorstore.as_retriever(),
        memory = memory  
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response ['chat_history']

    for i, message in enumerate (st.session_state.chat_history):
        if i%2 == 0:
            st.write(user_template.replace("{{MSG}}",message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}",message.content), unsafe_allow_html=True)

def main():
    st.set_page_config(page_title = "Chat with Multiple PDFs",page_icon=":books:")

    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with Multiple PDFs: ")
    user_question = st.text_input("Ask a Question: ")

    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your Documents")
        pdf_docs = st.file_uploader("Upload Your PDFs",accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("processing"):
            #get pdf text
                raw_text= get_pdf_text(pdf_docs)
            #get text chunks
                text_chunks = get_text_chunks(raw_text)
            #create vector store
                vectorstore = get_vectorstore(text_chunks)
            #create Conversation Chain
                st.session_state.conversation= get_conversation_chain(vectorstore)

if __name__ == '__main__':
    main()