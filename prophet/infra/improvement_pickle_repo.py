import pickle
from pathlib import Path
from typing import override

from prophet.domain.improvement import Improvement
from prophet.domain.improvement_repo import IImprovementRepo, ImprovementNotFoundError


class ImprovementPickleRepo(IImprovementRepo):
    pickle_dir: Path

    def __init__(self, pickle_dir: str | Path = "/tmp/pollenprophet") -> None:
        self.pickle_dir = Path(pickle_dir)
        self.pickle_dir.mkdir(parents=True, exist_ok=True)

    @override
    def add(self, improvement: Improvement) -> None:
        fname = self.pickle_dir / improvement.id
        try:
            with open(fname, "wb") as f:
                pickle.dump(improvement, f)
                print(f"Saved {fname}")
        except FileExistsError:
            print(f"Error saving file {fname}")

    @override
    def add_all(self, improvements: list[Improvement]) -> None:
        for imp in improvements:
            self.add(imp)

    @override
    def get(self, id: str) -> Improvement:
        try:
            with open(self.pickle_dir / id, "rb") as f:
                improvement: Improvement = pickle.load(f)
        except FileNotFoundError:
            raise ImprovementNotFoundError

        return improvement

    @override
    def get_all(self) -> list[Improvement]:
        improvements: list[Improvement] = []
        for fname in Path(self.pickle_dir).iterdir():
            try:
                improvements.append(self.get(fname.name))
            except ImprovementNotFoundError:
                print(f"File {fname.absolute()} is not a valid Improvement.")
        return improvements
