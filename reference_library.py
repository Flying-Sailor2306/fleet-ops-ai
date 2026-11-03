"""Local reference excerpts; documents are evidence, never agent instructions."""
import json
import re
from pathlib import Path
from company_sms import sms_reference

LIBRARY = Path(__file__).with_name('local-data') / 'references.json'

def references():
    docs = json.loads(LIBRARY.read_text(encoding='utf-8')) if LIBRARY.exists() else []
    return [sms_reference()] + [d for d in docs if d['id'] != 'ATM-SMS-001']

def attach(case):
    case['document_library'] = references()
    return case

ROLE_TOPICS = {
    'Engineering Superintendent': 'machinery maintenance engine fuel oil quick closing valves equipment repair inspection MARPOL sampling',
    'Marine Superintendent': 'navigation voyage planning emergency marine accident port state control class survey audit certificates flag notification',
    'Fleet Manager': 'ISM company responsibility master authority DPA safety management compliance risk superintendent accident reporting certificates',
}

def model_context(role, case, budget=30000, search_query=''):
    """Bounded, transparent lexical selection, not a claim of exhaustive review."""
    result = dict(case)
    # Failed outputs are retained for local diagnosis, never forwarded as evidence.
    result.pop('validation_attempts', None)
    submission = case.get('submission', {})
    query = ROLE_TOPICS.get(role, '') + ' ' + ' '.join(str(submission.get(k,'')) for k in ('problem','observations','assistance_requested')) + ' ' + search_query
    if not submission: query += ' piston rings compression blow by engine condition'
    terms = set(re.findall(r'[a-z]{3,}', query.lower()))
    candidates = []
    for doc in case.get('document_library', []):
        for chunk in doc.get('chunks', []):
            words = set(re.findall(r'[a-z]{3,}', chunk['text'].lower()))
            score = len(terms & words)
            # Always include company authority, evidence, decision and closure rules.
            core_sms = {'ATM-SMS-00', 'ATM-SMS-02', 'ATM-SMS-04', 'ATM-SMS-07', 'ATM-SMS-10', 'ATM-SMS-12', 'ATM-SMS-15'}
            role_sms = {'Engineering Superintendent':'ATM-SMS-11', 'Marine Superintendent':'ATM-SMS-06', 'Fleet Manager':'ATM-SMS-09'}
            if chunk['id'] in core_sms or chunk['id'] == role_sms.get(role): score += 1000
            if doc.get('category') == 'OEM engine manuals':
                # Prefer relevant technical guidance over general circular matches.
                if score: score += 200
                if chunk['id'] == 'OEM-MB04-p433': score += 900
                if role == 'Engineering Superintendent':
                    lower = chunk['text'].lower()
                    score += 20 * sum(phrase in lower and phrase in query.lower() for phrase in ['piston ring', 'compression pressure', 'blow-by', 'cylinder condition', 'starting air', 'exhaust temperature', 'lubricating oil', 'cooling water'])
            if score: candidates.append((score, doc['id'], chunk['id'], doc, chunk))
    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))
    selected, used, ids = {}, 0, []
    for _, doc_id, _, doc, chunk in candidates:
        if used + len(chunk['text']) > budget: continue
        if doc_id not in selected:
            selected[doc_id] = {k:v for k,v in doc.items() if k != 'chunks'}
            selected[doc_id]['chunks'] = []
        selected[doc_id]['chunks'].append(chunk)
        used += len(chunk['text'])
        ids.append(chunk['id'])
        if len(ids) >= 12: break
    result['document_library'] = list(selected.values())
    result['reference_selection'] = dict(query=query, method='Case and manager assignment search, at most 12 excerpts / 30000 characters; not exhaustive',
        role=role, excerpt_ids=ids, total_documents=len(case.get('document_library', [])),
        omitted_documents=[dict(id=d['id'], status=d['status']) for d in case.get('document_library', []) if d['id'] not in selected])
    return result
