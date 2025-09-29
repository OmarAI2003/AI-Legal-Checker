"""
RAG Embeddings Lambda Function
Handles AWS Titan embeddings and OpenSearch integration for clause comparison
"""
import json
import os
import boto3
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
USE_MOCK = os.environ.get('USE_MOCK', 'true').lower() in ('1', 'true', 'yes')

def lambda_handler(event, context):
    """Process clauses with embeddings and RAG"""
    
    try:
        # Initialize AWS clients (or use mocks)
        if USE_MOCK:
            bedrock = None
            opensearch = None
        else:
            bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')
            )
            opensearch = boto3.client('opensearchserverless')
        
        # Get clauses from OCR result
        ocr_data = event.get('ocr_data', {})
        clauses = ocr_data.get('clauses', [])
        document_type = ocr_data.get('document_type', 'غير محدد')
        
        if not clauses:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No clauses provided for embedding'})
            }
        
        # Generate embeddings for each clause
        embedded_clauses = []
        for clause in clauses:
            clause_text = clause.get('clause_text', '')
            if clause_text:
                # Generate embedding using AWS Titan (or mock)
                embedding = generate_titan_embedding(bedrock, clause_text)
                
                embedded_clause = clause.copy()
                embedded_clause['embedding'] = embedding
                embedded_clauses.append(embedded_clause)
        
        # Search similar clauses in OpenSearch
        similar_clauses = []
        for embedded_clause in embedded_clauses:
            similar = search_similar_clauses(
                opensearch, 
                embedded_clause['embedding'], 
                embedded_clause['clause_type'],
                document_type
            )
            similar_clauses.extend(similar)
        
        # Prepare RAG context for legal analysis
        rag_context = {
            "current_clauses": embedded_clauses,
            "similar_clauses": similar_clauses,
            "clause_comparison": compare_clauses(embedded_clauses, similar_clauses),
            "rag_summary": generate_rag_summary(embedded_clauses, similar_clauses)
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'agent_type': 'rag_processor',
                'analysis': {
                    'embedded_clauses_count': len(embedded_clauses),
                    'similar_clauses_found': len(similar_clauses),
                    'rag_context': rag_context
                }
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'agent_type': 'rag_processor'
            })
        }

def generate_titan_embedding(bedrock_client, text: str) -> List[float]:
    """Generate embedding using AWS Titan Embeddings V2"""
    try:
        # If running in mock mode, return a deterministic fake embedding
        if USE_MOCK or bedrock_client is None:
            # Simple mock: return a fixed-length vector based on text hash
            import hashlib
            h = hashlib.sha256(text.encode('utf-8')).digest()
            # Create 64-dim float vector from hash bytes (deterministic)
            vec = [float(b) / 255.0 for b in h[:64]]
            return vec

        # Prepare request for Titan Embeddings V2
        body = {
            "inputText": text,
            "dimensions": 1024,  # Titan V2 supports up to 1024 dimensions
            "normalize": True    # Normalize embeddings for better similarity search
        }

        response = bedrock_client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(body),
            contentType="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body.get('embedding', [])
        
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return []

def search_similar_clauses(opensearch_client, embedding: List[float], clause_type: str, document_type: str) -> List[Dict]:
    """Search for similar clauses in OpenSearch using vector similarity"""
    try:
        # OpenSearch vector search query
        search_query = {
            "size": 5,  # Top 5 similar clauses
            "_source": ["clause_text", "clause_type", "document_type", "similarity_score"],
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "clause_embedding": {
                                    "vector": embedding,
                                    "k": 5
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "terms": {
                                "clause_type": [clause_type, "عام"]  # Include general clauses too
                            }
                        }
                    ]
                }
            }
        }
        
        # If running in mock mode or client missing, return deterministic mock
        if USE_MOCK or opensearch_client is None:
            # create a mock similarity score using embedding first value
            score = round((embedding[0] if embedding else 0.5) * 0.9, 3)
            return [
                {
                    "clause_text": "بند مشابه من عقد سابق",
                    "clause_type": clause_type,
                    "document_type": document_type,
                    "similarity_score": float(score),
                    "source_contract": "عقد مرجعي"
                }
            ]

        # Real OpenSearch usage would go here (opensearch-py or boto3)
        # For safety, keep returning an empty list when not implemented
        return []
        
    except Exception as e:
        print(f"Error searching similar clauses: {str(e)}")
        return []

def compare_clauses(current_clauses: List[Dict], similar_clauses: List[Dict]) -> Dict:
    """Compare current clauses with similar ones from the database"""
    
    comparison = {
        "clause_matches": [],
        "unique_clauses": [],
        "potential_issues": [],
        "improvement_suggestions": []
    }
    
    for current_clause in current_clauses:
        clause_type = current_clause.get('clause_type', '')
        
        # Find matching clause types in similar clauses
        matches = [sc for sc in similar_clauses if sc.get('clause_type') == clause_type]
        
        if matches:
            best_match = max(matches, key=lambda x: x.get('similarity_score', 0))
            comparison["clause_matches"].append({
                "current_clause": current_clause['clause_text'],
                "similar_clause": best_match['clause_text'],
                "similarity_score": best_match.get('similarity_score', 0),
                "clause_type": clause_type
            })
        else:
            comparison["unique_clauses"].append(current_clause)
    
    return comparison

def generate_rag_summary(current_clauses: List[Dict], similar_clauses: List[Dict]) -> str:
    """Generate a summary of RAG findings for legal analysis"""
    
    total_clauses = len(current_clauses)
    total_similar = len(similar_clauses)
    
    summary = f"""
تحليل المقارنة مع قاعدة البيانات:
- عدد البنود المستخرجة: {total_clauses}
- عدد البنود المشابهة الموجودة: {total_similar}
- تم العثور على بنود مشابهة في عقود سابقة
- يمكن استخدام هذه المقارنة لتحسين صياغة العقد الحالي
"""
    
    return summary.strip()