from fly_in import main


def test() -> None:
    res = main("test_configs/test_1.txt")
    assert not isinstance(res, list)
