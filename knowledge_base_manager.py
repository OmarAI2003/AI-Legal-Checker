#!/usr/bin/env python3
"""
Knowledge Base Manager for Egyptian Legal Contracts
Creates and manages Bedrock Knowledge Base for RAG functionality
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError

class KnowledgeBaseManager:
    def __init__(self, region='us-west-2'):
        self.region = region
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.opensearch = boto3.client('opensearchserverless', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        
    def create_knowledge_base(self, name="egyptian-legal-contracts", bucket_name=None):
        """Create a new knowledge base for Egyptian legal contracts"""
        
        if not bucket_name:
            bucket_name = os.environ.get('KB_BUCKET', 'egyptian-legal-analyzer-knowledge-base')
        
        # Knowledge base configuration
        kb_config = {
            "name": name,
            "description": "قاعدة معرفة للعقود القانونية المصرية",
            "roleArn": self._get_or_create_kb_role(),
            "knowledgeBaseConfiguration": {
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1"
                }
            },
            "storageConfiguration": {
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration": {
                    "collectionArn": self._get_or_create_collection(),
                    "vectorIndexName": "egyptian-legal-index",
                    "fieldMapping": {
                        "vectorField": "embedding",
                        "textField": "text",
                        "metadataField": "metadata"
                    }
                }
            }
        }
        
        try:
            print(f"Creating knowledge base: {name}")
            response = self.bedrock_agent.create_knowledge_base(**kb_config)
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            
            print(f"Knowledge base created: {kb_id}")
            
            # Create data source
            self._create_data_source(kb_id, bucket_name)
            
            return {
                'knowledge_base_id': kb_id,
                'bucket_name': bucket_name,
                'status': 'created'
            }
            
        except ClientError as e:
            print(f"Error creating knowledge base: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _create_data_source(self, kb_id, bucket_name):
        """Create S3 data source for the knowledge base"""
        
        data_source_config = {
            "knowledgeBaseId": kb_id,
            "name": "egyptian-contracts-source",
            "description": "مصدر البيانات للعقود القانونية المصرية",
            "dataSourceConfiguration": {
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{bucket_name}",
                    "inclusionPrefixes": ["legal-contracts/"]
                }
            },
            "vectorIngestionConfiguration": {
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 300,
                        "overlapPercentage": 20
                    }
                }
            }
        }
        
        try:
            response = self.bedrock_agent.create_data_source(**data_source_config)
            data_source_id = response['dataSource']['dataSourceId']
            print(f"Data source created: {data_source_id}")
            return data_source_id
            
        except ClientError as e:
            print(f"Error creating data source: {e}")
            return None
    
    def _get_or_create_kb_role(self):
        """Get or create IAM role for knowledge base"""
        # This would typically return the ARN of the role created in CloudFormation
        # For now, return a placeholder that should be replaced with actual role ARN
        return "arn:aws:iam::ACCOUNT_ID:role/BedrockKnowledgeBaseRole"
    
    def _get_or_create_collection(self):
        """Get or create OpenSearch Serverless collection"""
        collection_name = "egyptian-legal-collection"
        
        try:
            # Check if collection exists
            response = self.opensearch.list_collections()
            for collection in response.get('collectionSummaries', []):
                if collection['name'] == collection_name:
                    return collection['arn']
            
            # Create new collection
            collection_config = {
                "name": collection_name,
                "type": "VECTORSEARCH",
                "description": "مجموعة البحث المتجه للعقود القانونية المصرية"
            }
            
            response = self.opensearch.create_collection(**collection_config)
            collection_arn = response['createCollectionDetail']['arn']
            
            # Wait for collection to be active
            print("Waiting for OpenSearch collection to be active...")
            time.sleep(60)
            
            return collection_arn
            
        except ClientError as e:
            print(f"Error with OpenSearch collection: {e}")
            return None
    
    def upload_sample_contracts(self, bucket_name, kb_id):
        """Upload sample legal contracts to the knowledge base"""
        
        sample_contracts = [
            {
                "filename": "contract_employment_template.txt",
                "content": """عقد عمل نموذجي - مصر

الأطراف:
الطرف الأول: [اسم الشركة]
الطرف الثاني: [اسم الموظف]

البنود الأساسية:
1. طبيعة العمل: [وصف الوظيفة]
2. الراتب: [المبلغ] جنيه مصري شهرياً
3. مدة العقد: [المدة]
4. ساعات العمل: 8 ساعات يومياً، 6 أيام أسبوعياً
5. الإجازات: 21 يوم سنوياً + الإجازات الرسمية

الشروط الإضافية:
- فترة تجربة: 3 أشهر
- إشعار الإنهاء: شهر واحد
- التأمين الاجتماعي: وفقاً للقانون المصري
- السرية: المحافظة على أسرار العمل

البنود المخاطرة:
- عدم تحديد مكان العمل بوضوح
- عدم ذكر آلية مراجعة الراتب
- عدم تحديد المسؤوليات بالتفصيل

التوصيات:
- إضافة بند تحديد مكان العمل
- تحديد آلية مراجعة الراتب السنوية
- تفصيل المسؤوليات والواجبات"""
            },
            {
                "filename": "contract_rental_template.txt", 
                "content": """عقد إيجار نموذجي - مصر

الأطراف:
المؤجر: [اسم المالك]
المستأجر: [اسم المستأجر]

تفاصيل العقار:
العنوان: [العنوان الكامل]
المساحة: [المساحة] متر مربع
الغرض: سكني/تجاري/إداري

الشروط المالية:
قيمة الإيجار: [المبلغ] جنيه مصري شهرياً
التأمين: [مبلغ التأمين]
طريقة السداد: [شهري/ربع سنوي/سنوي]

