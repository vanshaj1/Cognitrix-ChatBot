#*********************** Libraries *************************
# import pandas as pd
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import CSVLoader
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
# from langchain.chains.question_answering import load_qa_chain
# from langchain.chains import RetrievalQA
# from langchain import PromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


#************************ Model *************************
Gemini_pro_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                                        google_api_key="AIzaSyDzePu9FJjmdFb0nYtUcxERtn_vn8cbYto",
                                        temperature=0,
                                        convert_system_message_to_human=True,
                                        safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    })

GeminiEmbeddingModel = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key="AIzaSyDzePu9FJjmdFb0nYtUcxERtn_vn8cbYto")


#************************** Logic *****************************
loader = CSVLoader("transcripts/transcripts.csv")
documents = loader.load()

vector_index = Chroma.from_documents(documents, GeminiEmbeddingModel)

prompt = ChatPromptTemplate.from_template("""Explain the about the Question and Give its detailed answer with the at least two link provided in context but links are mandatory to give:

<context>
{context}
</context>

Question: {input}""")

document_retrieval_chain = create_stuff_documents_chain(Gemini_pro_llm, prompt)

retriever = vector_index.as_retriever()
Question_Answer_Chain = create_retrieval_chain(retriever, document_retrieval_chain)



#***************** Ask Query function *****************
def ask_Query(Query):
    question = Query
    result = Question_Answer_Chain.invoke({"input": question})
    return result["answer"]




