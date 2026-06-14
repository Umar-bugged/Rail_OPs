from backend.src.data import sample_data
from backend.src.features.build_features import FEATURE_COLUMNS, TARGET_COLUMN, prepare_training_frame


def test_prepare_training_frame_contains_expected_features() -> None:
    frame = prepare_training_frame(
        delay=sample_data.sample_delay(),
        schedule=sample_data.sample_schedule(),
        stations=sample_data.sample_stations(),
        trains=sample_data.sample_trains(),
    )

    assert not frame.empty
    assert TARGET_COLUMN in frame.columns
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
    assert frame[TARGET_COLUMN].min() >= 0
