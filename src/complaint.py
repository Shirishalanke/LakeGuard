"""Builds a structured complaint from a citizen report."""
from datetime import datetime


def build_complaint(r) -> str:
    """r is one row of the reports table. Returns plain text ready to copy."""
    return f"""COMPLAINT: VISIBLE POLLUTION IN LAKE
Prepared on: {datetime.now():%d-%m-%Y %H:%M}
LakeGuard Report ID: {r['Report ID']}

To,
The Commissioner / Concerned Zonal Officer
Greater Hyderabad Municipal Corporation

Subject: Visible pollution at {r['Lake Name']} - request for cleanup

Lake name: {r['Lake Name']}
Location (lat, long): {r['Latitude']}, {r['Longitude']}
Map link: https://www.google.com/maps?q={r['Latitude']},{r['Longitude']}
Date/time observed: {r['Date/Time']}

Description of the problem (citizen's words):
{r['Description']}

Automated visual assessment (LakeGuard AI): {r['Severity']} severity, type: {r['Pollution Type']}.
Note: this is an automated visual assessment of a photograph, NOT a scientific
or laboratory measurement of water quality.

Photo evidence: attached (file: {r['Image Path']})

I request the concerned department to inspect the site and take
necessary cleanup action.
"""