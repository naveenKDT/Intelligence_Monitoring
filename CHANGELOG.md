# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed

- **Database Models**: Renamed `metadata` column to `metadata_json` in `ScrapeQueue`, `Company`, `News`, `Document`, `Product`, and `Service` models to avoid SQLAlchemy's reserved attribute name conflict. This resolves the `sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API` error when running `run_scraper.py`.