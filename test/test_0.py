from fly_in import main


def test_valid_map():
    result = main("test_configs/test_0.txt")

    assert isinstance(result, int)
    assert result > 0