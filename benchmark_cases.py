"""Fictional evaluation inputs. Expected answers are kept out of model inputs."""
from copy import deepcopy

BASE = dict(reporter_role='Chief Engineer', reporter_name='Alex Morgan (fictional)',
    location='MT Aster Horizon, oil tanker; fictional open-sea voyage to next port',
    operating_condition='Steady reported engine load; detailed trend and calibration records pending',
    urgency='High', actions_taken='Master informed. No engine stoppage, inspection, repair or commercial notification is claimed.',
    assistance_requested='Assess this case using applicable OEM and SMS sources. Advise Fleet Manager on seriousness, conditional stoppage and repair scope, duration basis, voyage and commercial impact. Prepare vessel guidance and a commercial-team notification draft; do not send messages.',
    daily_cost_usd='24000', scenario_min_hours='6', scenario_max_hours='8')

CASES = [
    dict(id='BENCH-01', label='Benchmark 1 - Low peak pressure: sensor first', data=dict(BASE,
        problem='Unit 3 reports low peak firing pressure (Pmax), not low compression pressure.',
        observations='FICTIONAL: the installed peak-pressure sensor reports Unit 3 below its recent trend and other units. No independently verified peak-pressure measurement is yet available. Compression pressure has not been reported low. No scavenge-space inspection, exhaust-valve function check or injector findings are available. No fault is confirmed.',
        planning_context='USER-SUPPLIED FICTIONAL PLANNING INPUT: if an exhaust-valve and fuel-injector change-out proves necessary, allow 6-8 hours for that job. This is not an OEM duration or confirmation that replacement is needed. Suitable spare injectors and exhaust valve(s) are required; onboard inventory, compatibility and serviceability are not yet confirmed. Diagnostic time, cooldown/isolation and post-work testing may add time and must be scoped separately. Additional demo assumption: next-port ETA has 2 hours of schedule buffer and unchanged speed thereafter. Daily delay cost USD 24000 is illustrative, not a contractual rate or proven loss.')),
    dict(id='BENCH-02', label='Benchmark 2 - Conflicting peak-pressure measurements', data=dict(BASE,
        problem='Installed sensor reports low Unit 3 peak pressure, but an independent measurement conflicts with it.',
        observations='FICTIONAL: installed sensor continues to indicate low Unit 3 Pmax. A separate portable indicator reading reportedly matches the other units at a reported comparable load. Its calibration certificate, timing and raw traces have not been supplied. No low compression or physical component damage is reported. Neither measurement is independently verified in this case.',
        planning_context='The crew proposes the same hypothetical 6-8-hour exhaust-valve/injector replacement window, but the measurements conflict and no mechanical fault is established. Spares availability is unverified. Do not treat this contingency as an approved repair, necessary stoppage or actual delay. Additional fictional assumptions: 2-hour ETA buffer and USD 24000/day gross delay exposure.')),
    dict(id='BENCH-03', label='Benchmark 3 - Planned survey: no engine fault', data=dict(BASE,
        reporter_role='Master', urgency='Routine', operating_condition='Planning an upcoming port call; no machinery abnormality reported',
        problem='Coordinate a planned class/statutory survey attendance during the next port stay.',
        observations='FICTIONAL: port stay planned for 18 hours; requested survey attendance allowance 6-10 hours within that stay. Certificate list, actual due dates, survey scope, class confirmation and port schedule are still pending. No overdue certificate, machinery fault, low peak pressure or repair requirement is reported.',
        planning_context='FICTIONAL PLANNING INPUT: if the attendance fits within the existing 18-hour port stay, incremental voyage delay is 0 hours. Delayed attendance, expanded scope or findings would require reassessment. Daily cost USD 18000 is illustrative only. No engine repair or 6-8-hour component change-out applies to this case.',
        daily_cost_usd='18000',scenario_min_hours='0',scenario_max_hours='0')),
]


def benchmark_examples():
    return deepcopy(CASES)


def stress_examples():
    """Authored stress variations, not claims of a blind independent evaluation."""
    fleet = ('FICTIONAL FLEET: MT Aster Horizon has the reported fault. MT Aster Meridian has a survey due during its next 24-hour port stay and cannot release its reserved exhaust valve without review. MT Aster Bay reports a compatible spare but is 18 hours away; transfer feasibility, transport and compatibility are unverified. One shore service team is committed to Meridian. Consider resource conflicts and fleet priorities; no transfers or dispatches have occurred.')
    contract = ('FICTIONAL CONTRACT EXCERPT FOR TESTING ONLY: Arrival deadline 18:00 UTC on the demonstration voyage day; baseline ETA 16:00 UTC. Delay past the deadline gives charterer a cancellation option, subject to notice and applicable exceptions; cancellation is not automatic. Demurrage rate USD 30000/day applies only to counted time after allowed laytime is exhausted under the agreed NOR/laytime terms. At-sea delay does not itself start demurrage. A berth slot may be lost; later port/laytime facts, notices and exceptions are not yet available. Do not classify the illustrative USD 24000/day planning cost as demurrage or sum both without checking overlap.')
    first=deepcopy(CASES[0])
    first.update(id='STRESS-01',label='Stress test - Missed ETA and charter exposure')
    first['data'].update(observations='FICTIONAL: Chief Engineer reports the sensor has been checked and a separate calibrated indicator corroborates low Unit 3 peak firing pressure at comparable load. Raw traces await shore review. Component condition is not yet confirmed. No low compression reported.',
        planning_context='FICTIONAL: 6-8-hour conditional change-out job; suitable spare injectors and exhaust valve reportedly onboard, certification/compatibility to be verified. Baseline ETA 16:00 UTC; arrival deadline 18:00 UTC on the same demonstration day. Assume no time recovery for sensitivity analysis: 6-8 hours shifts ETA to 22:00-00:00 UTC (midnight is the next day), 4-6 hours beyond deadline, before additional task time. Stoppage and change-out remain conditional on findings and authorization.',
        fleet_context=fleet,contract_context=contract)
    second=deepcopy(first)
    second.update(id='STRESS-02',label='Stress test - Missing spare and fleet conflict')
    second['data'].update(planning_context='FICTIONAL UPDATE: compatible replacement exhaust valve is NOT onboard; spare injectors are reportedly onboard but serviceability unverified. The 6-8 hours is hands-on change-out time only AFTER the correct parts, crew and access are ready. Total downtime cannot be capped at 8 hours. Baseline ETA 16:00 UTC; arrival deadline 18:00 UTC; no recovery assumed. Fleet alternatives are in fleet_context. Do not invent a delivery time or commit another vessel.',scenario_min_hours='',scenario_max_hours='')
    return [first,second]
