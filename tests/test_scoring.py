import pytest
from api.scoring import mustache_score, classify_epicness


class TestMustacheScore:
    def test_pure_epic_returns_100(self):
        assert mustache_score(1.0, 0, 0, 0) == 100.0

    def test_pure_medium(self):
        assert mustache_score(0, 1.0, 0, 0) == pytest.approx(85.0)

    def test_pure_medium_thin(self):
        assert mustache_score(0, 0, 1.0, 0) == pytest.approx(50.0)

    def test_pure_thin(self):
        assert mustache_score(0, 0, 0, 1.0) == pytest.approx(10.0)

    def test_score_clipped_to_0_100(self):
        assert mustache_score(0, 0, 0, 0) == 0.0
        assert mustache_score(1.0, 1.0, 1.0, 1.0) == 100.0

    def test_mixed_probabilities(self):
        score = mustache_score(0.5, 0.3, 0.1, 0.1)
        assert 0 <= score <= 100


class TestClassifyEpicness:
    def test_legendary(self):
        title, _, _ = classify_epicness(95)
        assert "legendarisk" in title.lower()

    def test_epic(self):
        title, _, _ = classify_epicness(80)
        assert "episk" in title.lower()

    def test_respectable(self):
        title, _, _ = classify_epicness(60)
        assert "respektabel" in title.lower()

    def test_promising(self):
        title, _, _ = classify_epicness(25)
        assert "lovande" in title.lower()

    def test_thin(self):
        title, _, _ = classify_epicness(0)
        assert "fjunig" in title.lower()

    def test_boundary_95(self):
        title_below, _, _ = classify_epicness(94.9)
        title_at, _, _ = classify_epicness(95)
        assert "episk" in title_below.lower()
        assert "legendarisk" in title_at.lower()

    def test_returns_three_values(self):
        result = classify_epicness(50)
        assert len(result) == 3
        title, desc, video = result
        assert isinstance(title, str)
        assert isinstance(desc, str)
        assert isinstance(video, str)
