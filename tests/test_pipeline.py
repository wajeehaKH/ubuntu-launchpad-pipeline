import pytest

import src.pipeline as pipeline


def test_pipeline_does_not_transform_when_ingestion_fails(monkeypatch):
    calls = []

    def fake_ingestion(limit):
        calls.append("ingestion")
        raise RuntimeError("Ingestion failed")

    def fake_transformation():
        calls.append("transformation")

    monkeypatch.setattr(pipeline, "run_ingestion", fake_ingestion)
    monkeypatch.setattr(
        pipeline, "run_transformations", fake_transformation
    )

    with pytest.raises(RuntimeError, match="Ingestion failed"):
        pipeline.run_pipeline()

    assert calls == ["ingestion"]


def test_pipeline_runs_ingestion_before_transformation(monkeypatch):
    calls = []

    def fake_ingestion(limit):
        calls.append(("ingestion", limit))

    def fake_transformation():
        calls.append(("transformation",))

    monkeypatch.setattr(pipeline, "run_ingestion", fake_ingestion)
    monkeypatch.setattr(
        pipeline, "run_transformations", fake_transformation
    )

    pipeline.run_pipeline(limit=3)

    assert calls == [
        ("ingestion", 3),
        ("transformation",),
    ]
