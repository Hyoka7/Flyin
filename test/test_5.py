from fly_in import main


def test():
    res = main("test_configs/test_5.txt")
    assert not isinstance(res, list)
