"""
Document processors for loading and splitting different document types.
"""
import os
import logging
import copy
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    TextLoader
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Default chunk settings
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.ppt', '.xlsx', '.xls', '.html', '.htm', '.txt'}

# Initialize text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=DEFAULT_CHUNK_SIZE, 
    chunk_overlap=DEFAULT_CHUNK_OVERLAP, 
    length_function=len
)

def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize metadata keys to ensure consistency across different document loaders
    """
    normalized = {}
    
    # Normalize page/page_number
    if 'page' in metadata:
        normalized['page'] = metadata['page']
    if 'page_number' in metadata:
        normalized['page'] = metadata['page_number']
    
    # Preserve other keys
    for key, value in metadata.items():
        if key not in ['page', 'page_number'] or key not in normalized:
            normalized[key] = value
    
    return normalized

def preserve_minimal_metadata(document):
    """
    Create a copy of the document with only essential metadata
    to avoid serialization issues with some metadata fields
    """
    doc_copy = copy.deepcopy(document)
    
    # Get original metadata
    original_metadata = document.metadata
    
    # Create new metadata with only essential fields
    essential_metadata = {
        "source": original_metadata.get("source", ""),
        "page": original_metadata.get("page", original_metadata.get("page_number", 0)),
        "title": original_metadata.get("title", os.path.basename(original_metadata.get("source", ""))),
    }
    
    # Add document_id if present
    if "document_id" in original_metadata:
        essential_metadata["document_id"] = original_metadata["document_id"]
    
    # Update document copy with essential metadata
    doc_copy.metadata = essential_metadata
    
    return doc_copy

def chunk_page(page, chunk_size=2000, chunk_overlap=200):
    """
    Chunk a document page with specified size and overlap
    """
    # Create a text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return splitter.split_documents([page])

def pdf_chunking(file_path):
    """Load and chunk a PDF file"""
    try:
        logger.info(f"Loading PDF: {file_path}")
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # Process each page
        chunks = []
        for page in pages:
            page_chunks = chunk_page(page)
            chunks.extend(page_chunks)
        
        # Clean metadata to avoid serialization issues
        clean_chunks = [preserve_minimal_metadata(chunk) for chunk in chunks]
        
        return clean_chunks
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        return []

def doc_chunking(file_path):
    """Load and chunk a Word document"""
    try:
        logger.info(f"Loading Word document: {file_path}")
        loader = Docx2txtLoader(file_path)
        document = loader.load()
        
        # Add page metadata if missing
        for i, doc in enumerate(document):
            if 'page' not in doc.metadata:
                doc.metadata['page'] = i + 1
        
        # Split into chunks
        chunks = text_splitter.split_documents(document)
        
        # Clean metadata
        clean_chunks = [preserve_minimal_metadata(chunk) for chunk in chunks]
        
        return clean_chunks
    except Exception as e:
        logger.error(f"Error processing Word document {file_path}: {str(e)}")
        return []

def ppt_chunking(file_path):
    """Load and chunk a PowerPoint file, creating one chunk per page"""
    try:
        logger.info(f"Loading PowerPoint: {file_path}")
        loader = UnstructuredPowerPointLoader(file_path)
        slides = loader.load()
        
        # Process each slide
        chunks = []
        for i, slide in enumerate(slides):
            # Ensure slide has page metadata
            if 'page' not in slide.metadata:
                slide.metadata['page'] = i + 1
            
            # For PowerPoint, we might want to keep slides as single chunks
            # But if slides are very large, we can split them
            if len(slide.page_content) > DEFAULT_CHUNK_SIZE * 2:
                slide_chunks = chunk_page(slide)
                chunks.extend(slide_chunks)
            else:
                chunks.append(slide)
        
        # Clean metadata
        clean_chunks = [preserve_minimal_metadata(chunk) for chunk in chunks]
        
        return clean_chunks
    except Exception as e:
        logger.error(f"Error processing PowerPoint {file_path}: {str(e)}")
        return []

def excel_chunking(file_path):
    """Load an Excel file as a single chunk"""
    try:
        logger.info(f"Loading Excel file: {file_path}")
        loader = UnstructuredExcelLoader(file_path)
        sheets = loader.load()
        
        # Add page metadata if missing
        for i, sheet in enumerate(sheets):
            if 'page' not in sheet.metadata:
                sheet.metadata['page'] = i + 1
        
        # Split into chunks
        chunks = text_splitter.split_documents(sheets)
        
        # Clean metadata
        clean_chunks = [preserve_minimal_metadata(chunk) for chunk in chunks]
        
        return clean_chunks
    except Exception as e:
        logger.error(f"Error processing Excel file {file_path}: {str(e)}")
        return []

def html_chunking(file_path):
    """Load and chunk an HTML file"""
    try:
        logger.info(f"Loading HTML file: {file_path}")
        loader = UnstructuredHTMLLoader(file_path)
        html_doc = loader.load()
        
        # Add page metadata if missing
        for doc in html_doc:
            if 'page' not in doc.metadata:
                doc.metadata['page'] = 1
        
        # Split into chunks
        chunks = text_splitter.split_documents(html_doc)
        
        # Clean metadata
        clean_chunks = [preserve_minimal_metadata(chunk) for chunk in chunks]
        
        return clean_chunks
    except Exception as e:
        logger.error(f"Error processing HTML file {file_path}: {str(e)}")
        return []

def text_chunking(file_path):
    """Load and chunk a text file"""
    try:
        logger.info(f"Loading text file: {file_path}")
        loader = TextLoader(file_path)
        text_doc = loader.load()
        
        # Add page metadata if missing
        for doc in text_doc:
            if 'page' not in doc.metadata:
                doc.metadata['page'] = 1
        
        # Split into chunks
        chunks = text_splitter.split_documents(text_doc)
        
        # Clean metadata
        clean_chunks = [preserve_minimal_metadata(chunk) for chunk in chunks]
        
        return clean_chunks
    except Exception as e:
        logger.error(f"Error processing text file {file_path}: {str(e)}")
        return []

def load_and_split_document(file_path: str) -> List[Document]:
    """
    Load and split a document based on file extension
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.error(f"Unsupported file extension: {file_ext}")
            return []
        
        # Process based on file extension
        if file_ext == '.pdf':
            return pdf_chunking(file_path)
        elif file_ext == '.docx':
            return doc_chunking(file_path)
        elif file_ext in ['.pptx', '.ppt']:
            return ppt_chunking(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            return excel_chunking(file_path)
        elif file_ext in ['.html', '.htm']:
            return html_chunking(file_path)
        elif file_ext == '.txt':
            return text_chunking(file_path)
        else:
            logger.error(f"Unsupported file extension: {file_ext}")
            return []
    except Exception as e:
        logger.error(f"Error loading document {file_path}: {str(e)}")
        return []
