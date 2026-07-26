from fly_in import main


def test_valid_map() -> None:
    result = main("test_configs/test_0.txt")

    assert isinstance(result, int)
    assert result > 0
