-- Optional semantic ranking adapter for PostgreSQL deployments.
-- This file is intentionally not required by the offline-first core.
-- Jev scores are derived, provider/model-dependent signals, not canonical
-- biological evidence and not a replacement for deterministic indexes.
-- For the RefSeq Release 237 sort/rank/classify/route/map plan, see
-- docs/jev-refseq-release-237-plan.json and docs/jev-refseq-release-237.sql.

-- CREATE EXTENSION jev CASCADE;

-- The view should contain only the fields needed for the ranking question.
-- Keep stable IDs and an explicit release in every row.
-- CREATE VIEW protein_planner AS
-- SELECT
--     p.id AS protein_id,
--     p.preferred_name AS protein_name,
--     p.record_type,
--     p.organism_context_id,
--     p.sequence_record_id,
--     p.release_id
-- FROM protein p;

-- Example semantic ranking. Persist the returned row_id, query, model version,
-- score, and retrieval time in a derived-index manifest or audit table.
-- SELECT
--     protein_id,
--     protein_name,
--     jev_score(
--         protein_planner,
--         'how relevant is this protein to the requested molecular function?',
--         ARRAY['low', 'medium', 'high']
--     ) AS semantic_score
-- FROM protein_planner
-- WHERE release_id = 'release:example-1'
-- ORDER BY semantic_score DESC, protein_id;

-- Deterministic fallback when Jev is unavailable or not approved:
-- SELECT protein_id, protein_name
-- FROM protein_planner
-- WHERE release_id = 'release:example-1'
-- ORDER BY protein_name, protein_id;