مدة العقد:
تاريخ البداية: [التاريخ]
تاريخ النهاية: [التاريخ]
التجديد: [شروط التجديد]

الالتزامات:
التزامات المؤجر:
- صيانة الهيكل الأساسي
- توفير المرافق الأساسية
- عدم التدخل في الاستخدام السلمي

التزامات المستأجر:
- دفع الإيجار في المواعيد
- المحافظة على العقار
- عدم التأجير من الباطن بدون إذن

البنود المخاطرة:
- عدم تحديد مسؤوليات الصيانة بوضوح
- عدم ذكر آلية زيادة الإيجار
- غموض في شروط الإنهاء المبكر

أفضل الممارسات:
- تحديد قائمة تفصيلية بحالة العقار
- إضافة بند فض النزاعات
- تحديد نسبة الزيادة السنوية المسموحة"""
            },
            {
                "filename": "contract_partnership_template.txt",
                "content": """عقد شراكة نموذجي - مصر

الأطراف:
الشريك الأول: [الاسم والصفة]
الشريك الثاني: [الاسم والصفة]

طبيعة الشراكة:
نوع النشاط: [وصف النشاط التجاري]
اسم الشركة: [اسم الشركة]
رأس المال: [المبلغ الإجمالي]

توزيع الحصص:
الشريك الأول: [نسبة]% - [مبلغ المساهمة]
الشريك الثاني: [نسبة]% - [مبلغ المساهمة]

الإدارة والمسؤوليات:
- تحديد صلاحيات كل شريك
- آلية اتخاذ القرارات
- توقيعات معتمدة للمعاملات البنكية

توزيع الأرباح والخسائر:
- توزيع الأرباح حسب نسب الحصص
- تحمل الخسائر بنفس النسب
- آلية إعادة استثمار الأرباح

إنهاء الشراكة:
- أسباب الإنهاء
- آلية تقييم الأصول
- حقوق الشريك المنسحب

المخاطر الشائعة:
- عدم تحديد آلية حل النزاعات
- غموض في صلاحيات الإدارة
- عدم وضوح إجراءات الانسحاب

التوصيات:
- إضافة بند التحكيم للنزاعات
- تحديد آلية تقييم دورية للشركة
- وضع شروط واضحة لدخول شركاء جدد"""
            }
        ]
        
        try:
            for contract in sample_contracts:
                key = f"legal-contracts/{contract['filename']}"
                
                self.s3.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=contract['content'].encode('utf-8'),
                    ContentType='text/plain',
                    Metadata={
                        'contract-type': contract['filename'].split('_')[1],
                        'language': 'arabic',
                        'jurisdiction': 'egypt'
                    }
                )
                print(f"Uploaded: {contract['filename']}")
            
            # Trigger ingestion
            self._sync_knowledge_base(kb_id)
            
            return True
            
        except Exception as e:
            print(f"Error uploading contracts: {e}")
            return False
    
    def _sync_knowledge_base(self, kb_id):
        """Trigger knowledge base synchronization"""
        try:
            # Get data sources for the knowledge base
            response = self.bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            
            for data_source in response['dataSourceSummaries']:
                data_source_id = data_source['dataSourceId']
                
                # Start ingestion job
                self.bedrock_agent.start_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=data_source_id
                )
                print(f"Started ingestion for data source: {data_source_id}")
                
        except ClientError as e:
            print(f"Error syncing knowledge base: {e}")
    
    def list_knowledge_bases(self):
        """List all knowledge bases"""
        try:
            response = self.bedrock_agent.list_knowledge_bases()
            
            print("Available Knowledge Bases:")
            for kb in response['knowledgeBaseSummaries']:
                print(f"- ID: {kb['knowledgeBaseId']}")
                print(f"  Name: {kb['name']}")
                print(f"  Description: {kb.get('description', 'N/A')}")
                print(f"  Status: {kb['status']}")
                print()
                
            return response['knowledgeBaseSummaries']
            
        except ClientError as e:
            print(f"Error listing knowledge bases: {e}")
            return []
    
    def query_knowledge_base(self, kb_id, query):
        """Test query against knowledge base"""
        try:
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': query}
            )
            
            print(f"Query: {query}")
            print("Results:")
            for result in response['retrievalResults']:
                print(f"- Score: {result['score']}")
                print(f"  Content: {result['content']['text'][:200]}...")
                print()
                
            return response['retrievalResults']
            
        except ClientError as e:
            print(f"Error querying knowledge base: {e}")
            return []

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage Knowledge Base for Egyptian Legal Contracts')
    parser.add_argument('--create', action='store_true', help='Create new knowledge base')
    parser.add_argument('--list', action='store_true', help='List knowledge bases')
    parser.add_argument('--upload-samples', help='Upload sample contracts to KB ID')
    parser.add_argument('--query', nargs=2, metavar=('KB_ID', 'QUERY'), help='Query knowledge base')
    parser.add_argument('--bucket', help='S3 bucket name for knowledge base')
    
    args = parser.parse_args()
    
    manager = KnowledgeBaseManager()
    
    if args.create:
        result = manager.create_knowledge_base(bucket_name=args.bucket)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result['status'] == 'created':
            kb_id = result['knowledge_base_id']
            bucket_name = result['bucket_name']
            print(f"\nUploading sample contracts to KB {kb_id}...")
            manager.upload_sample_contracts(bucket_name, kb_id)
    
    elif args.list:
        manager.list_knowledge_bases()
    
    elif args.upload_samples:
        bucket_name = args.bucket or os.environ.get('KB_BUCKET')
        if bucket_name:
            manager.upload_sample_contracts(bucket_name, args.upload_samples)
        else:
            print("Error: Bucket name required")
    
    elif args.query:
        kb_id, query = args.query
        manager.query_knowledge_base(kb_id, query)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()