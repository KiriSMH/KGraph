// 1. Count nodes by labels.
MATCH (n)
UNWIND labels(n) AS label
RETURN label, count(*) AS count
ORDER BY label;

// 2. Count relationships by relationship types.
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY relationship_type;

// 3. Show all relationships.
MATCH (a)-[r]->(b)
RETURN a, r, b;

// 4. Show facts only.
MATCH (a)-[r]->(b)
WHERE r.evidence_type = "fact"
RETURN a, r, b;

// 5. Show hypotheses only.
MATCH (a)-[r:HYPOTHESIZED_RELATED_TO]->(b)
RETURN a, r, b;

// 6. Show subgraph around material_b.
MATCH path = (m:Entity {canonical_name: "material_b"})-[*1..2]-(n)
RETURN path;

// 7. Show subgraph around material_bb.
MATCH path = (m:Entity {canonical_name: "material_bb"})-[*1..2]-(n)
RETURN path;

// 8. Check that HYPOTHESIZED_RELATED_TO has visual_style="dashed".
MATCH (a)-[r:HYPOTHESIZED_RELATED_TO]->(b)
RETURN a.name AS source, type(r) AS relationship_type, b.name AS target, r.evidence_type AS evidence_type, r.visual_style AS visual_style;

// 9. Check that fact relationships have visual_style="solid".
MATCH (a)-[r]->(b)
WHERE r.evidence_type = "fact"
RETURN type(r) AS relationship_type, r.evidence_type AS evidence_type, r.visual_style AS visual_style, count(*) AS count
ORDER BY relationship_type;
