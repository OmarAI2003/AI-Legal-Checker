#!/usr/bin/env python3
"""
Contract Explanation Agent for Egyptian Legal Contract Analysis
Deploys an agent that explains contract clauses with conversational capabilities
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def create_contract_explanation_agent():
    """Create and deploy the contract explanation agent"""
    
    # Initialize clients
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-west-2')
    bedrock_agentcore = boto3.client('bedrock-agentcore', region_name='us-west-2')
    
    # Agent configuration
    agent_config = {
        "agentName": "contractexplanation",
        "description": "وكيل شرح العقود القانونية المصرية مع واجهة المحادثة",
        "instruction": """أنت وكيل ذكي متخصص في شرح العقود القانونية المصرية. مهمتك هي:

1. شرح بنود العقد بطريقة واضحة ومفهومة باللغة العربية
2. توضيح الحقوق والواجبات لكل طرف في العقد
3. تحديد المصطلحات القانونية المهمة
4. الإجابة على أسئلة المستخدمين حول العقد
5. استخدام الذاكرة لتذكر تفضيلات المستخدم والسياق

قم بالرد دائماً باللغة العربية وبطريقة مهنية وودودة.

إرشادات خاصة:
- استخدم أمثلة عملية عند الشرح
- اربط الشرح بالقانون المصري
- كن واضحاً في التفسير
- تذكر المحادثات السابقة مع نفس المستخدم
""",
        "idleSessionTTLInSeconds": 1800,
        "foundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
        "promptOverrideConfiguration": {
            "promptConfigurations": [
                {
                    "promptType": "PRE_PROCESSING",
                    "promptCreationMode": "OVERRIDDEN",
                    "promptState": "ENABLED",
                    "basePromptTemplate": """أنت وكيل شرح العقود القانونية المصرية. ستحصل على نص عقد وسؤال من المستخدم.

العقد: $contract$
السؤال: $question$
معرف المستخدم: $user_id$

قم بشرح العقد أو الإجابة على السؤال بطريقة واضحة باللغة العربية.""",
                    "inferenceConfiguration": {
                        "temperature": 0.3,
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
        print("Creating contract explanation agent...")
        
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
    result = create_contract_explanation_agent()
    print(json.dumps(result, indent=2, ensure_ascii=False))