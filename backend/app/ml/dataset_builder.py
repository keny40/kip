from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
import csv
import json
import statistics
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.entries import Entry
from app.models.players import Player
from app.models.races import Race
from app.models.results import Result
from app.models.tracks import Track


COMPLETED_RACE_STATUSES = {"completed", "finished"}


@dataclass(frozen=True)
class TrainingReadinessThresholds:
    min_completed_races: int = 500
    min_valid_entry_rows: int = 3000
    min_median_player_history: int = 5
    max_missing_result_rate: float = 0.05


@dataclass(frozen=True)
class TrainingDataSummary:
    completed_races: int
    total_races: int
    total_entries: int
    result_rows: int
    valid_entry_rows: int
    missing_result_rows: int
    missing_result_rate: float
    rank1_count: int
    rank2_count: int
    rank3_count: int
    average_history_per_player: float
    median_history_per_player: float
    stable_external_player_identifier: bool


@dataclass(frozen=True)
class TrainingReadiness:
    status: str
    reason: str | None
    summary: TrainingDataSummary
    thresholds: TrainingReadinessThresholds
    deficits: dict[str, float]


@dataclass(frozen=True)
class TrainingDatasetRow:
    race_date: str
    track_code: str
    race_number: int
    race_id: int
    player_id: int
    player_number: int
    player_name: str
    entry_number: int
    grade: str
    period_number: str | None
    result_rank: int | None
    result_status: str | None
    recent5_start_count: int
    recent5_avg_rank: float | None
    recent5_win_count: int
    recent5_top3_count: int
    recent10_avg_rank: float | None
    track_history_start_count: int
    track_avg_rank: float | None
    days_since_last_race: int | None
    has_prior_history: bool
    missing_result: bool


