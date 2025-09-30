#!/usr/bin/env python3
"""
Contract Assessment Agent for Egyptian Legal Contract Analysis
Deploys an agent that assesses contract risks and provides recommendations
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def create_contract_assessment_agent():
    """Create and deploy the contract assessment agent"""
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    # Agent configuration
    agent_config = {
        "agentName": "contractassessment",
        "description": "وكيل تقييم وتوصيات العقود القانونية المصرية",
        "instruction": """أنت وكيل ذكي متخصص في تقييم العقود القانونية المصرية وتقديم التوصيات. مهمتك هي:

1. تحليل العقد للبحث عن المخاطر القانونية المحتملة
2. تقييم مدى عدالة شروط العقد لكل طرف
3. تحديد البنود الغامضة أو الناقصة
4. تقديم تقييم شامل للمخاطر
5. تقديم توصيات لتحسين العقد وحماية الأطراف
6. اقتراح بنود إضافية أو تعديلات على البنود الموجودة

قم بالرد دائماً باللغة العربية وبطريقة مهنية منظمة.

إرشادات خاصة:
- ركز على المخاطر الفعلية والقابلة للحدوث
- اربط التقييم والتوصيات بالقانون المصري
- كن محدداً في تحديد المشاكل والحلول
- قدم مستوى خطورة لكل مخاطرة
- رتب التوصيات حسب الأولوية
- قدم صيغ بديلة للبنود الغامضة

هيكل الإجابة المطلوب:
{
  "risk_assessment": "تقييم المخاطر العامة",
  "identified_risks": [
    {
      "risk": "وصف المخاطرة",
      "severity": "عالي/متوسط/منخفض",
      "impact": "التأثير المحتمل"
    }
  ],
  "contract_weaknesses": ["نقاط الضعف في العقد"],
  "recommendations": [
    {
      "priority": "عالي/متوسط/منخفض",
      "recommendation": "التوصية",
      "suggested_clause": "النص المقترح للبند"
    }
  ],
  "overall_fairness": "تقييم عدالة العقد",
  "legal_compliance": "مدى التوافق مع القانون المصري"
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
                    "basePromptTemplate": """أنت وكيل تقييم وتوصيات العقود القانونية المصرية.

العقد للتقييم: $contract$
معرف المستخدم: $user_id$

قم بتقييم المخاطر في هذا العقد وقدم توصيات للتحسين باللغة العربية وفقاً للهيكل المطلوب.""",
                    "inferenceConfiguration": {
                        "temperature": 0.2,
                        "topP": 0.9,
                        "topK": 250,
                        "maximumLength": 2000,
                        "stopSequences": []
                    }
                }
            ]
        }
    }
    
    try:
        print("Creating contract assessment agent...")
        
        response = bedrock_agentcore.create_agent(**agent_config)
        agent_id = response['agent']['agentId']
        
        print(f"Agent created successfully with ID: {agent_id}")
        
        # Wait for agent to be ready
        print("Waiting for agent to be ready...")
        time.sleep(30)
        
        # Create agent version
        print("Creating agent version...")
        version_response = bedrock_agentcore.prepare_agent(agentId=agent_id)
        
        print("Agent deployment completed!")
        print(f"Agent ID: {agent_id}")
        print(f"Agent ARN: {response['agent']['agentArn']}")
        
        return {
            'agent_id': agent_id,
            'agent_arn': response['agent']['agentArn'],
            'status': 'success'
        }
        
    except ClientError as e:
        print(f"Error creating agent: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

if __name__ == "__main__":
    result = create_contract_assessment_agent()
    print(json.dumps(result, indent=2, ensure_ascii=False))