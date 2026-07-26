from fly_in import main


def test() -> None:
    res = main("test_configs/test_2.txt")
    assert not isinstance(res, list)
