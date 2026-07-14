from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.external_race_history import ExternalRace, ExternalRaceEntry, ExternalRaceResult


class RaceHistoryAnalyticsService:
    def players(self, db: Session, *, year: str | None = None, meet_name: str | None = None, period_number: str | None = None, grade: str | None = None, minimum_starts: int = 0) -> list[dict]:
        races = self._race_map(db, year=year, meet_name=meet_name)
        entries = self._entries(db, races, period_number=period_number, grade=grade)
        results = self._results(db, races)
        results_by_race_entry = {(item.external_race_id, item.entry_number): item for item in results}
        grouped: dict[tuple[str, str | None], list[tuple[ExternalRaceEntry, ExternalRaceResult | None]]] = defaultdict(list)
        for entry in entries:
            grouped[(entry.player_name, entry.period_number)].append((entry, results_by_race_entry.get((entry.external_race_id, entry.entry_number))))

        payload = []
        for (name, period), rows in grouped.items():
            if len(rows) < minimum_starts:
                continue
            finished = [result for _, result in rows if result and result.result_rank is not None and result.result_status == "FINISHED"]
            ranks = [result.result_rank for result in finished if result.result_rank is not None]
            ordered = sorted(rows, key=lambda pair: (races[pair[0].external_race_id].race_date or races[pair[0].external_race_id].created_at.date()))
            recent = [result for _, result in ordered[-5:] if result and result.result_rank is not None]
            payload.append(
                {
                    "player_name": name,
                    "period_number": period,
                    "total_starts": len(rows),
                    "completed_starts": None,
                    "wins": sum(1 for rank in ranks if rank == 1),
                    "second_places": sum(1 for rank in ranks if rank == 2),
                    "third_places": sum(1 for rank in ranks if rank == 3),
                    "top3_count": sum(1 for rank in ranks if rank <= 3),
                    "average_rank": None,
                    "best_rank": min(ranks) if ranks else None,
                    "recent5_average_rank": None,
                    "recent5_top3_count": sum(1 for item in recent if item.result_rank and item.result_rank <= 3),
                    "tracks_participated": len({races[entry.external_race_id].meet_name for entry, _ in rows}),
                    "last_race_date": max((races[entry.external_race_id].race_date for entry, _ in rows if races[entry.external_race_id].race_date), default=None),
                }
            )
        return sorted(payload, key=lambda item: (-item["total_starts"], item["player_name"], item["period_number"] or ""))

    def tracks(self, db: Session, *, year: str | None = None, meet_name: str | None = None) -> list[dict]:
        races = list(self._race_map(db, year=year, meet_name=meet_name).values())
        entries = self._entries(db, {race.id: race for race in races})
        results = self._results(db, {race.id: race for race in races})
        entries_by_race = Counter(entry.external_race_id for entry in entries)
        results_by_race = Counter(result.external_race_id for result in results)
        grouped = defaultdict(list)
        for race in races:
            grouped[race.meet_name].append(race)
        payload = []
        for meet, meet_races in grouped.items():
            race_ids = {race.id for race in meet_races}
            meet_entries = [entry for entry in entries if entry.external_race_id in race_ids]
            meet_results = [result for result in results if result.external_race_id in race_ids]
            payload.append(
                {
                    "meet_name": meet,
                    "race_count": len(meet_races),
                    "completed_race_count": sum(1 for race in meet_races if race.status in {"completed", "finished"}),
                    "total_entries": len(meet_entries),
                    "result_count": len(meet_results),
                    "average_entries_per_race": round(len(meet_entries) / len(meet_races), 2) if meet_races else 0.0,
                    "unique_player_candidates": len({(entry.player_name, entry.period_number) for entry in meet_entries}),
                    "missing_result_count": 0,
                    "disqualified_count": sum(1 for result in meet_results if result.result_status == "DISQUALIFIED"),
                    "withdrawn_count": sum(1 for result in meet_results if result.result_status == "WITHDRAWN"),
                    "first_race_date": min((race.race_date for race in meet_races if race.race_date), default=None),
                    "last_race_date": max((race.race_date for race in meet_races if race.race_date), default=None),
                }
            )
        return sorted(payload, key=lambda item: item["meet_name"])

    def summary(self, db: Session, *, year: str | None = None) -> dict:
        races = self._race_map(db, year=year)
        entries = self._entries(db, races)
        results = self._results(db, races)
        rank_counts = Counter(str(result.result_rank) + "위" for result in results if result.result_rank is not None)
        grade_counts = Counter(entry.grade or "unknown" for entry in entries)
        track_counts = Counter(race.meet_name for race in races.values())
        month_counts = Counter((race.race_date.strftime("%Y-%m") if race.race_date else "unknown") for race in races.values())
        return {
            "total_races": len(races),
            "total_entries": len(entries),
            "total_results": len(results),
            "unique_player_candidates": len({(entry.player_name, entry.period_number) for entry in entries}),
            "result_coverage_rate": None,
            "result_coverage_type": "top3_only" if results else "unverified",
            "rank_distribution": [{"rank": key, "count": rank_counts[key]} for key in sorted(rank_counts)],
            "grade_distribution": [{"grade": key, "count": grade_counts[key]} for key in sorted(grade_counts)],
            "track_distribution": [{"meet_name": key, "count": track_counts[key]} for key in sorted(track_counts)],
            "monthly_race_counts": [{"month": key, "count": month_counts[key]} for key in sorted(month_counts)],
        }

    def quality(self, db: Session) -> dict:
        races = list(db.scalars(select(ExternalRace)).all())
        entries = list(db.scalars(select(ExternalRaceEntry)).all())
        results = list(db.scalars(select(ExternalRaceResult)).all())
        entry_keys = {(entry.external_race_id, entry.entry_number) for entry in entries}
        result_keys = {(result.external_race_id, result.entry_number) for result in results}
        return {
            "race_count": len(races),
            "entry_count": len(entries),
            "result_count": len(results),
            "missing_race_date": sum(race.race_date is None for race in races),
            "missing_meet_name": sum(not race.meet_name for race in races),
            "missing_player_name": sum(not entry.player_name for entry in entries),
            "missing_period_number": sum(not entry.period_number for entry in entries),
            "missing_grade": sum(not entry.grade or entry.grade == "unknown" for entry in entries),
            "missing_results": 0,
            "unmatched_entries": 0,
            "unmatched_results": len(result_keys - entry_keys),
            "duplicate_race_natural_keys": self._duplicate_races(db),
            "duplicate_entry_numbers": self._duplicates(db, ExternalRaceEntry),
            "duplicate_result_numbers": self._duplicates(db, ExternalRaceResult),
            "invalid_result_rank": sum(result.result_rank is not None and result.result_rank < 1 for result in results),
            "withdrawn_count": sum(result.result_status == "WITHDRAWN" for result in results),
            "disqualified_count": sum(result.result_status == "DISQUALIFIED" for result in results),
            "did_not_start_count": sum(result.result_status == "DID_NOT_START" for result in results),
            "latest_collected_at": max([*(race.collected_at for race in races), *(entry.collected_at for entry in entries), *(result.collected_at for result in results)], default=None),
        }

    def _race_map(self, db: Session, *, year: str | None = None, meet_name: str | None = None) -> dict[int, ExternalRace]:
        query = select(ExternalRace)
        if year:
            query = query.where(ExternalRace.standard_year == year)
        if meet_name:
            query = query.where(ExternalRace.meet_name == meet_name)
        return {race.id: race for race in db.scalars(query).all()}

    def _entries(self, db: Session, races: dict[int, ExternalRace], *, period_number: str | None = None, grade: str | None = None) -> list[ExternalRaceEntry]:
        if not races:
            return []
        query = select(ExternalRaceEntry).where(ExternalRaceEntry.external_race_id.in_(races.keys()))
        if period_number:
            query = query.where(ExternalRaceEntry.period_number == period_number)
        if grade:
            query = query.where(ExternalRaceEntry.grade == grade)
        return list(db.scalars(query).all())

    def _results(self, db: Session, races: dict[int, ExternalRace]) -> list[ExternalRaceResult]:
        if not races:
            return []
        return list(db.scalars(select(ExternalRaceResult).where(ExternalRaceResult.external_race_id.in_(races.keys()))).all())

    def _duplicate_races(self, db: Session) -> int:
        groups = db.execute(select(func.count()).select_from(ExternalRace).group_by(ExternalRace.source, ExternalRace.standard_year, ExternalRace.meet_name, ExternalRace.week_count, ExternalRace.day_count, ExternalRace.race_number).having(func.count() > 1)).scalars().all()
        return sum(count - 1 for count in groups)

    def _duplicates(self, db: Session, model) -> int:
        groups = db.execute(select(func.count()).select_from(model).group_by(model.external_race_id, model.entry_number).having(func.count() > 1)).scalars().all()
        return sum(count - 1 for count in groups)
