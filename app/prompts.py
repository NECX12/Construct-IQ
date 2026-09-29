BLUEPRINT_EXTRACTION_PROMPT = """
You are extracting measurable information from an architectural blueprint.

Return only JSON matching the supplied schema. Extract only information visible
in the document. Do not invent dimensions or quantities. Use null for unknown
room dimensions. Use confidence values from 0 to 1 and set review_required to
true for inferred or uncertain measurements.

For building_elements, use only these element_type values when applicable:
- block_wall: wall surface area in m2
- floor_area: floor surface area in m2

Include the drawing type, rooms, visible door and window counts, supported
building elements, and warnings for missing or uncertain information.
""".strip()