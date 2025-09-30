"""
Egyptian Legal Contract Analysis API
AWS Lambda Function for contract analysis with RAG-enhanced AgentCore
"""

import json
import logging
import os
import boto3
import uuid
import base64
import re
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock AgentCore client
try:
    agent_core_client = boto3.client('bedrock-agentcore', region_name='us-west-2')
    logger.info("Bedrock AgentCore client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AgentCore client: {e}")
    agent_core_client = None

def extract_clean_arabic_text(response_text):
    """Extract clean Arabic text from complex JSON responses"""
    if not response_text or response_text.strip() == "":
        return "لم أتمكن من الحصول على إجابة"
    
    try:
        if response_text.strip().startswith('{'):
            parsed = json.loads(response_text)
            
            # Handle nested structure: {"role": "assistant", "content": [{"text": "..."}]}
            if 'content' in parsed and isinstance(parsed['content'], list):
                if parsed['content'] and 'text' in parsed['content'][0]:
                    inner_text = parsed['content'][0]['text']
                    
                    try:
                        inner_json = json.loads(inner_text)
                        # For follow-up questions, check if it's a simple response
                        if len(inner_json) == 1 and 'contract_summary' in inner_json:
                            clean_answer = inner_json['contract_summary']
                            if clean_answer.startswith('📋 ملخص العقد:'):
                                clean_answer = clean_answer.replace('📋 ملخص العقد:', '').strip()
                            return clean_text_response(clean_answer)
                        return format_contract_json_to_arabic(inner_json)
                    except:
                        inner_cleaned = clean_text_response(inner_text)
                        if inner_cleaned.startswith('📋 ملخص العقد:'):
                            inner_cleaned = inner_cleaned.replace('📋 ملخص العقد:', '').strip()
                        return inner_cleaned
            
            # Handle direct JSON contract data
            elif any(key in parsed for key in ['contract_summary', 'contract_type', 'legal_classification']):
                return format_contract_json_to_arabic(parsed)
            
            # Handle simple text response
            elif 'text' in parsed:
                text_response = clean_text_response(parsed['text'])
                if text_response.startswith('📋 ملخص العقد:'):
                    text_response = text_response.replace('📋 ملخص العقد:', '').strip()
                return text_response
                
        # If not JSON, clean and return as text
        cleaned_text = clean_text_response(response_text)
        if cleaned_text.startswith('📋 ملخص العقد:'):
            cleaned_text = cleaned_text.replace('📋 ملخص العقد:', '').strip()
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        # Fallback: try to extract Arabic text with regex
        arabic_text = re.findall(r'[\u0600-\u06FF\s]+', response_text)
        if arabic_text:
            result = ' '.join(arabic_text).strip()
            if result.startswith('📋 ملخص العقد:'):
                result = result.replace('📋 ملخص العقد:', '').strip()
            return result
        return "تم استلام الرد لكن حدث خطأ في التحليل"

