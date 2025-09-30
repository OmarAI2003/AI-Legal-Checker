#!/usr/bin/env python3
"""
Simple RAG-Enhanced Assessment Agent
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError

def create_simple_rag_agent():
    """Create a simple RAG-enhanced assessment agent"""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    knowledge_base_id = os.environ.get('EGYPTIAN_LAW_KB_ID', 'QJWEBKNQ1N')
    
    # Simple agent configuration
    agent_config = {
        "agentName": "ragassessment",
        "description": "وكيل تقييم العقود مع قاعدة المعرفة",
        "instruction": """أنت وكيل ذكي متخصص في تقييم العقود القانونية المصرية.

مهامك:
1. تحليل العقد للبحث عن المخاطر القانونية
2. مقارنة العقد مع عقود مشابهة في قاعدة المعرفة
3. تقديم تقييم شامل للمخاطر
4. تقديم توصيات محددة

استخدم قاعدة المعرفة للحصول على أمثلة من العقود المشابهة وأفضل الممارسات.

قم بالرد باللغة العربية بشكل منظم ومهني.""",
        "foundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
        "idleSessionTTLInSeconds": 1800
    }
    
    try:
        print(f"Creating simple RAG agent with knowledge base: {knowledge_base_id}")
        
        # Create agent
        response = bedrock_agent.create_agent(**agent_config)
        agent_id = response['agent']['agentId']
        
        print(f"Agent created with ID: {agent_id}")
        
        # Associate knowledge base
        print("Associating knowledge base...")
        bedrock_agent.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            knowledgeBaseId=knowledge_base_id,
            description="قاعدة المعرفة للعقود القانونية المصرية",
            knowledgeBaseState="ENABLED"
        )
        
        print("Knowledge base associated successfully!")
        
        # Prepare agent
        print("Preparing agent...")
        bedrock_agent.prepare_agent(agentId=agent_id)
        
        print(f"✅ RAG Agent deployed successfully!")
        print(f"Agent ID: {agent_id}")
        print(f"Agent ARN: {response['agent']['agentArn']}")
        
        # Save config
        config = {
            'agent_id': agent_id,
            'agent_arn': response['agent']['agentArn'],
            'knowledge_base_id': knowledge_base_id,
            'status': 'success'
        }
        
        with open('simple_rag_agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return config
        
    except ClientError as e:
        print(f"Error: {e}")
        return {'status': 'error', 'error': str(e)}

if __name__ == "__main__":
    result = create_simple_rag_agent()
    print(json.dumps(result, indent=2, ensure_ascii=False))