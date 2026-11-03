"""Invented training cases, not actual measurements or OEM acceptance limits."""

CASES = [

    ('Low compression', 'Chief Engineer', 'Unit 2 compression pressure appears below the other cylinders.', 'Invented readings: 30, 24, 30, 31, 30, 29, 30 bar. Calibration and comparable operating conditions unverified. No physical inspection confirming damage.', 'Find relevant MAN guidance on compression pressure and piston ring condition; distinguish measurement error from mechanical causes.'),

    ('High exhaust temperature', 'Chief Engineer', 'Unit 4 exhaust temperature appears higher than adjacent cylinders.', 'A temperature difference was reported at steady load; no calibrated values, trend or alarm threshold supplied. No component inspection.', 'Retrieve OEM exhaust temperature and fuel injection guidance; prepare evidence checks and conditional vessel guidance.'),

    ('Starting-air difficulty', 'Chief Engineer', 'Main engine did not respond normally to a reported start attempt.', 'Starting air pressure, interlocks, control indications and sequence records are not yet supplied. No repeat attempt is assumed.', 'Search operation and manoeuvring manuals for starting air and starting interlocks; draft applicable checks without bypass instructions.'),

    ('Lubricating-oil pressure concern', 'Chief Engineer', 'A main-engine lubricating oil pressure alarm was reported.', 'Gauge reading, alarm set point, load, oil temperature and instrument verification missing. No pump failure confirmed.', 'Find applicable lubrication-system guidance and identify records needed to assess the reported alarm. Do not invent operating limits.'),

    ('Cooling-water temperature trend', 'Chief Engineer', 'Jacket cooling water temperature has reportedly risen during the watch.', 'No validated inlet/outlet readings, load trend or maintenance history supplied. Cause unknown.', 'Retrieve cooling water guidance and prepare a source-backed diagnostic evidence request and conditional guidance draft.'),

    ('Survey and certificate planning', 'Master', 'Please coordinate planning for an upcoming survey attendance.', 'Certificate list, expiry dates, class status and port schedule have not yet been provided; no overdue certificate is assumed.', 'Consult SMS and relevant circulars for planning responsibilities and draft a request for vessel records. Verify circular applicability before relying on it.'),

]





def examples():

    from benchmark_cases import benchmark_examples, stress_examples
    return [dict(label=label, data=dict(reporter_role=role, reporter_name='Alex Morgan (fictional)',

        location='Fictional demonstration voyage; actual position not supplied',

        operating_condition='Reported condition only; load and operational context to be verified',

        urgency='High' if role=='Chief Engineer' else 'Routine', problem=problem,

        observations='FICTIONAL EXERCISE: '+observations,

        actions_taken='Case reported; no inspection, repair or operational change is asserted.',

        planning_context=('FICTIONAL PLANNING ASSUMPTIONS, not OEM durations: '+{'Low compression':'Crew proposes a 4–8 hour diagnostic window; if a component repair is required, reserve 24–48 hours subject to scope, parts and testing. Delivery buffer 12 hours.', 'High exhaust temperature':'Conditional inspection window 3–6 hours; if a fuel equipment replacement is warranted, planning allowance 8–16 hours subject to confirmed spare and approved scope. Delivery buffer 6 hours.', 'Starting-air difficulty':'Safe anchorage assumed for this exercise. Troubleshooting allowance 2–6 hours; component replacement branch 12–24 hours, spares and service attendance unconfirmed. Delivery buffer 4 hours.', 'Lubricating-oil pressure concern':'No repair time is established. An inspection window of 4–12 hours is a planning assumption only; bearing damage would require a new estimate. Delivery buffer 8 hours.', 'Cooling-water temperature trend':'Inspection planning allowance 2–4 hours; repair branch 8–20 hours conditional on parts and access. Delivery buffer 10 hours.', 'Survey and certificate planning':'Planned port stay 18 hours; fictional survey attendance allowance 6–10 hours within that stay. No defect or repair stoppage reported; class availability and scope unconfirmed.'}[label]), daily_cost_usd='24000' if role=='Chief Engineer' else '18000',

        scenario_min_hours={'Low compression':'24','High exhaust temperature':'8','Starting-air difficulty':'12','Lubricating-oil pressure concern':'4','Cooling-water temperature trend':'8','Survey and certificate planning':'0'}[label],
        scenario_max_hours={'Low compression':'48','High exhaust temperature':'16','Starting-air difficulty':'24','Lubricating-oil pressure concern':'12','Cooling-water temperature trend':'20','Survey and certificate planning':'0'}[label],
        assistance_requested=request)) for label,role,problem,observations,request in CASES] + benchmark_examples() + stress_examples()

