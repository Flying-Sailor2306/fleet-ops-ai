"""Role-specific assessment contracts and transparent scenario arithmetic."""
import math

ENGINEERING = dict(severity='Case-specific severity and evidence', stop_recommendation='Whether a stoppage review is indicated, conditional or not established; rationale, not an order',
    voyage_disruption='Likelihood/conditions and uncertainty, no invented probabilities', repair_scope='Likely diagnostic/repair scope and prerequisites',
    downtime=dict(min_hours='Number or null',max_hours='Number or null',basis='Reported planning input, source-backed estimate, or explicit AI planning assumption; never claim OEM duration without source',confidence='Confidence and why',assumptions=['Crew, parts, access, cooldown, isolation, repair, testing and logistics assumptions']))
MARINE = dict(engineering_report_id='Exact latest ENG report ID', voyage_impact='Case-specific schedule/ETA/port implications based on Engineering',
    commercial_impact='Scenario exposure, off-hire/charter implications conditional on actual terms; no automatic loss or demurrage claim',
    mitigation='Options, dependencies and tradeoffs for this case', notifications='Draft recipients and purpose, nothing sent', missing_inputs=['Missing commercial inputs'],
    commercial_notification=dict(subject='Case-specific subject for commercial team',body='Complete draft: reported facts, conditional stoppage/duration basis, ETA risk, uncertainties and next update; never claim unperformed work or that a message was sent',send_status='draft_not_sent'))


def validate(role, report):
    data = report.get('impact')
    schema = ENGINEERING if role == 'Engineering Superintendent' else MARINE
    if not isinstance(data,dict): raise ValueError('Case-specific impact assessment missing.')
    for key, sample in schema.items():
        value = data.get(key)
        if isinstance(sample,str) and (not isinstance(value,str) or not value.strip()): raise ValueError('Impact field missing: '+key)
    if role == 'Engineering Superintendent':
        d=data.get('downtime')
        if not isinstance(d,dict): raise ValueError('Downtime basis missing.')
        lo,hi=d.get('min_hours'),d.get('max_hours')
        if (lo is None)!=(hi is None): raise ValueError('Provide both duration bounds or neither.')
        if lo is not None and (any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in (lo,hi)) or lo>hi): raise ValueError('Invalid downtime range.')
        if any(not isinstance(d.get(k),str) or not d[k].strip() for k in ('basis','confidence')) or not isinstance(d.get('assumptions'),list) or not all(isinstance(x,str) for x in d['assumptions']): raise ValueError('Downtime assumptions missing.')
    else:
        if not isinstance(data.get('missing_inputs'),list) or not all(isinstance(x,str) for x in data['missing_inputs']): raise ValueError('Commercial inputs missing.')
        draft=data.get('commercial_notification')
        if not isinstance(draft,dict) or any(not isinstance(draft.get(k),str) or not draft[k].strip() for k in ('subject','body')) or draft.get('send_status')!='draft_not_sent': raise ValueError('Commercial notification must be a complete unsent draft.')


def exposure(case):
    history=case.get('reports',{}).get('Engineering Superintendent',[])
    if not history: return {'status':'Awaiting Engineering report'}
    report=history[-1]
    duration=report['impact']['downtime']
    submission=case.get('submission',{})
    duration_origin='Engineering conditional estimate'
    if duration['min_hours'] is None and submission.get('scenario_min_hours','') != '':
        duration=dict(min_hours=float(submission['scenario_min_hours']),max_hours=float(submission['scenario_max_hours']),
            basis='Officer-entered what-if duration, not an Engineering or OEM estimate', confidence='Unverified planning assumption', assumptions=[submission.get('planning_context','')])
        duration_origin='Submitted what-if scenario; Engineering duration remains unknown'
    rate=case.get('submission',{}).get('daily_cost_usd','')
    result=dict(engineering_report_id=report['report_id'],duration=duration,duration_origin=duration_origin,daily_cost_usd=rate or None,
        caveat='Gross scenario exposure before schedule-buffer/contract adjustments; not proven financial loss, off-hire entitlement or demurrage. Rate and duration assumptions need verification.')
    if rate and duration['min_hours'] is not None:
        result.update(status='Scenario calculated',formula='hours / 24 × submitted daily cost',
            min_usd=round(duration['min_hours']/24*float(rate),2),max_usd=round(duration['max_hours']/24*float(rate),2))
    else: result['status']='Cannot calculate amount: duration or daily cost missing'
    return result
