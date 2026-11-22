
# Ubuntu Launchpad Pipeline

A Python-based data ingestion pipeline that retrieves Ubuntu bug tasks from Launchpad and stores raw bug and task data in PostgreSQL.

## Architecture

Launchpad API → Python ingestion → PostgreSQL

## Technologies

- Python 3.12
- Launchpad API / launchpadlib
- PostgreSQL 16
- Psycopg 3
- Docker Compose

## Features

- Launchpad task retrieval with pagination
- Associated bug detail retrieval
- Raw JSON persistence using PostgreSQL JSONB
- Transactional bug and task upserts
- HTTP 503 retry handling

## Setup

Clone the repository:

    git clone https://github.com/wajeehaKH/ubuntu-launchpad-pipeline.git
    cd ubuntu-launchpad-pipeline

Create your environment file:

    cp .env.example .env

Update the database credentials in `.env`.

Build and start the services:

    sudo docker compose up -d --build

Run ingestion:

    sudo docker compose exec ingestion python -m src.ingestion.run

## Configuration

Database credentials are supplied through `.env`. This file is excluded from version control. Use `.env.example` as a template.

## Current Status

Basic ingestion functionality is implemented. Live end-to-end verification is pending recovery of the Launchpad task-search service.
