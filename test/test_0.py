from fly_in import main


def test():
    res = main("test_configs/test_0.txt")
    assert isinstance(res, list)
