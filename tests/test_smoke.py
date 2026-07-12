from pathlib import Path
import unittest


class SmokeTest(unittest.TestCase):
    def test_project_skeleton_exists(self) -> None:
        root = Path(__file__).resolve().parents[1]
        expected = [
            root / "backend" / "app" / "main.py",
            root / "frontend" / "lib" / "main.dart",
            root / "README.md",
            root / "ARCHITECTURE.md",
            root / "ROADMAP.md",
            root / "INSTALL.md",
        ]
        for path in expected:
            self.assertTrue(path.exists(), f"Missing expected file: {path}")


if __name__ == "__main__":
    unittest.main()
