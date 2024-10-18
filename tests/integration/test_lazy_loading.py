import zntrack.examples


def test_run_project(proj_path):
    with zntrack.Project() as project:
        node = zntrack.examples.ParamsToOuts(params=42)

    assert "outs" not in node.__dict__
    project.build()
    project.run()
    assert node.__dict__["outs"] == 42
    node = node.from_rev()
    assert "outs" not in node.__dict__
    node = node.from_rev(lazy_evaluation=False)
    assert node.__dict__["outs"] == 42


# def test_ParamsToOuts(proj_path, lazy, eager):
#         with zntrack.Project() as project:
#             node = zntrack.examples.ParamsToOuts(params=42)
#         project.run(eager=eager)

#         if not eager:
#             node.load()
#         if lazy and not eager:
#             assert node.__dict__["outs"] is ZNTRACK_LAZY_VALUE
#         else:
#             assert node.__dict__["outs"] is 42
#         assert node.outs == 42


# @pytest.mark.parametrize("eager", [True, False])
# @pytest.mark.parametrize("lazy", [True, False])
# def test_CollectOutputs(proj_path, lazy, eager):
#     with zntrack.config.updated_config(lazy=lazy):
#         with zntrack.Project() as project:
#             a = zntrack.examples.ParamsToOuts(params=17, name="a")
#             b = zntrack.examples.ParamsToOuts(params=42, name="b")
#             node = zntrack.examples.AddNodeNumbers(numbers=[a, b])
#         project.run(eager=eager)

#         if not eager:
#             node.load()
#         if lazy and not eager:
#             assert node.__dict__["sum"] is ZNTRACK_LAZY_VALUE
#             assert node.__dict__["numbers"] is ZNTRACK_LAZY_VALUEv
#             assert node.numbers[0].__dict__["outs"] is ZNTRACK_LAZY_VALUE
#             assert node.numbers[1].__dict__["outs"] is ZNTRACK_LAZY_VALUE
#         else:
#             assert node.__dict__["sum"] is 59
#             assert node.__dict__["numbers"][0].name == "a"
#             assert node.__dict__["numbers"][1].name == "b"

#         assert node.numbers[0].outs == 17
#         assert node.numbers[1].outs == 42
#         assert node.sum == 59

#         if not eager:
#             # Check that non-lazy loading works
#             node = node.from_rev(lazy=False)
#             assert node.__dict__["sum"] is 59
#             assert node.__dict__["numbers"][0].name == "a"
#             assert node.__dict__["numbers"][1].name == "b"
