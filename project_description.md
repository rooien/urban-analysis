
Introduced ourselves and the key roles.
 
High Level

- Reallocate road space - understand what happens to businesses and their revenue when we reallocate space to pedestrians or a bike area.
- There are limited amounts of space on the road so when we allocate more space to pedestrians or cyclists how does this affect the other stakeholders, namely business owners.
- Really high level of where the project sits at strategically.
- Understanding what impacts there are for parking utilization when we implement one of the interventions such as a bike lane or pedestrian area.
- Accounting for all the parking numbers pre-and post-infrastructure is available.
 
Datasets:

- All information and work will be released publicly for public help.
- Research project focused on understanding the effects of street space optimization initiatives.
- All datasets are there to use but focus on the ones in the project brief.
 
Research Question
How does parking use change with bike lanes constructed?
 
Null hypothesis - there has been no change. If there has been a change what has the change been and why? 
 
If all the parking available was at capacity pre-intervention. Since the bike lane intervention how has the parking capacity changed.
 
Focus on Metropolitan Melbourne and Regional Victoria. CBD already has some data for parking spots. Further prioritize the protected bike lanes datasets at this stage.
 
Have all there parking spaces, and want to understand how many people are actually using these spaces and the impact of adding bike lanes. So for example, if we remove some spaces does it result in less people being able to park in the area.
 
Must haves:

- Dataset that map this out over time so the parking utilization, ideally showing the before and after.
 
Nice to have:

- Visualization or interactive dashboard.
- Interpretation from the students. 


Project - Urban Streetscape Intervention Analysis Loop paragraph
Meeting Minutes 14 July 2026
Project Overview

- Streetscape Intervention Analysis: brand new Chameleon project 
- Goal: analyze how road/streetscape changes affect pedestrians, cyclists, public transport, and vehicles 
- Mentor: Scott West (sessional academic, School of IT, 3 years at Deakin) 
- Product owners: Matthew and Danielle (represent the customer, set priorities) 
- Company director: Sing (high-level admin, approves special requests, attends select meetings) 
Platforms and Tools

- All communication via Microsoft Teams; all code stored on GitHub 
- GitHub account needs a new repository created for this project 
- RO has already set up a group chat and Microsoft Planner 
- Project management via Microsoft Planner (preferred over Trello/Jira/Monday to avoid cost) 
- Labels per stream, buckets: Backlog, Sprint 1 In Progress, Completed, Sprint 2 
- Coordination lead to flesh out the existing planner with lists and stream labels 
- Cloud services (e.g. AWS): submit a written proposal to the company director if needed 
Stream Structure

- Agreed to scrap the original data engineering/analytics/research/GIS streams 
- Moving to four stakeholder-focused streams: 
1. Cycling and public transport mode shift 
2. Traffic volumes and parking 
3. Pedestrian counts 
4. Temporal patterns  
- Stream allocation spreadsheet to be updated; everyone to submit preference by Thursday 16th July, 5:00 PM 
- Key alignment point: all streams must share the same tech stack and methodology to avoid sprawl 
1. e.g. don’t have one stream on Tableau and another on Power BI 
Tech Stack and Data

- R and Python confirmed; visualization tool (Power BI or Tableau) to be confirmed with POs 
- Power BI noted as easier to learn; subscription status unclear 
- Ro shared a proven dataset list from the MOP project in the chat 
- Datasets from VICRoads, PTV, data.vic.gov.au likely to require coordinate reference system (CRS) reprojection 
- Do not assume all datasets share the same coordinate system 
- ABS census due in August: defer population data integration until after release to avoid mid-sprint disruption 
- Proxy labeling approach recommended (from MOP precedent) for cases where ground truth labels are absent 
- Define and document the proxy method upfront so it can be swapped later without rewriting code 
- Comprehensive documentation required throughout (not just at the end): README, methodology, model comparisons, limitations, future work 
