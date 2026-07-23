from pathlib import Path

from superlig_forecast.data.warehouse import WAREHOUSE_TABLES, Warehouse


def test_empty_build_is_deterministic_and_creates_schema(tmp_path: Path) -> None:
    warehouse = Warehouse(tmp_path / "model.duckdb")

    first = warehouse.build([])
    second = warehouse.build([])

    assert first.data_hash == second.data_hash
    assert set(warehouse.tables()) == set(WAREHOUSE_TABLES)