def format_contract_json_to_arabic(data):
    """Format contract JSON data into clean Arabic text"""
    result = []
    
    # For follow-up questions, don't repeat contract summary - just return the main content
    if len(data) == 1 and 'contract_summary' in data:
        return data['contract_summary']
    
    # Contract summary (only for full analysis)
    if 'contract_summary' in data and len(data) > 1:
        result.append(f"📋 ملخص العقد: {data['contract_summary']}")
    
    # Contract type
    if 'contract_type' in data:
        contract_type = data['contract_type']
        if isinstance(contract_type, dict):
            if 'نوع_رئيسي' in contract_type:
                result.append(f"📝 نوع العقد: {contract_type['نوع_رئيسي']}")
            if 'تصنيف_فرعي' in contract_type:
                result.append(f"🏷️ التصنيف: {contract_type['تصنيف_فرعي']}")
            
            # Characteristics
            if 'خصائص' in contract_type and isinstance(contract_type['خصائص'], list):
                result.append("\n✨ خصائص العقد:")
                for feature in contract_type['خصائص']:
                    result.append(f"  • {feature}")
    
    # Legal classification
    if 'legal_classification' in data:
        legal = data['legal_classification']
        if isinstance(legal, dict):
            result.append("\n⚖️ التصنيف القانوني:")
            if 'القانون_الحاكم' in legal:
                result.append(f"  📚 القانون الحاكم: {legal['القانون_الحاكم']}")
            if 'طبيعة_العقد' in legal:
                result.append(f"  🏛️ طبيعة العقد: {legal['طبيعة_العقد']}")
            if 'درجة_الإلزام' in legal:
                result.append(f"  ⚡ درجة الإلزام: {legal['درجة_الإلزام']}")
    
    # Contract duration
    if 'contract_duration' in data:
        duration = data['contract_duration']
        if isinstance(duration, dict):
            result.append("\n⏰ مدة العقد:")
            if 'نوع_المدة' in duration:
                result.append(f"  📅 نوع المدة: {duration['نوع_المدة']}")
            if 'فترة_الاختبار' in duration:
                result.append(f"  🧪 فترة الاختبار: {duration['فترة_الاختبار']}")
            if 'تاريخ_البدء' in duration:
                result.append(f"  🚀 تاريخ البدء: {duration['تاريخ_البدء']}")
    
    # Additional notes
    if 'additional_notes' in data:
        notes = data['additional_notes']
        if isinstance(notes, dict) and 'ملاحظات_قانونية' in notes:
            if isinstance(notes['ملاحظات_قانونية'], list):
                result.append("\n📝 ملاحظات قانونية:")
                for note in notes['ملاحظات_قانونية']:
                    result.append(f"  • {note}")
    
    return '\n'.join(result) if result else "تم تحليل العقد بنجاح"

def clean_text_response(text):
    """Clean and format text response"""
    if not text:
        return "لم أتمكن من الحصول على إجابة"
    
    # Remove extra whitespace and clean up
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remove JSON-like patterns if they exist
    cleaned = re.sub(r'[{}"\[\]]', '', cleaned)
    
    # Remove contract summary prefixes specifically
    summary_prefixes = [
        '📋 ملخص العقد:',
        'ملخص العقد:',
        '📋 ملخص العقد',
        'ملخص العقد'
    ]
    
    for prefix in summary_prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned.replace(prefix, '').strip()
            break
    
    return cleaned

def lambda_handler(event, context):
    """AWS Lambda handler for Egyptian Legal Contract Analysis"""
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': ''
        }
    
    try:
        # Parse the request
        path = event.get('path', '/')
        method = event.get('httpMethod', 'GET')
        body = event.get('body', '{}')
        
        # Health check endpoint
        if path == '/health' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'Egyptian Legal Contract Analysis API',
                    'aws_status': 'connected',
                    'agentcore_status': 'available',
                    'region': 'us-west-2'
                })
            }
        
        # Contract analysis endpoint
        if path == '/api/analyze' and method == 'POST':
            return analyze_contract(body)
        
        # Follow-up questions endpoint for chat functionality
        if path == '/api/ask' and method == 'POST':
            return ask_followup_question(body)
        
        # OCR processing endpoint
        if path == '/api/ocr' and method == 'POST':
            return process_contract_image(body)
        
        # Default response for unknown paths
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'مسار غير موجود'
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'خطأ غير متوقع: {str(e)}'
            })
        }

