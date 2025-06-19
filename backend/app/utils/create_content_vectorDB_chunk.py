import os
import sys

# Add the project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.document_loaders import PyPDFLoader
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from uuid import uuid4
from langchain_core.documents import Document
from app.utils.get_embedding_model import hf
import traceback


def get_vector_store():
    # 检查是否存在已有的向量数据库
    db_path = os.path.join(os.path.dirname(current_dir), "fund_production_chunk")
    if os.path.exists(db_path):
        print("加载已有的向量数据库...")
        return FAISS.load_local(db_path, hf, allow_dangerous_deserialization=True)
    else:
        print("创建新的向量数据库...")
        index = faiss.IndexFlatL2(len(hf.embed_query("hello world")))
        return FAISS(
            embedding_function=hf,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )


def create_savepath(filename):
    savepath = filename.split("证券投资基金")
    if len(savepath) == 1:
        savepath = filename.split("债券型基金中基金(FOF)")
    return savepath


def create_overlapping_chunks(text, chunk_size=5000, overlap=500):
    """创建重叠的文本块"""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        # 如果不是最后一块，尝试在句子边界处分割
        # if end < text_length:
        #     # 在chunk_size范围内找最后一个句号
        #     last_period = text[start:end].rfind('。')
        #     if last_period != -1:
        #         end = start + last_period + 1

        if end > text_length:
            end = text_length

        chunks.append(text[start:end])
        if end == text_length:
            break
        # 移动窗口，考虑重叠部分
        start = end - overlap

    return chunks


def create_doc():
    # Get the absolute path to the docs directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    docs_dir = os.path.join(project_root, "docs1")
    docs_dir = r'E:\work\aill资料\珍奥AI投喂材料\珍奥AI投喂材料\已投喂\目录'
    if not os.path.exists(docs_dir):
        raise FileNotFoundError(f"Docs directory not found at {docs_dir}")

    documents = []
    i=0
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if not file.endswith(('.docx')):  # Only process Word documents
                continue
            filename = os.path.splitext(file)[0]
            print('name: ' + filename)
            #name, report = create_savepath(filename)  # 获取名称和报告期

            file_path = os.path.join(root, file)
            #loader = PyPDFLoader(file_path)
            loader =UnstructuredWordDocumentLoader(file_path)
            pages = loader.load()

            # 将所有页面的内容合并
            full_text = ""
            for page in pages:
                full_text += page.page_content + "\n"

            # 创建重叠的文本块
            chunks = create_overlapping_chunks(full_text)

            # 为每个块创建文档
            for i, chunk in enumerate(chunks):
                documents.append(Document(
                    page_content=chunk,
                    id=str(uuid4()),
                    metadata={
                        "name": f"production",
                        "chunk_index": i,
                        "source": filename
                    }
                ))
    return documents


if __name__ == "__main__":
    try:
        # 获取向量存储（新建或加载已有的）
        vector_store = get_vector_store()

        # 添加新文档
        print("添加新文档到向量数据库...")
        vector_store.add_documents(documents=create_doc())

        # 保存更新后的向量数据库
        print("保存向量数据库...")
        vector_store.save_local("../fund_production_chunk")
        print("完成！")
    except Exception as e:
        traceback.print_exc()

