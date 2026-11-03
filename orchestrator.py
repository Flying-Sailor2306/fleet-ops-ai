"""Manager-led, bounded AI coordination. Models propose; Python validates transitions."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import re
import uuid
from domain import fixture
from reference_library import attach

MANAGER = 'Fleet Manager'
SPECIALISTS = ('Engineering Superintendent', 'Marine Superintendent')
MAX_CALLS = 15  # Up to eight workflow calls plus seven bounded correction calls.
MAX_CORRECTIONS = 7  # At most one correction per stage; never retry indefinitely.


class QuoteMismatch(ValueError):
    def __init__(self, source_id):
        self.source_id = source_id
        super().__init__('Guidance quote does not match retrieved source text: '+source_id)


class ResponseFormatError(ValueError):
    source_id = 'response-format'

def intake(data):
    required = ('reporter_role', 'reporter_name', 'location', 'operating_condition', 'problem', 'urgency')
    if any(not isinstance(data.get(k), str) or not data[k].strip() for k in required):
        raise ValueError('Complete reporting officer, location, operating condition, problem and urgency.')
    if data['reporter_role'] not in ('Master', 'Chief Engineer'): raise ValueError('Reporter must be Master or Chief Engineer.')
    if data['urgency'] not in ('Routine', 'High', 'Immediate concern'): raise ValueError('Invalid urgency.')
    if any(len(str(v)) > 12000 for v in data.values()): raise ValueError('Case field too long.')
    rate = data.get('daily_cost_usd', '').strip()
    if rate:
        import math
        if not math.isfinite(float(rate)) or float(rate) < 0: raise ValueError('Daily cost must be a nonnegative finite number.')
    lo,hi=data.get('scenario_min_hours','').strip(),data.get('scenario_max_hours','').strip()
    if bool(lo)!=bool(hi): raise ValueError('Supply both what-if duration bounds or leave both blank.')
    if lo:
        import math
        if not all(math.isfinite(float(x)) and float(x)>=0 for x in (lo,hi)) or float(lo)>float(hi): raise ValueError('Invalid what-if duration range.')
    case = fixture()
    case.update(id='ATM-' + uuid.uuid4().hex[:8].upper(), scenario='submitted', evidence=[], assessment=None,
        references=[], pending=[], assumptions={},
        tasks=[], trace=[], approval=None, closure=False, owner=MANAGER, status='Submitted',
        submission={k:data.get(k, '').strip() for k in required + ('observations', 'actions_taken', 'assistance_requested', 'planning_context', 'daily_cost_usd', 'scenario_min_hours', 'scenario_max_hours', 'fleet_context', 'contract_context')})
    for key in ('problem', 'observations', 'actions_taken', 'planning_context', 'daily_cost_usd', 'scenario_min_hours', 'scenario_max_hours', 'fleet_context', 'contract_context'):
        if case['submission'][key]:
            case['evidence'].append(dict(id=f'E{len(case["evidence"])+1}', title='Officer-reported '+key.replace('_',' '), date=datetime.now(timezone.utc).isoformat(), text=case['submission'][key], verification='Officer report; not independently corroborated'))
    case['priority'] = data['urgency']
    case['fixture_rehearsal'] = False
    return attach(case)

def prepare(case):
    case = attach(deepcopy(case))
    case.update(status='Ready', trace=[], tasks=[], approval=None, closure=False, owner=MANAGER,
        reports={}, reviews=[], decision_report=None, ai_calls=0, run_error=None,
        action_results=[], pending_actions=[], commercial_scenario={}, validation_attempts=[])
    return case

def parse_response(raw, phase, case, allowed_refs):
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith('```'): text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
        try: raw = json.loads(text)
        except (ValueError, TypeError): raise ResponseFormatError('Agent returned invalid JSON; run halted without approval.')
    if not isinstance(raw, dict): raise ValueError('Agent response must be a JSON object.')
    if not isinstance(raw.get('summary'), str) or not raw['summary'].strip(): raise ValueError('Agent summary missing.')
    if phase == 'plan':
        assignments = raw.get('assignments')
        if not isinstance(assignments, list) or len(assignments) != 2: raise ValueError('Manager must assign both specialist roles.')
        if {a.get('role') for a in assignments if isinstance(a,dict)} != set(SPECIALISTS): raise ValueError('Invalid specialist delegation.')
        if any(not isinstance(a.get('question'),str) or not a['question'].strip() for a in assignments): raise ValueError('Each assignment needs a question.')
    elif phase == 'specialist':
        for key in ('findings', 'uncertainties', 'proposed_actions'):
            if not isinstance(raw.get(key), list) or any(not isinstance(x,str) for x in raw[key]): raise ValueError('Invalid specialist report field: '+key)
        guidance = raw.get('guidance')
        if not isinstance(guidance, list): raise ValueError('Specialist guidance must be a list.')
        chunks = {x['id']:x['text'] for d in case.get('document_library',[]) for x in d.get('chunks',[])}
        normalize = lambda text: ' '.join(text.split())
        for item in guidance:
            if not isinstance(item,dict) or any(not isinstance(item.get(k),str) or not item[k].strip() for k in ('instruction','source_id','quote','applicability')):
                raise ValueError('Incomplete source-backed guidance.')
            if item['source_id'] not in allowed_refs or item['source_id'] not in chunks:
                raise ValueError('Guidance source was not retrieved.')
            if normalize(item['quote']) not in normalize(chunks[item['source_id']]):
                raise QuoteMismatch(item['source_id'])
    elif phase == 'review':
        followups = raw.get('followups')
        if not isinstance(followups,list) or len(followups)>2: raise ValueError('Invalid follow-up requests.')
        if any(not isinstance(f,dict) or f.get('role') not in SPECIALISTS or not isinstance(f.get('question'),str) or not f['question'].strip() for f in followups): raise ValueError('Invalid follow-up delegation.')
        if len({f['role'] for f in followups}) != len(followups): raise ValueError('Duplicate follow-up role.')
    elif phase == 'final':
        for key in ('decision', 'rationale'):
            if not isinstance(raw.get(key),str) or not raw[key].strip(): raise ValueError('Management decision/rationale missing.')
        for key in ('risks', 'missing_evidence', 'required_approvals'):
            if not isinstance(raw.get(key),list) or any(not isinstance(x,str) for x in raw[key]): raise ValueError('Invalid management report field: '+key)
        if not raw['required_approvals']: raise ValueError('Human approval requirements cannot be empty.')
        actions=raw.get('action_plan')
        if not isinstance(actions,list) or any(not isinstance(a,dict) or any(not isinstance(a.get(k),str) or not a[k].strip() for k in ('action','owner','depends_on')) for a in actions): raise ValueError('Invalid action plan.')
        brief = raw.get('decision_brief')
        if not isinstance(brief,dict) or any(not isinstance(brief.get(k),str) or not brief[k].strip() for k in ('severity','next_step','stoppage','duration','eta','commercial','fleet_priority')): raise ValueError('Concise decision brief missing.')
        email = raw.get('vessel_email')
        if not isinstance(email,dict) or any(not isinstance(email.get(k),str) or not email[k].strip() for k in ('subject','body')): raise ValueError('Vessel email draft missing.')
        review = raw.get('draft_review')
        if not isinstance(review,dict) or review.get('status') not in ('approved_for_human_review','revision_required') or not isinstance(review.get('reason'),str) or not review['reason'].strip(): raise ValueError('Fleet Manager draft review missing.')
    citations = raw.get('citations')
    if not isinstance(citations,list) or any(not isinstance(x,str) for x in citations): raise ValueError('Citations must be a list of source IDs.')
    if set(citations) - set(allowed_refs): raise ValueError('Agent cited unavailable evidence/reference IDs; run halted.')
    # Citation existence is checked, semantic support is still a human review task.
    return raw

def coordinate(case, invoke, publish=lambda c: None, provenance='Meta Muse · unverified AI output'):
    c = prepare(case)
    c['status'] = 'Fleet Manager planning'
    publish(deepcopy(c))
    def call(role, phase, assignment=None):
        from reference_library import model_context
        if c['ai_calls'] >= MAX_CALLS: raise ValueError('Agent call budget exceeded.')
        context = model_context(role, c, search_query=assignment or '')
        from impact import exposure, validate
        context['commercial_scenario'] = exposure(c)
        refs = context['reference_selection']['excerpt_ids']
        evidence = [e['id'] for e in c['evidence']]
        report_ids = [r['report_id'] for history in c['reports'].values() for r in history]
        # Manager receives validated specialist reports, including their source quotes.
        # Those sources remain available through the report even if its own search differs.
        forwarded_refs = [source for history in c['reports'].values() for report in history
                          for source in report.get('citations', []) + [g['source_id'] for g in report.get('guidance', [])]]
        c['status'] = role + ': ' + phase
        c['ai_calls'] += 1
        publish(deepcopy(c))
        allowed = refs+evidence+report_ids+forwarded_refs
        raw = invoke(role, phase, context, assignment)
        try:
            response = parse_response(raw, phase, c, allowed)
        except (QuoteMismatch, ResponseFormatError) as exc:
            # Never relax quotation matching or pass rejected guidance to other agents.
            if len(c['validation_attempts']) >= MAX_CORRECTIONS or c['ai_calls'] >= MAX_CALLS:
                raise ValueError('Response could not be validated within the correction budget. Review required; no final guidance issued.')
            attempt = dict(role=role, phase=phase, source_id=exc.source_id,
                           reason=str(exc), status='Correction requested', rejected_response=raw)
            c['validation_attempts'].append(attempt)
            c['status'] = role + ': correcting response format' if isinstance(exc,ResponseFormatError) else role + ': correcting source quotation'
            c['ai_calls'] += 1
            publish(deepcopy(c))
            corrected_context = deepcopy(context)
            corrected_context['_validation_feedback'] = dict(source_id=exc.source_id,
                instruction='Your previous response failed exact quotation matching. Regenerate the complete report. Copy a short contiguous quote directly from the supplied source text without paraphrasing, joining passages, ellipses or changing numbers. If unsupported, omit that guidance item and explain the source gap in uncertainties. Do not fabricate replacement evidence.')
            if isinstance(exc,ResponseFormatError):
                corrected_context['_validation_feedback']['instruction'] = 'Regenerate the complete response as one valid JSON object matching the supplied schema. No Markdown, commentary, trailing commas or unescaped quotes/newlines inside strings. Keep prose concise. Do not invent facts to complete fields; preserve unknowns and source checks.'
            try:
                response = parse_response(invoke(role, phase, corrected_context, assignment), phase, c, allowed)
            except Exception:
                attempt['status'] = 'Correction failed; run halted'
                raise
            attempt['status'] = 'Corrected response passed validation'
        if phase == 'specialist':
            validate(role, response)
            if role == SPECIALISTS[1] and response['impact']['engineering_report_id'] != c['reports'][SPECIALISTS[0]][-1]['report_id']:
                raise ValueError('Marine must use the latest Engineering report.')
        c['trace'].append(dict(step=len(c['trace'])+1, role=role, phase=phase,
            to='Specialist agents' if phase=='plan' else MANAGER if phase=='specialist' else 'Reporting officer' if phase=='final' else 'Specialist review',
            at=datetime.now(timezone.utc).isoformat(), note=response['summary'], output=response,
            evidence_ids=evidence, reference_excerpt_ids=refs, forwarded_reference_ids=sorted(set(forwarded_refs)), library_search=context['reference_selection'], provenance=provenance, company=c['company']['name']))
        publish(deepcopy(c))
        return response
    try:
        plan = call(MANAGER, 'plan')
        c['tasks'] = [dict(task=a['question'], owner=a['role'], depends='Fleet Manager delegation', status='Assigned') for a in plan['assignments']]
        # Explicit dependency: Engineering returns first; Marine receives that report.
        for assignment in sorted(plan['assignments'], key=lambda a:SPECIALISTS.index(a['role'])):
            report = call(assignment['role'], 'specialist', assignment['question'])
            report['report_id'] = ('ENG' if assignment['role']==SPECIALISTS[0] else 'MAR')+'-R1'
            c['reports'][assignment['role']] = [report]
            next(t for t in c['tasks'] if t['owner']==assignment['role'])['status']='Report returned'
        review = call(MANAGER, 'review')
        c['reviews'].append(review)
        if review['followups']:
            requests = list(review['followups'])
            if any(r['role']==SPECIALISTS[0] for r in requests) and not any(r['role']==SPECIALISTS[1] for r in requests):
                requests.append(dict(role=SPECIALISTS[1],question='Update voyage and commercial impact using the revised Engineering report.'))
            for request in sorted(requests,key=lambda a:SPECIALISTS.index(a['role'])):
                c['tasks'].append(dict(task=request['question'],owner=request['role'],depends='Manager review',status='Follow-up assigned'))
                report = call(request['role'], 'specialist', request['question'])
                report['report_id'] = ('ENG' if request['role']==SPECIALISTS[0] else 'MAR')+'-R2'
                c['reports'][request['role']].append(report)
                c['tasks'][-1]['status']='Follow-up returned'
            review = call(MANAGER, 'review', 'Final review after one bounded follow-up round. Carry unresolved matters forward; no more iterations.')
            c['reviews'].append(review)
        c['unresolved_followups'] = review['followups']
        c['decision_report'] = call(MANAGER, 'final', 'Review specialist source-backed guidance and draft a complete email to Master and Chief Engineer. Give an explicit draft approval or revision decision. Include unresolved followups, source IDs, applicability checks, uncertainties and missing evidence. Do not replace supported guidance with generic advice to consult manuals. No operational authorization.')
        c['decision_report']['authority'] = 'AI management recommendation only. Human authorization required; Master retains overriding safety authority.'
        c['decision_report']['unresolved_followups'] = deepcopy(c['unresolved_followups'])
        c['decision_report']['missing_evidence'] += [r['question'] for r in c['unresolved_followups'] if r['question'] not in c['decision_report']['missing_evidence']]
        from impact import exposure
        c['commercial_scenario'] = exposure(c)
        from agent_actions import execute
        c['status'] = 'Executing local case-document actions'
        publish(deepcopy(c))
        execute(c)
        c['status'] = 'Awaiting human review'
        c['owner'] = 'Reporting officer / qualified human approver'
    except Exception as exc:
        c['status'] = 'Run failed — review partial trace'
        c['run_error'] = str(exc) if isinstance(exc,ValueError) else 'Meta request failed; check configuration/account/API. No scripted fallback was substituted.'
    c['closure'] = False
    publish(deepcopy(c))
    return c

def rehearsal(role, phase, context, assignment):
    """Explicitly scripted architecture rehearsal; never impersonates model inference."""
    ids = [e['id'] for e in context['evidence']]
    base = dict(summary='', citations=ids[:1])
    if phase=='plan':
        return dict(base, summary='Rehearsal: Fleet Manager delegates technical and marine assessments.', assignments=[dict(role=SPECIALISTS[0], question='Assess reported engine evidence, OEM applicability, alternatives and missing confirmation.'),dict(role=SPECIALISTS[1],question='Assess oil tanker voyage risks, SMS checks, commercial uncertainty and draft notification needs.')])
    if phase=='specialist':
        from impact import ENGINEERING, MARINE
        problem = context.get('submission',{}).get('problem','Unspecified case')
        impact = dict(severity='Scripted rehearsal only: '+problem,stop_recommendation='Not determined by scripted mode',voyage_disruption='Requires live assessment of this case',repair_scope='Not inferred in rehearsal',downtime=dict(min_hours=None,max_hours=None,basis='No estimate generated in scripted rehearsal',confidence='Unassessed',assumptions=[])) if role==SPECIALISTS[0] else dict(engineering_report_id=context['reports'][SPECIALISTS[0]][-1]['report_id'],voyage_impact='Scripted rehearsal: '+problem,commercial_impact='No live commercial assessment',mitigation='Requires live case-specific assessment',notifications='No messages sent',commercial_notification=dict(subject='Scripted rehearsal - commercial update',body='No live assessment performed. No stoppage or repair is confirmed; await case-specific review.',send_status='draft_not_sent'),missing_inputs=['Verified duration and commercial terms'])
        return dict(base,impact=impact,summary='Rehearsal specialist report: evidence remains unverified.',guidance=[],findings=['Officer report received; no diagnosis inferred from narrative alone.'],uncertainties=['Need calibrated measurements, comparable baseline and physical findings.'],proposed_actions=['Request source evidence through Chief Engineer and Master; apply OEM and SMS review.'])
    if phase=='review':
        return dict(base,summary='Rehearsal manager review: ask Engineering for corroboration; do not close the alert.',followups=[] if context['reviews'] else [dict(role=SPECIALISTS[0],question='Identify what evidence would distinguish a sealing fault from a measurement problem; do not invent missing results.')])
    return dict(base,decision_brief=dict(severity='Rehearsal: unassessed',next_step='Run live assessment',stoppage='Not determined',duration='No technical estimate',eta='Not assessed',commercial='Scenario only',fleet_priority='No fleet decision made'),vessel_email=dict(subject='Fictional case: request for supporting evidence',body='Dear Master and Chief Engineer,\nThis is a scripted rehearsal draft. Please provide supporting observations and applicable source records for the reported condition. No technical procedure has been validated by this rehearsal. Fleet Ops AI'),draft_review=dict(status='revision_required',reason='Scripted rehearsal has not produced source-backed technical guidance. Run live Muse assessment for a case-specific draft.'),summary='Rehearsal management report — not Meta-generated.',decision='Request further evidence and qualified human review.',rationale='Reports do not establish a verified operational decision; uncertainty remains.',risks=['Potential main-engine impairment on a oil tanker.'],missing_evidence=['Verified OEM criteria and calibration','Physical findings and comparable measurements'],required_approvals=['Master and Chief Engineer review','Qualified company approval for proposed consequential action'],action_plan=[dict(action='Obtain and validate missing technical evidence',owner='Chief Engineer',depends_on='Shipboard authority and approved safeguards'),dict(action='Assess location-specific contingency options',owner='Marine Superintendent',depends_on='Master consultation')])