def analyze_contract(body_str):
    """Analyze contract using direct Bedrock AgentCore API"""
    try:
        if not agent_core_client:
            return {
                'statusCode': 503,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'خدمة AgentCore غير متاحة'
                })
            }

        # Parse request body
        if isinstance(body_str, str):
            data = json.loads(body_str)
        else:
            data = body_str
        
        analysis_type = data.get('analysis_type')
        contract_text = data.get('contract_text')
        user_id = data.get('user_id', f'web_user_{uuid.uuid4().hex[:8]}')
        
        if not analysis_type or not contract_text:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False, 
                    'error': 'نوع التحليل أو نص العقد مفقود'
                })
            }
        
        # Map analysis types to deployed agent ARNs
        agent_arns = {
            'explanation': 'arn:aws:bedrock-agentcore:us-west-2:273667282126:runtime/memoryenhancedexplanation-L1S4nKChZB',
            'assessment': 'arn:aws:bedrock-agentcore:us-west-2:273667282126:runtime/memoryenhancedassessment-JAX5fj2gv1'
        }
        
        if analysis_type not in agent_arns:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'نوع التحليل غير صحيح'
                })
            }
        
        agent_arn = agent_arns[analysis_type]
        session_id = f'session-{user_id}-{uuid.uuid4().hex}'
        
        # Ensure session ID meets AWS minimum length requirement (33 characters)
        if len(session_id) < 33:
            session_id = f'session-{user_id}-{uuid.uuid4().hex}'
        
        # Prepare payload data
        if analysis_type == 'explanation':
            payload_data = {
                "contract": contract_text,
                "user_id": user_id,
                "analysis_type": "detailed_explanation",
                "request": "قم بتحليل هذا العقد وشرحه بالتفصيل. اشرح البنود والحقوق والواجبات بطريقة واضحة."
            }
        else:
            payload_data = {
                "contract": contract_text,
                "user_id": user_id,
                "analysis_type": "risk_assessment",
                "request": "قم بتقييم هذا العقد من الناحية القانونية وحدد المخاطر والتوصيات."
            }
        
        # Convert payload to bytes
        payload = json.dumps(payload_data, ensure_ascii=False).encode('utf-8')
        
        logger.info(f"Invoking agent: {analysis_type} for user: {user_id}")
        
        try:
            # Invoke the selected agent
            response = agent_core_client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                runtimeSessionId=session_id,
                payload=payload
            )
            
            # Process response
            if 'response' in response:
                response_body = response['response']
                
                # For streaming responses, we need to read all chunks
                if hasattr(response_body, 'read'):
                    try:
                        full_content = response_body.read()
                        if isinstance(full_content, bytes):
                            full_content = full_content.decode('utf-8')
                        response_body = full_content
                    except Exception as read_error:
                        logger.error(f"Error reading response body: {read_error}")
                        response_body = str(response_body)
                
                # Extract clean Arabic text from complex JSON responses
                clean_response = extract_clean_arabic_text(response_body)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'analysis_type': analysis_type,
                        'result': clean_response,
                        'user_id': user_id,
                        'session_id': session_id
                    }, ensure_ascii=False)
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'لم يتم الحصول على استجابة من الوكيل'
                    })
                }
                
        except ClientError as e:
            logger.error(f"Bedrock AgentCore error: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'خطأ في استدعاء الوكيل: {str(e)}'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_contract: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'خطأ غير متوقع: {str(e)}'
            })
        }

def ask_followup_question(body_str):
    """Handle follow-up questions in chat mode"""
    try:
        if not agent_core_client:
            return {
                'statusCode': 503,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'خدمة AgentCore غير متاحة'
                })
            }

        # Parse request body
        if isinstance(body_str, str):
            data = json.loads(body_str)
        else:
            data = body_str
        
        question = data.get('question')
        contract_text = data.get('contract_text', '')
        user_id = data.get('user_id', f'web_user_{uuid.uuid4().hex[:8]}')
        session_id = data.get('session_id', f'session-{user_id}-{uuid.uuid4().hex}')
        
        # Ensure session ID meets AWS minimum length requirement (33 characters)
        if len(session_id) < 33:
            session_id = f'session-{user_id}-{uuid.uuid4().hex}'
        
        if not question:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'السؤال مطلوب'
                })
            }
        
        # Use the explanation agent for follow-up questions
        agent_arn = 'arn:aws:bedrock-agentcore:us-west-2:273667282126:runtime/memoryenhancedexplanation-L1S4nKChZB'
        
        # Prepare payload for follow-up question - improved for detailed responses
        payload_data = {
            "contract": contract_text,
            "user_id": user_id,
            "question": f"""السؤال: {question}

بناءً على العقد المقدم، يرجى تقديم إجابة مفصلة وشاملة. اذكر التفاصيل القانونية والبنود ذات الصلة.

العقد المرجعي:
{contract_text}

يرجى الإجابة بشكل مفصل وواضح مع ذكر الأدلة من العقد."""
        }
        
        # Convert payload to bytes
        payload = json.dumps(payload_data, ensure_ascii=False).encode('utf-8')
        
        logger.info(f"Follow-up question: {question[:100]}...")
        
        try:
            # Invoke the explanation agent
            response = agent_core_client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                runtimeSessionId=session_id,
                payload=payload
            )
            
            # Process response
            if 'response' in response:
                response_body = response['response']
                
                # For streaming responses, we need to read all chunks
                if hasattr(response_body, 'read'):
                    try:
                        full_content = response_body.read()
                        if isinstance(full_content, bytes):
                            full_content = full_content.decode('utf-8')
                        response_body = full_content
                    except Exception as read_error:
                        logger.error(f"Error reading response body: {read_error}")
                        response_body = str(response_body)
                
                # Extract clean Arabic text from complex JSON responses
                clean_response = extract_clean_arabic_text(response_body)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'question': question,
                        'result': clean_response,
                        'user_id': user_id,
                        'session_id': session_id
                    }, ensure_ascii=False)
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'لم يتم الحصول على استجابة من الوكيل'
                    })
                }
                
        except ClientError as e:
            logger.error(f"Bedrock AgentCore error in follow-up: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'خطأ في استدعاء الوكيل: {str(e)}'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in ask_followup_question: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'خطأ غير متوقع: {str(e)}'
            })
        }