class TrainingDatasetBuilder:
    """Build leakage-safe one-row-per-entry training data from existing DB rows.

    The builder only reads from the database. Historical features are calculated
    from results strictly before the target race ordering.
    """

    fieldnames = list(TrainingDatasetRow.__dataclass_fields__.keys())

    def __init__(self, thresholds: TrainingReadinessThresholds | None = None) -> None:
        self.thresholds = thresholds or TrainingReadinessThresholds()

    def summarize(self, db: Session) -> TrainingDataSummary:
        total_races = db.scalar(select(func.count()).select_from(Race)) or 0
        completed_races = (
            db.scalar(select(func.count()).select_from(Race).where(Race.status.in_(COMPLETED_RACE_STATUSES))) or 0
        )
        total_entries = db.scalar(select(func.count()).select_from(Entry)) or 0
        result_rows = db.scalar(select(func.count()).select_from(Result)) or 0
        valid_entry_rows = (
            db.scalar(
                select(func.count())
                .select_from(Entry)
                .join(Result, (Result.race_id == Entry.race_id) & (Result.player_id == Entry.player_id))
            )
            or 0
        )
        missing_result_rows = max(total_entries - valid_entry_rows, 0)
        missing_result_rate = round(missing_result_rows / total_entries, 4) if total_entries else 0.0
        rank_counts = dict(db.execute(select(Result.finish_position, func.count()).group_by(Result.finish_position)).all())
        per_player_history = [
            count
            for (count,) in db.execute(select(func.count()).select_from(Result).group_by(Result.player_id)).all()
        ]
        average_history = round(sum(per_player_history) / len(per_player_history), 4) if per_player_history else 0.0
        median_history = float(statistics.median(per_player_history)) if per_player_history else 0.0
        return TrainingDataSummary(
            completed_races=completed_races,
            total_races=total_races,
            total_entries=total_entries,
            result_rows=result_rows,
            valid_entry_rows=valid_entry_rows,
            missing_result_rows=missing_result_rows,
            missing_result_rate=missing_result_rate,
            rank1_count=int(rank_counts.get(1, 0)),
            rank2_count=int(rank_counts.get(2, 0)),
            rank3_count=int(rank_counts.get(3, 0)),
            average_history_per_player=average_history,
            median_history_per_player=median_history,
            stable_external_player_identifier=False,
        )

    def assess_readiness(self, db: Session) -> TrainingReadiness:
        summary = self.summarize(db)
        thresholds = self.thresholds
        deficits: dict[str, float] = {}
        if summary.completed_races < thresholds.min_completed_races:
            deficits["completed_races"] = thresholds.min_completed_races - summary.completed_races
        if summary.valid_entry_rows < thresholds.min_valid_entry_rows:
            deficits["valid_entry_rows"] = thresholds.min_valid_entry_rows - summary.valid_entry_rows
        if summary.median_history_per_player < thresholds.min_median_player_history:
            deficits["median_player_history"] = thresholds.min_median_player_history - summary.median_history_per_player
        if summary.missing_result_rate > thresholds.max_missing_result_rate:
            deficits["missing_result_rate"] = round(summary.missing_result_rate - thresholds.max_missing_result_rate, 4)

        return TrainingReadiness(
            status="INSUFFICIENT_TRAINING_DATA" if deficits else "READY",
            reason="INSUFFICIENT_TRAINING_DATA" if deficits else None,
            summary=summary,
            thresholds=thresholds,
            deficits=deficits,
        )

    def build_rows(self, db: Session) -> list[TrainingDatasetRow]:
        entries = list(
            db.scalars(
                select(Entry)
                .options(
                    joinedload(Entry.race).joinedload(Race.track),
                    joinedload(Entry.player),
                )
                .join(Entry.race)
                .order_by(Race.race_date.asc(), Race.scheduled_start_time.asc(), Race.race_number.asc(), Entry.entry_number.asc())
            ).unique()
        )
        result_map = {
            (result.race_id, result.player_id): result
            for result in db.scalars(select(Result).options(joinedload(Result.race).joinedload(Race.track))).all()
        }
        history_by_player: dict[int, list[Result]] = defaultdict(list)
        rows: list[TrainingDatasetRow] = []

        for entry in entries:
            race = entry.race
            player = entry.player
            prior_results = list(history_by_player[entry.player_id])
            finished_prior = [item for item in prior_results if item.finish_position is not None]
            recent5 = finished_prior[-5:]
            recent10 = finished_prior[-10:]
            track_prior = [item for item in finished_prior if item.race and item.race.track_id == race.track_id]
            last_race_date = finished_prior[-1].race.race_date if finished_prior and finished_prior[-1].race else None
            result = result_map.get((entry.race_id, entry.player_id))
            rows.append(
                TrainingDatasetRow(
                    race_date=race.race_date.isoformat(),
                    track_code=race.track.code if race.track else "",
                    race_number=race.race_number,
                    race_id=race.id,
                    player_id=player.id,
                    player_number=player.player_number,
                    player_name=player.name,
                    entry_number=entry.entry_number,
                    grade=player.grade,
                    period_number=None,
                    result_rank=result.finish_position if result else None,
                    result_status=result.result_status if result else None,
                    recent5_start_count=len(recent5),
                    recent5_avg_rank=_average_rank(recent5),
                    recent5_win_count=sum(1 for item in recent5 if item.finish_position == 1),
                    recent5_top3_count=sum(1 for item in recent5 if item.finish_position is not None and item.finish_position <= 3),
                    recent10_avg_rank=_average_rank(recent10),
                    track_history_start_count=len(track_prior),
                    track_avg_rank=_average_rank(track_prior),
                    days_since_last_race=(race.race_date - last_race_date).days if last_race_date else None,
                    has_prior_history=bool(finished_prior),
                    missing_result=result is None,
                )
            )
            if result is not None:
                history_by_player[entry.player_id].append(result)

        return rows

    def write_dataset(self, db: Session, output_path: Path, report_path: Path) -> dict[str, object]:
        rows = self.build_rows(db)
        readiness = self.assess_readiness(db)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(asdict(row))
        report = {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "row_count": len(rows),
            "valid_training_rows": sum(1 for row in rows if row.result_rank is not None),
            "dataset_columns": self.fieldnames,
            "leakage_policy": "Historical features use only results appended before each target race in race_date/start/race_number order.",
            "cold_start_policy": "Missing prior history is represented by null averages, zero counts, and has_prior_history=false.",
            "readiness": _dataclass_to_dict(readiness),
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report


def _average_rank(results: list[Result]) -> float | None:
    ranks = [item.finish_position for item in results if item.finish_position is not None]
    return round(sum(ranks) / len(ranks), 4) if ranks else None


def _dataclass_to_dict(value) -> dict:
    return asdict(value)
