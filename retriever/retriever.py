# retriever.py

import os
from typing import List, Tuple
from .conf import RetrieverConfig
import uuid

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = ""

from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
# SPLITTERS (nuevo paquete separado)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownTextSplitter,
    TokenTextSplitter,
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Qdrant     
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, Filter, FilterSelector
from langchain_core.documents import Document as LCDocument
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# from langchain.retrievers.document_compressors import CrossEncoderReranker
# from langchain.retrievers import ContextualCompressionRetriever


class Retriever():
    """
    Handles: loading PDFs, chunking, building the Qdrant vector store and exposing
    a LangChain retriever.
    """
    def __init__(self, cfg: RetrieverConfig):
        """
        Build the retriever from disk PDFs (if any).
        Inputs:
            cfg (RetrieverConfig): configuration for paths, embeddings and vector store.
        Outputs: None
        """
        # Retriever configuration
        self.cfg = cfg              
        # Load documents from the 'data' directory
        self.all_document_pages = self.load_documents_from_directory(self.cfg.data_path)
        # Create chunks from the loaded documents
        self.chunks = self.create_chunks_splits(self.all_document_pages, chunk_size=1000, chunk_overlap=200, splitter='recursive')
        # Build the Qdrant retriever
        self.client, self.retriever, self.vectorestore = self.build_retriever(chunks=self.chunks, collection_name=self.cfg.collection_name, path=self.cfg.index_path)
                    
    def close(self) -> None:
            """Close the client session to avoid resource leaks and warnings."""
            self.client.close()

    def load_documents_from_directory(self, directory_path): 
        """
        Load all PDF documents from a given directory (recursive).
        Inputs:
            directory_path (Path|str): folder containing PDFs.
        Outputs:
            list[Document]: all pages loaded as LangChain Documents.
        """
        loader = DirectoryLoader(
                str(directory_path), 
                glob="**/*.pdf",          
                loader_cls=PyPDFLoader
            )
        return loader.load()
    
    def load_documents_from_gradio(self, documents):
        """
        Load PDFs uploaded via Gradio file input.
        Inputs:
            documents (list[str|Path]): paths provided by Gradio.
        Outputs:
            list[Document]: all pages loaded.
        """
        docs = []
        for i in documents:
            loader = PyPDFLoader(i)
            pages = loader.load()
            docs.extend(pages)
        return docs

    def create_chunks_splits(
        self, 
        documents, 
        chunk_size=1000, 
        chunk_overlap=200, 
        splitter = 'recursive'): 
        """
        Split documents into smaller chunks for retrieval.
        Inputs:
            documents (list[Document])
            chunk_size (int)
            chunk_overlap (int)
            splitter (str): 'recursive' | 'character' | 'markdown' | 'token'
        Outputs:
            list[Document]: chunked documents with metadata preserved.
        """
        if splitter == 'recursive':
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        elif splitter == 'character':
            text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            
        elif splitter == 'markdown':
            text_splitter = MarkdownTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)

        elif splitter == 'token':
            text_splitter = TokenTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap)
        else:
            raise ValueError("Invalid splitter type. Choose from 'recursive', 'character', 'markdown', or 'token'.")
        
        return text_splitter.split_documents(documents)
        
        
    def build_retriever(self, chunks, collection_name, path):
        """
        Build a Qdrant retriever using Google embeddings and a local Qdrant instance.
        Inputs:
            chunks (list[Document])
            collection_name (str)
            path (Path|str): local DB path for Qdrant
        Outputs:
            (QdrantClient, BaseRetriever)
        """
        # 1) Initialize Google Generative AI Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model=self.cfg.embed_model)

        # 2) Initialize Qdrant client (local instance)
        client = QdrantClient(
            path=str(path),                          
            prefer_grpc=self.cfg.prefer_grpc,       
        )

        # 3) Create the collection (Only if it doesnt exits)
        if not client.collection_exists(collection_name):
            embedding_dim = len(embeddings.embed_query("Hello, world!"))
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
            
        # 3.1) If reset_collection=True, delete all points in the collection
        if self.cfg.reset_collection:
            client.delete(
                collection_name=collection_name,
                points_selector=FilterSelector(filter=Filter(must=[])),
                wait=True,  
            )

        # 4) Create Qdrant vectorstore from chunks 
        vectorestore = Qdrant(
            embeddings=embeddings,
            client=client,
            collection_name=collection_name
        )

        # 7) Index initial chunks only if empty
        if (client.count(collection_name=self.cfg.collection_name,exact=True,).count == 0):
             ids = self._make_ids(chunks)
             vectorestore.add_documents(chunks, ids=ids)

        # 5) Safe kwargs for retriever

        # Using rerank
        if self.cfg.use_reranker:
            kwargs = {"k": self.cfg.vectore_store_k * 4}

        # Using mmr or similarity
        else :
            # Just similarity
            kwargs = {"k": self.cfg.vectore_store_k }

            # Using mmr
            if self.cfg.vectore_store_search_type == "mmr":
                kwargs.update({
                    "k": self.cfg.vectore_store_k,
                    "fetch_k": self.cfg.vectore_store_fetch_k,
                    "lambda_mult": float(self.cfg.vectore_store_lambda_mult),
                })

        # 6) Create retriever from vectorestore
        base_retriever = vectorestore.as_retriever(
            search_type= self.cfg.vectore_store_search_type,
            search_kwargs=kwargs,
        )
        
        # 7) Optional: cross-encoder reranking
        ''' if self.cfg.use_reranker:
            cross_encoder = HuggingFaceCrossEncoder(
                model_name=self.cfg.reranker_model
            )
            compressor = CrossEncoderReranker(
                model=cross_encoder,
                top_n= self.cfg.reranker_top_k,
            )

            retriever = ContextualCompressionRetriever(
                base_retriever=base_retriever,
                base_compressor=compressor,
            )
        else:
            retriever = base_retriever'''
        
        retriever = base_retriever
        return client, retriever, vectorestore
    
    def add_chunks_into_vectorestorage(self,chunks) -> str:
        """
        Add new chunks to the existing vector store.
        Inputs:
            chunks (list[Document])
        Outputs:
            str: status message.
        """
        ids = self._make_ids(chunks)
        self.vectorestore.add_documents(chunks, ids=ids)
        return 'New chunks have been uploaded into the Retriever'

    
    def _make_ids(self, chunks):
        """
        Generate deterministic, human-traceable IDs for document chunks.
        Inputs:
            chunks (list[Document]): must contain metadata keys 'source', 'page', 'start_index'.
        Outputs:
            list[str]: stable UUIDv5 identifiers aligned with the input order.
        """
        ids = []
        for i, d in enumerate(chunks):
            src   = d.metadata.get("source", "doc")
            page  = d.metadata.get("page", -1)
            start = d.metadata.get("start_index", i)
            key = f"{src}|p{page}|s{start}"
            ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, key)))
        return ids

    def get_relevant_documents(self, query:str):
        """
        Retrieve relevant documents for a query using the underlying retriever.
        Inputs:
            query (str)
        Outputs:
            list[Document]
        """
        return self.retriever.invoke(query)
    

    def vector_count(self) -> int:
        """
        Number of vectors (points) currently stored in the collection.
        Inputs:  None
        Outputs: int
        """
        return self.client.count(
            collection_name=self.cfg.collection_name,
            exact=True,  
        ).count