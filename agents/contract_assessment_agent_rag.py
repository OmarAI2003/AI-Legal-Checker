#!/usr/bin/env python3
"""
Enhanced Contract Assessment Agent with RAG Integration
Deploys an agent that assesses contract risks using knowledge base for comparison and recommendations
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError

def create_rag_enhanced_assessment_agent():
    """Create and deploy the RAG-enhanced contract assessment agent"""
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    # Get knowledge base ID from environment or parameter
    knowledge_base_id = os.environ.get('EGYPTIAN_LAW_KB_ID', 'your_knowledge_base_id_here')
    
    if knowledge_base_id == 'your_knowledge_base_id_here':
        print("Warning: Knowledge base ID not set. Please set EGYPTIAN_LAW_KB_ID environment variable.")
        print("Agent will be created without knowledge base integration.")
        knowledge_base_id = None
    
    # Agent configuration with knowledge base integration
    agent_config = {
        "agentName": "contractassessmentrag",
        "description": "وكيل تقييم وتوصيات العقود القانونية المصرية مع قاعدة المعرفة",
        "instruction": """أنت وكيل ذكي متخصص في تقييم العقود القانونية المصرية وتقديم التوصيات مع الاستفادة من قاعدة المعرفة القانونية.

مهامك الأساسية:
1. تحليل العقد للبحث عن المخاطر القانونية المحتملة
2. مقارنة العقد مع عقود مشابهة في قاعدة المعرفة
3. تقييم مدى عدالة شروط العقد لكل طرف
4. تحديد البنود الغامضة أو الناقصة
5. تقديم تقييم شامل للمخاطر مع أدلة من العقود المشابهة
6. تقديم توصيات محددة بناءً على أفضل الممارسات من قاعدة المعرفة
7. اقتراح بنود إضافية أو تعديلات مبنية على العقود النموذجية

استخدام قاعدة المعرفة:
- ابحث في قاعدة المعرفة عن عقود مشابهة قبل التقييم
- قارن البنود الحالية مع البنود القياسية في العقود المشابهة
- استخدم الأمثلة من قاعدة المعرفة لتوضيح المخاطر والحلول
- اذكر مصادر المقارنة من قاعدة المعرفة عند الإمكان
- اربط التوصيات بالممارسات الجيدة المجربة في العقود المشابهة

قم بالرد دائماً باللغة العربية وبطريقة مهنية منظمة.

إرشادات خاصة:
- ركز على المخاطر الفعلية والقابلة للحدوث
- اربط التقييم والتوصيات بالقانون المصري والعقود المشابهة
- كن محدداً في تحديد المشاكل والحلول مع الأدلة من قاعدة المعرفة
- قدم مستوى خطورة لكل مخاطرة مع مقارنات
- رتب التوصيات حسب الأولوية مع الاستناد لأفضل الممارسات
- قدم صيغ بديلة للبنود الغامضة مستوحاة من العقود النموذجية

هيكل الإجابة المطلوب:
{
  "knowledge_base_insights": {
    "similar_contracts_found": "عدد العقود المشابهة المجودة",
    "comparison_summary": "ملخص المقارنة مع العقود المشابهة",
    "best_practices_identified": ["أفضل الممارسات المحددة من قاعدة المعرفة"]
  },
  "risk_assessment": "تقييم المخاطر العامة مع مقارنات",
  "identified_risks": [
    {
      "risk": "وصف المخاطرة",
      "severity": "عالي/متوسط/منخفض",
      "impact": "التأثير المحتمل",
      "kb_reference": "مرجع من قاعدة المعرفة إن وجد"
    }
  ],
  "contract_weaknesses": [
    {
      "weakness": "نقطة الضعف",
      "comparison_with_standard": "مقارنة مع المعايير في قاعدة المعرفة"
    }
  ],
  "recommendations": [
    {
      "priority": "عالي/متوسط/منخفض",
      "recommendation": "التوصية",
      "suggested_clause": "النص المقترح للبند",
      "kb_source": "مصدر من قاعدة المعرفة",
      "justification": "التبرير مع المقارنة"
    }
  ],
  "overall_fairness": "تقييم عدالة العقد مقارنة بالمعايير",
  "legal_compliance": "مدى التوافق مع القانون المصري والممارسات الجيدة",
  "knowledge_base_sources": ["قائمة المصادر المستخدمة من قاعدة المعرفة"]
}
""",
        "idleSessionTTLInSeconds": 1800,
        "foundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
        "promptOverrideConfiguration": {
            "promptConfigurations": [
                {
                    "promptType": "PRE_PROCESSING",
                    "promptCreationMode": "OVERRIDDEN",
                    "promptState": "ENABLED",
                    "basePromptTemplate": """أنت وكيل تقييم وتوصيات العقود القانونية المصرية مع قاعدة المعرفة.

