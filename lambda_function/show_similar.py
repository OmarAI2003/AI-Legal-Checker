import os
import json
from lambda_rag_processor import lambda_handler

# Ensure mock mode for safety
os.environ['USE_MOCK'] = 'true'

# Load sample event
with open(os.path.join(os.path.dirname(__file__), 'sample_event.json'), 'r', encoding='utf-8') as f:
    event = json.load(f)

resp = lambda_handler(event, None)
body = resp.get('body') if isinstance(resp, dict) else None
if not body:
    print('No body in response')
    print(resp)
    raise SystemExit(1)

parsed = json.loads(body)
analysis = parsed.get('analysis', {})
rag_context = analysis.get('rag_context', {})
similar = rag_context.get('similar_clauses', [])
comparison = rag_context.get('clause_comparison', {})

print('\n== Similar Clauses Found ==\n')
for i, sc in enumerate(similar, 1):
    print(f"Similar #{i}:")
    print(json.dumps(sc, ensure_ascii=False, indent=2))
    print()

print('\n== Clause Matches (input -> best similar) ==\n')
for match in comparison.get('clause_matches', []):
    print(f"Input clause: {match.get('current_clause')}")
    print(f"Matched similar clause: {match.get('similar_clause')}")
    print(f"Similarity score: {match.get('similarity_score')}")
    print(f"Clause type: {match.get('clause_type')}")
    print('-'*40)

if not similar:
    print('No similar clauses returned.')