def process_contract_image(body):
    """Process contract image using simplified OCR (direct image processing - no S3)"""
    
    try:
        # Parse request body
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body
            
        logger.info("Starting simplified OCR processing for contract image")
        
        # Check for required image_data
        if 'image_data' not in data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'مطلوب image_data'
                })
            }
        
        # Call simplified OCR processor Lambda function
        logger.info("Calling simplified OCR processor Lambda function")
        lambda_client = boto3.client('lambda', region_name='us-west-2')
        
        # Prepare payload for simplified OCR (pass image_data directly)
        ocr_payload = {
            'image_data': data['image_data']
        }
        
        try:
            # Invoke simplified OCR processor Lambda
            ocr_response = lambda_client.invoke(
                FunctionName='ocr-processor',
                InvocationType='RequestResponse',
                Payload=json.dumps(ocr_payload)
            )
            
            # Parse OCR response
            ocr_result = json.loads(ocr_response['Payload'].read())
            
            if ocr_result['statusCode'] == 200:
                # Parse the extracted text
                ocr_body = json.loads(ocr_result['body'])
                extracted_text = ocr_body.get('extracted_text', '')
                
                logger.info(f"Simplified OCR extraction successful. Text length: {len(extracted_text)}")
                
                # Prepare response
                response_data = {
                    'success': True,
                    'extracted_text': extracted_text,
                    'character_count': len(extracted_text),
                    'processing_method': 'direct_claude_vision'
                }
                
                # If auto_analyze is requested, run contract analysis
                if data.get('auto_analyze') and data.get('analysis_type') and extracted_text:
                    logger.info(f"Running auto-analysis: {data['analysis_type']}")
                    
                    # Prepare analysis request
                    analysis_request = {
                        'analysis_type': data['analysis_type'],
                        'contract_text': extracted_text,
                        'user_id': data.get('user_id', f'ocr_user_{uuid.uuid4().hex[:8]}'),
                        'source': 'simplified_ocr'
                    }
                    
                    # Run analysis
                    analysis_result = analyze_contract(json.dumps(analysis_request))
                    
                    if analysis_result['statusCode'] == 200:
                        analysis_data = json.loads(analysis_result['body'])
                        response_data['analysis'] = analysis_data
                        response_data['auto_analysis_completed'] = True
                        logger.info("Auto-analysis completed successfully")
                    else:
                        response_data['analysis_error'] = "فشل في التحليل التلقائي"
                        response_data['auto_analysis_completed'] = False
                        logger.warning("Auto-analysis failed")
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(response_data, ensure_ascii=False)
                }
                
            else:
                # OCR failed
                ocr_error = json.loads(ocr_result['body']).get('error', 'فشل في استخراج النص')
                logger.error(f"OCR processor error: {ocr_error}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': f'فشل في استخراج النص من الصورة: {ocr_error}'
                    })
                }
                
        except Exception as e:
            logger.error(f"Error calling OCR processor: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'فشل في استدعاء معالج OCR: {str(e)}'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in process_contract_image: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'خطأ غير متوقع: {str(e)}'
            })
        }