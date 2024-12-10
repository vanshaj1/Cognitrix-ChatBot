#*********************** Libraries *************************
import csv
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import CSVLoader
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
# from langchain.chains.question_answering import load_qa_chain
# from langchain.chains import RetrievalQA
# from langchain import PromptTemplate
import os

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
Question_Answer_Chain = None
 #*******************************Inference******************************
def init_LLM():
    global Question_Answer_Chain
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




init_LLM()

#***************** Ask Query function *****************
def ask_Query(Query):
    # change_detection()
    question = Query
    result = Question_Answer_Chain.invoke({"input": question})
    return result["answer"]



#******************* Utility functions ****************
# def change_detection():
#     original = "transcripts/transcripts.csv"
#     backup = "transcripts/transcripts_copy.csv"

#     #*******************Edge case*******************
#     if not os.path.exists(original):
#         raise FileNotFoundError("Data is not present,please add data first")
#     if not os.path.exists(backup):
#         # If file2 doesn't exist, create it by copying file1
#         print(f"{backup} does not exist. Creating it from {original}.")
#         df1 = pd.read_csv(original)
#         df1.to_csv(backup, index=False)
#         # init_LLM()
#         return
    
#     # Read the two CSV files
#     original_data = pd.read_csv(original)
#     backup_data = pd.read_csv(backup)

#     # Check if they have the same content
#     if backup_data.equals(original_data):
#         print("CSV files have the same content. No action taken.")
#     else:
#         print("CSV files differ.")
#         print("Adding data to csv...")
#         original_data.to_csv(backup, index=False)
#         print("Initializing LLM...")
#         init_LLM()


def read_csv(file_path):
    """Read a CSV file and return its content as a list of rows."""
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        return list(reader)

def write_csv(file_path, data):
    """Write data to a CSV file."""
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def change_detection():
    original = "transcripts/transcripts.csv"
    backup = "transcripts/transcripts_copy.csv"

    # Edge case: Check if original file exists
    if not os.path.exists(original):
        raise FileNotFoundError("Data is not present, please add data first.")

    # Check if backup file exists
    if not os.path.exists(backup):
        print(f"{backup} does not exist. Creating it from {original}.")
        original_data = read_csv(original)
        write_csv(backup, original_data)
        init_LLM()
        return

    # Read the contents of the two CSV files
    original_data = read_csv(original)
    backup_data = read_csv(backup)

    # Compare the content of the two files
    if original_data == backup_data:
        print("CSV files have the same content. No action taken.")
    else:
        print("CSV files differ.")
        print("Adding data to csv...")
        write_csv(backup, original_data)
        print("Initializing LLM...")
        init_LLM()