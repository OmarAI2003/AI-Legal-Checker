import json
import sys
import os

INPUT_DEFAULT = os.path.join(os.path.dirname(__file__), 'user_input.json')

# Simple rules to "edit required clauses":
# - Fill placeholder fields with example values in Arabic
# - Normalize clause_type to a known set
# - Set importance to one of (عالية, متوسطة, منخفضة)
# - Ensure parties_mentioned is a list

def normalize_clause_type(ct):
    ct = ct or ''
    ct = ct.strip().lower()
    mapping = {
        'راتب': 'راتب',
        'ساعات_عمل': 'ساعات_عمل',
        'ساعات عمل': 'ساعات_عمل',
        'مدة_عقد': 'مدة_عقد',
        'إنهاء': 'إنهاء',
        'التزامات': 'التزامات'
    }
    for k,v in mapping.items():
        if k in ct:
            return v
    return 'عام'

def normalize_importance(imp):
    if not imp:
        return 'متوسطة'
    imp = imp.strip().lower()
    if 'عالي' in imp:
        return 'عالية'
    if 'منخفض' in imp:
        return 'منخفضة'
    return 'متوسطة'


def process(data):
    # Fill document metadata placeholders if needed
    meta = data.get('document_metadata', {})
    if meta.get('contract_type', '').startswith('نوع'):
        meta['contract_type'] = 'عقد عمل'
    if meta.get('parties') and isinstance(meta['parties'], list) and meta['parties'][0].startswith('أسماء'):
        meta['parties'] = ['شركة ألف', 'الموظف باء']
    if meta.get('contract_date', '').startswith('تاريخ'):
        meta['contract_date'] = '2025-09-28'
    if meta.get('total_clauses', '').startswith('عدد'):
        meta['total_clauses'] = len(data.get('extracted_clauses', []))
    data['document_metadata'] = meta

    # processing info
    pinfo = data.get('processing_info', {})
    if pinfo.get('ocr_confidence', '').startswith('مستوى'):
        pinfo['ocr_confidence'] = 'متوسطة'
    if pinfo.get('document_quality', '').startswith('جودة'):
        pinfo['document_quality'] = 'جيدة'
    if pinfo.get('language_detected', '').startswith('اللغة'):
        pinfo['language_detected'] = 'ar'
    data['processing_info'] = pinfo

    # clauses
    clauses = data.get('extracted_clauses', [])
    for i, c in enumerate(clauses):
        if c.get('clause_id', '').startswith('رقم'):
            c['clause_id'] = f'CL-{i+1}'
        if c.get('clause_title', '').startswith('عنوان'):
            c['clause_title'] = f'بند {i+1} - عنوان مثال'
        if c.get('clause_text', '').startswith('نص'):
            c['clause_text'] = 'هذا نص تجريبي للبند يوضح الشروط والالتزامات المتعلقة بالعمل.'
        c['clause_type'] = normalize_clause_type(c.get('clause_type'))
        c['importance'] = normalize_importance(c.get('importance'))
        if not isinstance(c.get('parties_mentioned'), list):
            c['parties_mentioned'] = [c.get('parties_mentioned')]
        clauses[i] = c
    data['extracted_clauses'] = clauses
    return data


def main(path=INPUT_DEFAULT):
    if not os.path.exists(path):
        print('Input file not found:', path)
        return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    out = process(data)
    print('\n=== Edited JSON ===\n')
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # Summary
    print('\n=== Summary ===\n')
    print(f"Contract type: {out['document_metadata'].get('contract_type')}")
    print(f"Parties: {', '.join(out['document_metadata'].get('parties', []))}")
    print(f"Total clauses: {out['document_metadata'].get('total_clauses')}")
    print(f"OCR confidence: {out['processing_info'].get('ocr_confidence')}")

if __name__ == '__main__':
    p = sys.argv[1] if len(sys.argv) > 1 else INPUT_DEFAULT
    main(p)
