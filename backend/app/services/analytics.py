from collections import Counter, defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.entries import Entry
from app.models.enums import ResultStatus
from app.models.players import Player
from app.models.races import Race
from app.models.results import Result
from app.models.tracks import Track


class AnalyticsService:
    def track_summary(self, db: Session, track_id: int) -> dict[str, object]:
        track = db.get(Track, track_id)
        if track is None:
            raise LookupError("track not found")

        races = list(
            db.scalars(
                select(Race)
                .where(Race.track_id == track_id)
                .options(joinedload(Race.entries), joinedload(Race.results))
            ).unique().all()
        )
        results = list(
            db.scalars(
                select(Result)
                .join(Result.race)
                .where(Race.track_id == track_id)
                .options(joinedload(Result.player), joinedload(Result.race))
            ).unique().all()
        )
        entries = list(
            db.scalars(
                select(Entry)
                .join(Entry.race)
                .where(Race.track_id == track_id)
                .options(joinedload(Entry.player), joinedload(Entry.race))
            ).unique().all()
        )

        race_status_counts = Counter(race.status for race in races)
        grade_counts = Counter(entry.player.grade for entry in entries)
        latest_race_date = max((race.race_date for race in races), default=None)
        recent_30_races = [
            {
                "race_id": race.id,
                "race_date": race.race_date,
                "track_name": track.name,
                "race_number": race.race_number,
                "status": race.status,
            }
            for race in sorted(races, key=lambda item: (item.race_date, item.race_number), reverse=True)[:30]
        ]
        return {
            "track_id": track.id,
            "track_name": track.name,
            "code": track.code,
            "region": track.region,
            "total_races": len(races),
            "completed_races": sum(1 for race in races if race.status == "completed"),
            "total_entries": len(entries),
            "unique_players": len({entry.player_id for entry in entries}),
            "latest_race_date": latest_race_date,
            "race_status_counts": dict(race_status_counts),
            "grade_counts": dict(grade_counts),
            "recent_30_races": recent_30_races,
        }

    def track_players(self, db: Session, track_id: int) -> list[dict[str, object]]:
        track = db.get(Track, track_id)
        if track is None:
            raise LookupError("track not found")

        players = list(
            db.scalars(
                select(Player)
                .join(Entry, Entry.player_id == Player.id)
                .join(Race, Race.id == Entry.race_id)
                .where(Race.track_id == track_id)
                .options(joinedload(Player.entries))
            ).unique().all()
        )
        stats_by_player = defaultdict(lambda: {"starts": 0, "wins": 0, "top2": 0, "top3": 0, "dq": 0, "wd": 0})
        result_rows = list(
            db.scalars(
                select(Result)
                .join(Result.race)
                .where(Race.track_id == track_id)
                .options(joinedload(Result.player), joinedload(Result.race))
            ).unique().all()
        )
        for result in result_rows:
            stats = stats_by_player[result.player_id]
            stats["starts"] += 1
            if result.result_status == ResultStatus.finished.value:
                if result.finish_position == 1:
                    stats["wins"] += 1
                if result.finish_position <= 2:
                    stats["top2"] += 1
                if result.finish_position <= 3:
                    stats["top3"] += 1
            elif result.result_status == ResultStatus.disqualified.value:
                stats["dq"] += 1
            elif result.result_status == ResultStatus.withdrawn.value:
                stats["wd"] += 1

        payload = []
        for player in players:
            stats = stats_by_player[player.id]
            starts = stats["starts"]
            payload.append(
                {
                    "player_id": player.id,
                    "player_number": player.player_number,
                    "name": player.name,
                    "grade": player.grade,
                    "starts": starts,
                    "wins": stats["wins"],
                    "top2": stats["top2"],
                    "top3": stats["top3"],
                    "win_rate": round(stats["wins"] / starts, 4) if starts else 0.0,
                    "top2_rate": round(stats["top2"] / starts, 4) if starts else 0.0,
                    "top3_rate": round(stats["top3"] / starts, 4) if starts else 0.0,
                    "disqualified_count": stats["dq"],
                    "withdrawn_count": stats["wd"],
                }
            )
        return sorted(payload, key=lambda item: (-item["starts"], item["player_number"]))

    def races_summary(self, db: Session) -> dict[str, object]:
        total_races = db.scalar(select(func.count()).select_from(Race)) or 0
        scheduled_races = db.scalar(select(func.count()).select_from(Race).where(Race.status == "scheduled")) or 0
        in_progress_races = db.scalar(select(func.count()).select_from(Race).where(Race.status == "in_progress")) or 0
        completed_races = db.scalar(select(func.count()).select_from(Race).where(Race.status == "completed")) or 0
        total_players = db.scalar(select(func.count()).select_from(Player)) or 0
        total_results = db.scalar(select(func.count()).select_from(Result)) or 0
        latest_race_date = db.scalar(select(func.max(Race.race_date)))
        track_count = db.scalar(select(func.count()).select_from(Track)) or 0
        return {
            "total_races": int(total_races),
            "scheduled_races": int(scheduled_races),
            "in_progress_races": int(in_progress_races),
            "completed_races": int(completed_races),
            "total_players": int(total_players),
            "total_results": int(total_results),
            "latest_race_date": latest_race_date,
            "track_count": int(track_count),
        }
