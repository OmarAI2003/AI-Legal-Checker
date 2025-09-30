#!/usr/bin/env python3
"""
Simple OCR Processor Lambda - Direct Image to Arabic Text
No S3 dependency - just image in, text out
"""
import json
import boto3
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Simple OCR processor: Image data → Arabic text
    
    Input: {
        "image_data": "base64_encoded_image_data"
    }
    
    Output: {
        "statusCode": 200,
        "body": json.dumps({
            "success": true,
            "extracted_text": "النص العربي المستخرج من الصورة"
        })
    }
    """
    
    try:
        logger.info("🔍 Starting direct OCR processing")
        
        # Parse input
        if isinstance(event, str):
            data = json.loads(event)
        else:
            data = event
            
        # Get image data
        image_data = data.get('image_data')
        if not image_data:
            return create_error_response(400, "مطلوب image_data")
            
        logger.info(f"📥 Received image data (length: {len(image_data)})")
        
        # Clean base64 data (remove data URL prefix if present)
        if ',' in image_data:
            image_data = image_data.split(',')[1]
            
        # Decode base64 to bytes
        try:
            image_bytes = base64.b64decode(image_data)
            logger.info(f"✅ Decoded image: {len(image_bytes)} bytes")
        except Exception as e:
            return create_error_response(400, f"فشل في تحويل الصورة: {str(e)}")
        
        # Validate image size
        if len(image_bytes) < 100:
            return create_error_response(400, "الصورة صغيرة جداً، يرجى رفع صورة أكبر")
            
        if len(image_bytes) > 5 * 1024 * 1024:  # 5MB limit
            return create_error_response(400, "الصورة كبيرة جداً، الحد الأقصى 5 ميجابايت")
        
        # Process with Claude Vision
        logger.info("🤖 Processing with Claude Vision...")
        extracted_text = process_image_with_claude(image_bytes)
        
        if not extracted_text:
            return create_error_response(500, "لم يتم العثور على نص في الصورة")
            
        logger.info(f"✅ OCR completed successfully: {len(extracted_text)} characters")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'extracted_text': extracted_text,
                'character_count': len(extracted_text),
                'processing_method': 'direct_claude_vision'
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"❌ OCR processing failed: {str(e)}")
        return create_error_response(500, f"فشل في معالجة الصورة: {str(e)}")

def process_image_with_claude(image_bytes):
    """Process image directly with Claude Vision model"""
    
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        # Prepare the request for Claude Vision
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64.b64encode(image_bytes).decode('utf-8')
                            }
                        },
                        {
                            "type": "text",
                            "text": """استخرج كل النص العربي من هذه الصورة. 

متطلبات:
- استخرج النص بدقة كما هو مكتوب
- حافظ على التنسيق والفواصل
- اكتب النص العربي فقط دون أي تفسير أو تعليق
- إذا كان هناك نص إنجليزي، ترجمه للعربية
- لا تضيف أي نص من عندك

النص المستخرج:"""
                        }
                    ]
                }
            ]
        }
        
        # Call Claude Vision
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and response_body['content']:
            extracted_text = response_body['content'][0]['text'].strip()
            
            # Clean up the response (remove any prefixes Claude might add)
            cleaned_text = clean_extracted_text(extracted_text)
            return cleaned_text
            
        return None
        
    except Exception as e:
        logger.error(f"Claude Vision error: {str(e)}")
        raise e

def clean_extracted_text(text):
    """Clean and format the extracted text"""
    
    if not text:
        return ""
    
    # Remove common prefixes that Claude might add
    prefixes_to_remove = [
        "النص المستخرج:",
        "النص المستخرج من الصورة:",
        "النص في الصورة:",
        "المحتوى:",
        "النص:"
    ]
    
    cleaned = text.strip()
    
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove excessive whitespace
    import re
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Multiple empty lines to double
    cleaned = re.sub(r' +', ' ', cleaned)  # Multiple spaces to single
    
    return cleaned.strip()

def create_error_response(status_code, error_message):
    """Create standardized error response"""
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': error_message
        }, ensure_ascii=False)
    }