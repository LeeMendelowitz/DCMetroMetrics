# DC Metro Metrics Data Download

http://dcmetrometrics.com/data

This data is released under the ODC Open Database License (ODbL) v1.0.
http://opendatacommons.org/licenses/odbl/summary/

Contact: Lee Mendelowitz <Lee.Mendelowitz@gmail.com>



# Files

## timestamp

The UTC timestamp of the data export.

## stations.csv

Each station is a row. Some stations have two station codes
if they have two platforms serving different lines (Fort Totten,
Gallery Place, L'Enfant, Metro Center).

- *code*: The WMATA station code.
- *long_name*: The full name of the station
- *short_name*: A shortened name of the station, good for URL routing.
- *line_code1-3*: The color code of the metro lines serving the station platform.
- *other_station_code*: The station code of the other platform for a separate line at the same station. This applies to Fort Totten, Gallery Place, L'Enfant Plaza, and Metro Center.





## units.csv

A directory of all escalators and elevators.

- *unit_id*: The id of the unit. (e.g. "A03S02ESCALATOR)
- *station_code*: The station code of the unit (e.g. "A03")
- *station_name*: The station name as provided by the WMATA API. This may have spelling mistakes or be different than the official station name. Join with stations.csv for a more consistent station name. (e.g. "DUPONT CIRCLE")
- *station_desc*: Station level description for the unit. Used if a station has multiple entrances, but NA for most units. (e.g "South/DuPont Circle Entrance")
- *esc_desc*: Unit level description. (e.g "Escalator between street and mezzanine")
- *unit_type*: ESCALATOR or ELEVATOR





## unit_statuses.csv

A list of all stored unit statuses. A unit status is an escalator/elevator state with a start time and and end time. A unit only has one unit status at any given time. 

Note that data may be stale for stretches of time due to stale data provided by the WMATA API or outages in data collection in the DC Metro Metrics application. Escalator & Elevator statuses are constantly changing, so if you see no statuses for 3 or more consecutive hours, the data is likely stale during that stretch of time. There is over a 7 day outage in July 2014 when WMATA made unannounced backwards incompatible changes to the WMATA API which broke the DC Metro Metrics app.

When an escalator or elevator appears in the WMATA API list of outages for the first time, it is given an initial OPERATIONAL status, followed by the outage status.

 - *unit_id*: The unit_id of the escalator or elevator
 - *time*: The start time of the status in UTC.
 - *end_time*: The end time of the status in UTC. If NA, the status is still active.
 - *metro_open_time*: The number of seconds for which Metrorail was open during the duration of the status.
 - *update_type*: The type of the update. Should be one of: "Break", "Fix", "Off", "On", "Update". These categorize the type of state changes:

   - Break: the unit has transitioned to a broken state from a non-broken state. (e.g. Operational -> Service Call)
   - Fix means the unit has transitioned to an operational status from a broken status. (e.g. Major Report -> Operational)
   - Off means the unit has been turned off, but is not broken. (e.g. Operational -> Walker or Operational -> Preventive Maintenance Inspection)
   - On means the unit has been turned back on, but was not broken. (e.g. Preventive Maintenance Inspection -> Operational)
   - Update means the unit is still broken or off but has changed states. (e.g. Service Call -> Minor Repair)

 - *symptom_description*: The description of the unit state. WMATA changed the descriptions in July 2014, so there is some duplication here ("MAJOR REPAIR" and "Major Repair", "CALLBACK/REPAIR" -> "Service Call"). I can't make a one to one correspondence between the old symptom descriptions and the new symptom descriptions, so I didn't bother cleaning this up.

 - *symptom_category*: The type of the symptom description. Is one of: "ON", "BROKEN", "OFF", "REHAB", "INSPECTION"





## daily_unit_reports.csv

Daily summary of the performance of a single escalator or elevator.

For accounting purposes, a "Metro Day" is considered to be the time between system openings. For example, the Metro Day corresponding to Sunday 2/22/2015 is 2/22/2015 7 AM EST (system opening Sunday) to 2/23/2015 5 AM EST (system opening Monday). Some outages are not discovered by Metro employees until the next calendar day (after system close). This accounting attempts to correct for that. Just a heads up.

 - *day*: The "Metro day" (see above)
 - *unit_id*: The unit id of the summary. 
 - *num_fixes*: Number of *new* fixes for this unit on this day.
 - *num_inspections*: Number of *new* inspections for the unit on this day.
 - *num_breaks*: Number of *new* breaks of the unit on this day. 
 - *availability*: The percentage of the time that Metro was open for which the unit was operating.
 - *broken_time_percentage*: The percentage of the time that Metro was open on this day for which the unit was broken (statuses with symptom_category == "BROKEN").





## daily_system_reports.csv

The averages of all daily_unit_reports.csv for a given day, to provide a system wide snapshot.

 - *day*
 - *elevators_num_fixes*
 - *escalators_availability*
 - *escalators_num_fixes*
 - *elevators_num_inspections*
 - *elevators_num_breaks*
 - *escalators_num_inspections*
 - *elevators_num_units*: Number of elevators included in the daily system report.
 - *escalators_num_units*: Number of escalators included in the daily system report.
 - *escalators_num_breaks*
 - *elevators_broken_time_percentage*
 - *elevators_availability*
 - *escalators_broken_time_percentage*


 ## hotcars.csv

 HotCar report data. Each hot car report is from a tweet mentioning a single valid 4 digit Metro car number.

 - *car_number*: Metro car number
 - *color*: Line color
 - *time*: Tweet time (UTC)
 - *text*: Tweet text
 - *handle*: Twitter user's screen name
 - *user_id*: Twitter user's user_id
 - *tweet_id*


