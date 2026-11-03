"""Deterministic evidence and approval gates, independent of model prose."""
from datetime import datetime, timezone
from copy import deepcopy
from reference_library import attach, model_context
from company_sms import company

ROLES = ['Engineering Superintendent', 'Marine Superintendent', 'Fleet Manager']

def fixture(scenario='corroborated'):
    evidence = [
        dict(id='E1', title='Prepared fictional compression measurements', date='2026-10-30', text='FICTIONAL compression bar: units 1–7 = 30, 24, 30, 31, 30, 29, 30. Unit 2 historical baseline 30 bar under comparable fictional trial conditions. Invented measurements, not OEM acceptance limits or original shop-trial data.'),
        dict(id='E2', title='Prepared inspection finding', date='2026-10-30', text='Prior blow-by signs on unit 2. This is an inspection finding, not a diagnosis.'),
        dict(id='E3', title='Fictional Chief Engineer physical inspection', date='2026-10-31', text='Physical inspection identifies damaged piston rings on unit 2. No repair or follow-up trial yet.'),
    ]
    if scenario == 'missing': evidence = evidence[:1]
    if scenario == 'conflicting': evidence[2]['text'] = 'Physical inspection finds rings intact; measurement calibration unresolved.'
    return dict(id='FO-002', scenario=scenario, company=company(), vessel='MT Aster Horizon • fictional', priority='High', owner=ROLES[0], evidence=evidence,
        references=[dict(id='ATM-SMS-001', date='2026-10-31', text='Aster Tide Marine fictional SMS revision 0.2. Apply ATM-SMS-04 technical evidence, 06 marine handoff, 07 human decision, 10 verification/closure and 02 Master/DPA authority. Demonstration policy, not a certified SMS.'),
                    dict(id='REF-DEMO', date='2026-10-31', text='FICTIONAL assessment: low compression and blow-by suggest sealing issue; physical inspection required for confirmation. Replace with user reference assessment.')],
        pending=['OEM set supplied; verify section applicability, revision and latest service letters before using technical limits', 'Independent reference assessment', 'Calibration and comparable trial conditions', 'Chief Engineer, Master, reliability and fleet technical consultation', 'OEM consultation if unresolved', 'Fictional SMS is supplied; no real company approval or certification is claimed'],
        tasks=[dict(task='Validate measurements and inspect unit 2', owner='Chief Engineer', depends='OEM procedure and isolation authorization', status='Pending real verification'),
               dict(task='Assess voyage impact and prepare notification drafts', owner=ROLES[1], depends='Engineering handoff', status='Draft only'),
               dict(task='Decide stoppage with superintendent consultation', owner=ROLES[2], depends='Technical and marine assessments; human approval', status='Awaiting approval')],
        assumptions=dict(cargo_barrels=2000000, cargo_value_usd=250000000, earnings_usd_day=800000),
        trace=[], approval=None, closure=False)

def assessment(case):
    ids = {e['id'] for e in case['evidence']}
    conflict = any('intact' in e['text'] for e in case['evidence'])
    confirmed = 'E3' in ids and not conflict
    return dict(diagnosis='Fictional physical inspection corroborates piston-ring damage' if confirmed else 'Suspected sealing issue; diagnosis unresolved',
        certainty='Corroborated within fixture only' if confirmed else 'Uncertain',
        citations=sorted(ids), deviation_bar=6, historical_deviation_bar=6,
        conflict=conflict, alert='OPEN',
        checks=['Compression is distinct from peak firing pressure; no injector diagnosis inferred.',
                'No verified case-applicable OEM rejection limit: 6 bar is descriptive, not a rejection rule.',
                'Missing authorized guidance and consultation prevent operational release.',
                'No corroboration never closes an alert.'])

def run(case, generate=None):
    result = deepcopy(case)
    attach(result)
    result['trace'] = []
    result['approval'] = None
    result['closure'] = False
    result['assessment'] = assessment(result)
    outputs = [
        result['assessment']['diagnosis'] + '. Aster Tide Marine technical handoff: consult Chief Engineer, reliability and fleet technical; verify OEM manual/SOP and trial data [ATM-SMS-04]. Escalate to OEM if necessary. Verification and closure remain blocked pending repair/trial evidence [ATM-SMS-10].',
        'Aster Tide Marine operational handoff: coordinate with Master and shipboard command. Prepare voyage manager/charterer notification drafts only; verify circular applicability [ATM-SMS-06]. Assess schedule and operating restrictions with Engineering. Master retains overriding safety authority [ATM-SMS-02]. No external message sent.',
        'Aster Tide Marine decision brief: human Fleet Manager review required for company stoppage planning after superintendent, Master and Chief Engineer consultation [ATM-SMS-07]. Master retains overriding safety authority; unresolved concerns escalate to human DPA [ATM-SMS-02]. Cargo value is exposure context, not loss. Daily earnings are not automatic stoppage cost. No autonomous vessel action. Closure blocked [ATM-SMS-10].'
    ]
    for i, role in enumerate(ROLES):
        note = generate(role, result) if generate else outputs[i]
        result['trace'].append(dict(step=i+1, role=role, to=ROLES[i+1] if i < 2 else 'Qualified human manager',
            at=datetime.now(timezone.utc).isoformat(), note=note, evidence_ids=result['assessment']['citations'],
            reference_excerpt_ids=model_context(role, result)['reference_selection']['excerpt_ids'] if generate else [
                ['ATM-SMS-04', 'ATM-SMS-10'], ['ATM-SMS-06', 'ATM-SMS-02'], ['ATM-SMS-07', 'ATM-SMS-02', 'ATM-SMS-10']][i],
            company=result['company']['name'],
            provenance='Meta model draft — unverified' if generate else 'Deterministic fictional fixture'))
    result['owner'] = 'Qualified human manager'
    return result

def approve(case, name, consultation, decision):
    if not case.get('trace') or not name.strip() or not consultation or decision not in ('Request stoppage review', 'Request further evidence'):
        raise ValueError('Named human, completed handoffs, consultation acknowledgment and valid decision required.')
    case['approval'] = dict(name=name.strip(), decision=decision, at=datetime.now(timezone.utc).isoformat(), scope='Demo decision acknowledgment only; no operational authorization')
    return case

def evaluate(case):
    a = case.get('assessment', assessment(case))
    available = {e['id'] for e in case['evidence']}
    return dict(reference='REF-DEMO: fictional rubric, not independent validation',
        correct_deviation=a['deviation_bar'] == 6,
        citation_validity=set(a['citations']) <= available,
        suspected_vs_confirmed=('unresolved' in a['diagnosis']) == (case['scenario'] != 'corroborated'),
        safety_checks_present=len(a['checks']) == 4,
        missing_findings=case['pending'], unsupported_assertions='Model prose requires human comparison; citation existence does not prove entailment.',
        reference_dates=[r['date'] for r in case['references']],
        missing_approval=case.get('approval') is None,
        closure_blocked=True)
