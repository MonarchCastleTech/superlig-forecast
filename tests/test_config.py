from pathlib import Path

from superlig_forecast.config import Settings


def test_settings_loads_all_turkish_competitions(tmp_path: Path) -> None:
    path = tmp_path / "competitions.yaml"
    path.write_text(
        "competitions:\n"
        "  - {id: TR1, tier: 1, name: Super Lig}\n"
        "  - {id: TR2, tier: 2, name: 1. Lig}\n"
        "  - {id: TR3, tier: 3, name: 2. Lig}\n"
        "  - {id: TR4, tier: 4, name: 3. Lig}\n"
        "  - {id: TRC, tier: 0, name: Turkish Cup}\n",
        encoding="utf-8",
    )

    settings = Settings.load(path)

    assert [item.tier for item in settings.competitions] == [1, 2, 3, 4, 0]
