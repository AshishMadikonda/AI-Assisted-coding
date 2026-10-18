# Classification test results

Run date: 2026-10-18

Output of `classify_issue()` for every photo in `ai/sample-images/`.
The last column is filled in by hand after checking each result against the photo.

| Photo | Category | Urgency | Description | Correct? |
|---|---|---|---|---|
| Air pollution and smog.jpg | unknown | medium | Heavy traffic congestion and dense smog creating poor visibility on an urban roadway. | |
| Blocked drains.jpg | water_drainage | medium | A street storm drain grate is clogged with accumulated plastic waste and litter. | |
| Construction debris on roads.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Damaged electrical wiring.jpg | electricity | high | Tangled and exposed wires hang low from a utility pole box along a pedestrian walkway. | |
| Damaged footpaths.jpg | road_damage | medium | Broken and displaced sidewalk tiles and sunken drain cover slabs creating a hazard for pedestrians. | |
| Flooding and waterlogging.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Garbage overflow and illegal dumping.jpg | sanitation | high | A massive pile of uncollected garbage and organic waste is dumped across the roadway, blocking traffic and posing a severe health hazard. | |
| Illegal construction and encroachment.jpg | road_damage | medium | An unpaved, uneven dirt road with sand and debris affecting residential vehicular movement. | |
| Illegal waste dumping.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Overflowing garbage bins.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Sewage overflow.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Stagnant water and mosquito breeding.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Stray animals.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Traffic congestion.jpg | unknown | medium | Severe traffic congestion and vehicle gridlock blocking a busy intersection. | |
| Unhygienic public toilets.jpg | sanitation | medium | A public toilet is damaged and unsanitary, with a detached seat and debris on the floor. | |
| Water pipeline leaks.jpg | ERROR | - | 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand  | |
| Water pollution.jpg | sanitation | medium | A large accumulation of garbage and floral waste is dumped along the riverbank and floating in the water. | |
| broken streelights.jpg | ERROR | - | [WinError 10053] An established connection was aborted by the software in your host machine | |
| pothole.jpg | road_damage | medium | A large, deep pothole filled with muddy water is obstructing a busy road. | |

## Findings

(The AI correctly classified several civic issues, including blocked drains, damaged electrical wiring, damaged footpaths, garbage overflow, unhygienic public toilets, and potholes. Some non-civic or unsupported cases were labelled as `unknown`, but these results need to be checked against the intended categories. Several images could not be tested because the AI service returned HTTP 503 errors or a connection error. Improvements should include retrying failed requests, handling service errors gracefully, and improving classification for ambiguous categories such as traffic congestion, air pollution, and illegal encroachment.)
