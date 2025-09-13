import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from show_scores import ScoreViewer


def test_no_patches_generated(capsys):
    viewer = ScoreViewer()
    scores = [{
        "evaluation_status": "completed",
        "generation_score": 0,
        "evaluation_score": 0,
    }]

    viewer.show_statistics(scores)
    captured = capsys.readouterr()
    assert "No patches generated; success rate unavailable." in captured.out
