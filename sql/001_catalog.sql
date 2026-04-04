-- ASHA Sahayak: Catalog and Schema Setup
-- Run in Databricks SQL or a notebook with appropriate permissions

CREATE CATALOG IF NOT EXISTS asha_sahayak;
USE CATALOG asha_sahayak;

CREATE SCHEMA IF NOT EXISTS core
  COMMENT 'Core entities: patients, workers, villages';

CREATE SCHEMA IF NOT EXISTS clinical
  COMMENT 'Clinical data: reports, observations, encounters, medications';

CREATE SCHEMA IF NOT EXISTS ops
  COMMENT 'Operational data: schedules, rations, alerts, appointments';

CREATE SCHEMA IF NOT EXISTS reference
  COMMENT 'Reference data: guidelines, thresholds, nutrition rules';

CREATE SCHEMA IF NOT EXISTS serving
  COMMENT 'RAG serving: chunks, embeddings, retrieval logs';

-- Create managed volumes for raw file storage
CREATE VOLUME IF NOT EXISTS core.raw_audio;
CREATE VOLUME IF NOT EXISTS core.raw_images;
CREATE VOLUME IF NOT EXISTS core.raw_pdfs;
CREATE VOLUME IF NOT EXISTS core.extracted;
CREATE VOLUME IF NOT EXISTS core.exports;
