"""Execute local case-document work; never imply external or physical execution."""
from datetime import datetime, timezone


def execute(case):
    results = []
    for role, history in case['reports'].items():
        report = history[-1]
        results.append(dict(owner=role, action='Compile specialist findings and evidence request',
            status='Completed locally', completed_at=datetime.now(timezone.utc).isoformat(),
            result=dict(report_id=report['report_id'], findings=report['findings'],
                        citations=report['citations'], guidance=report['guidance'], evidence_requests=report['uncertainties']),
            limitation='Evidence requests prepared; no inspection or external contact performed.'))
    final = case['decision_report']
    results.append(dict(owner='Fleet Manager', action='Assemble case pack and return results to reporting officer',
        status='Completed locally', completed_at=datetime.now(timezone.utc).isoformat(),
        result=dict(case_id=case['id'], decision=final['decision'],
                    vessel_email=final['vessel_email'], draft_review=final['draft_review'], outstanding_evidence=final['missing_evidence'], approvals=final['required_approvals']),
        limitation='Returned in this dashboard and case download; no external message sent.'))
    case['action_results'] = results
    case['pending_actions'] = [dict(a, status='Pending — requires evidence, authorization or an external connection')
                               for a in final['action_plan']]
    return results
