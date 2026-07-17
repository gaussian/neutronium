from neutronium.utils.performance import Performance


def test_get_time_since_is_nonnegative():
    p = Performance()
    assert p.get_time_since() >= 0


def test_reset_and_num_levels():
    p = Performance()
    p.reset()
    assert p.get_time_since(level=2) >= 0
    assert p.num_levels == 4


def test_print_time_since_outputs_label(capsys):
    Performance().print_time_since(pre_print="step")
    assert "step" in capsys.readouterr().out
