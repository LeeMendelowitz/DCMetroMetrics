"""
eles.defs

Define constants for escalator/elevator status codes
"""

from collections import defaultdict

OPERATIONAL_CODE = -1
NUM_ESCALATORS = 588
NUM_ELEVATORS = 238

###################################################
# Define symptomToCategory. Consider adding these
# to the symptom_codes database
symptomToCategory = defaultdict(lambda: 'BROKEN')

offStatuses = ['SAFETY WORK ORDER',
               'TURNED OFF/WALKER',
               'SCHEDULED SUPPORT',
               'PREV. MAINT. REPAIRS']

inspectStatuses = ['SAFETY INSPECTION',
                   'PREV. MAINT. INSPECTION',
                   'PREV. MAINT. COMPLIANCE INSPECTION']

rehabStatuses = ['REHAB/MODERNIZATION']

plannedRepairStatuses = ['PREV. MAINT. REPAIRS']

# Define outages which are planned.
# Note: Saying that 'TURNED OFF/WALKER' is a planned outage
#       is fairly generous.
plannedOutageSymptoms = offStatuses + inspectStatuses + rehabStatuses\
                + plannedRepairStatuses

symptomToCategory['OPERATIONAL'] = 'ON'
symptomToCategory.update((status, 'OFF') for status in offStatuses)
symptomToCategory.update((status, 'INSPECTION') for status in inspectStatuses)
symptomToCategory.update((status, 'REHAB') for status in rehabStatuses)