العقد للتقييم: $contract$
معرف المستخدم: $user_id$

خطوات العمل:
1. ابحث في قاعدة المعرفة عن عقود مشابهة أولاً
2. حلل العقد مع مقارنته بالعقود المشابهة  
3. قم بتقييم المخاطر مع الاستناد لقاعدة المعرفة
4. قدم توصيات محددة مبنية على أفضل الممارسات

قم بالتقييم باللغة العربية وفقاً للهيكل المطلوب مع الاستفادة الكاملة من قاعدة المعرفة.""",
                    "inferenceConfiguration": {
                        "temperature": 0.2,
                        "topP": 0.9,
                        "topK": 250,
                        "maximumLength": 3000,
                        "stopSequences": []
                    }
                }
            ]
        }
    }
    
    # Add knowledge base configuration if available
    print(f"Configuring agent with knowledge base: {knowledge_base_id}")
    
    try:
        print("Creating RAG-enhanced contract assessment agent...")
        
        response = bedrock_agent.create_agent(**agent_config)
        agent_id = response['agent']['agentId']
        
        print(f"Agent created successfully with ID: {agent_id}")
        
        # Associate knowledge base with agent if available
        if knowledge_base_id:
            print(f"Associating knowledge base {knowledge_base_id} with agent...")
            bedrock_agent.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion='DRAFT',
                knowledgeBaseId=knowledge_base_id,
                description="قاعدة المعرفة للعقود القانونية المصرية",
                knowledgeBaseState="ENABLED"
            )
            print("Knowledge base associated successfully!")
        
        # Wait for agent to be ready
        print("Waiting for agent to be ready...")
        time.sleep(30)
        
        # Create agent version
        print("Creating agent version...")
        version_response = bedrock_agent.prepare_agent(agentId=agent_id)
        
        print("RAG-enhanced agent deployment completed!")
        print(f"Agent ID: {agent_id}")
        print(f"Agent ARN: {response['agent']['agentArn']}")
        
        # Save configuration for later use
        config = {
            'agent_id': agent_id,
            'agent_arn': response['agent']['agentArn'],
            'knowledge_base_id': knowledge_base_id,
            'status': 'success'
        }
        
        with open('rag_assessment_agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return config
        
    except ClientError as e:
        print(f"Error creating agent: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def update_existing_agent_with_rag(agent_id, knowledge_base_id):
    """Update an existing agent to include knowledge base integration"""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    
    try:
        # Get current agent configuration
        agent_response = bedrock_agent.get_agent(agentId=agent_id)
        agent = agent_response['agent']
        
        # Update agent with knowledge base
        update_config = {
            "agentId": agent_id,
            "agentName": agent['agentName'],
            "description": agent['description'] + " مع قاعدة المعرفة",
            "instruction": agent['instruction'],
            "foundationModel": agent['foundationModel']
        }
        
        print(f"Updating agent {agent_id} with knowledge base {knowledge_base_id}...")
        
        response = bedrock_agent.update_agent(**update_config)
        
        # Associate knowledge base with agent
        print("Associating knowledge base with agent...")
        bedrock_agent.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            knowledgeBaseId=knowledge_base_id,
            description="قاعدة المعرفة للعقود القانونية المصرية",
            knowledgeBaseState="ENABLED"
        )
        
        # Prepare updated agent
        print("Preparing updated agent...")
        bedrock_agent.prepare_agent(agentId=agent_id)
        
        print("Agent updated successfully with RAG integration!")
        return {
            'agent_id': agent_id,
            'knowledge_base_id': knowledge_base_id,
            'status': 'updated'
        }
        
    except ClientError as e:
        print(f"Error updating agent: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy RAG-enhanced contract assessment agent')
    parser.add_argument('--update', help='Update existing agent ID with RAG', type=str)
    parser.add_argument('--kb-id', help='Knowledge base ID to use', type=str)
    
    args = parser.parse_args()
    
    if args.update:
        kb_id = args.kb_id or os.environ.get('EGYPTIAN_LAW_KB_ID')
        if not kb_id:
            print("Error: Knowledge base ID required. Use --kb-id or set EGYPTIAN_LAW_KB_ID")
            exit(1)
        result = update_existing_agent_with_rag(args.update, kb_id)
    else:
        result = create_rag_enhanced_assessment_agent()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))