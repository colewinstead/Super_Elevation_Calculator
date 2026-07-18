import unittest

from scripts.validate_release_version import parse_version, release_tags


class ReleaseVersionTests(unittest.TestCase):
    def test_parse_version_accepts_numeric_semver(self):
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))

    def test_parse_version_rejects_non_release_labels(self):
        with self.assertRaises(ValueError):
            parse_version("1.2")
        with self.assertRaises(ValueError):
            parse_version("1.2.3-beta")

    def test_release_tags_accept_existing_tag_case(self):
        self.assertEqual(
            release_tags(["v1.0.0", "V1.1.0", "other"]),
            {"v1.0.0": (1, 0, 0), "V1.1.0": (1, 1, 0)},
        )


if __name__ == "__main__":
    unittest.main()
