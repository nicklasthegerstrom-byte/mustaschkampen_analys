import pytest
from api.scoring import weighted_epic_score, classify_epicness


class TestWeightedEpicScore:
    def test_pure_epic_returns_100(self):
        assert weighted_epic_score(1.0, 0, 0, 0) == 100.0

    def test_near_epic_threshold(self):
        # p_epic >= 0.99 → 100
        assert weighted_epic_score(0.99, 0, 0, 0) == 100.0
        assert weighted_epic_score(0.98, 0, 0, 0) < 100.0

    def test_pure_thin_low_score(self):
        score = weighted_epic_score(0, 0, 0, 1.0)
        assert 0 <= score <= 20

    def test_pure_medium(self):
        score = weighted_epic_score(0, 1.0, 0, 0)
        assert score == pytest.approx(80.0)

    def test_pure_medium_thin(self):
        score = weighted_epic_score(0, 0, 1.0, 0)
        assert score == pytest.approx(50.0)

    def test_score_clipped_to_0_100(self):
        score = weighted_epic_score(0, 0, 0, 0)
        assert score == 0.0
        score = weighted_epic_score(1.0, 1.0, 1.0, 1.0)
        assert score == 100.0

    def test_mixed_probabilities(self):
        score = weighted_epic_score(0.5, 0.3, 0.1, 0.1)
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
