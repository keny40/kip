from datetime import date

from sqlalchemy.orm import Session

from app.models.enums import RaceStatus, ResultStatus
from app.models.results import Result
from app.repositories.entries import EntryRepository
from app.repositories.players import PlayerRepository
from app.repositories.results import ResultRepository
from app.repositories.races import RaceRepository
from app.schemas.results import PlayerStatisticsFiltersRead, ResultCreate, ResultUpdate


class ResultService:
    def __init__(
        self,
        repository: ResultRepository | None = None,
        race_repository: RaceRepository | None = None,
        entry_repository: EntryRepository | None = None,
    ) -> None:
        self.repository = repository or ResultRepository()
        self.race_repository = race_repository or RaceRepository()
        self.entry_repository = entry_repository or EntryRepository()
        self.player_repository = PlayerRepository()

    def list_results(
        self,
        db: Session,
        *,
        race_id: int | None,
        player_id: int | None,
        race_date=None,
        track_name: str | None = None,
        result_status: str | None = None,
        page: int,
        page_size: int,
    ) -> tuple[list[Result], int]:
        offset = (page - 1) * page_size
        return self.repository.list_results(
            db,
            race_id=race_id,
            player_id=player_id,
            race_date=race_date,
            track_name=track_name,
            result_status=result_status,
            offset=offset,
            limit=page_size,
        )

    def get_result(self, db: Session, result_id: int) -> Result | None:
        return self.repository.get_by_id(db, result_id)

    def create_result(self, db: Session, payload: ResultCreate) -> Result:
        race = self.race_repository.get_by_id(db, payload.race_id)
        if race is None:
            raise LookupError("race not found")
        entry = self.entry_repository.get_by_race_and_player(db, payload.race_id, payload.player_id)
        if entry is None:
            raise ValueError("player is not entered in this race")
        if self.repository.get_by_race_and_player(db, payload.race_id, payload.player_id):
            raise ValueError("result already exists for this player in race")
        if self.repository.get_by_race_and_position(db, payload.race_id, payload.finish_position):
            raise ValueError("finish_position already exists in race")
        if payload.result_status != ResultStatus.finished.value and payload.finish_position < 1:
            raise ValueError("finish_position must be 1 or greater")

        result = Result(**payload.model_dump())
        created = self.repository.create(db, result)
        self._recalculate_race_status(db, payload.race_id)
        return created

    def update_result(self, db: Session, result_id: int, payload: ResultUpdate) -> Result:
        result = self.repository.get_by_id(db, result_id)
        if result is None:
            raise LookupError("result not found")

        updates = payload.model_dump(exclude_unset=True)
        if "finish_position" in updates and updates["finish_position"] != result.finish_position:
            duplicate = self.repository.get_by_race_and_position(db, result.race_id, updates["finish_position"])
            if duplicate and duplicate.id != result.id:
                raise ValueError("finish_position already exists in race")

        for key, value in updates.items():
            setattr(result, key, value)
        db.flush()
        db.refresh(result)
        self._recalculate_race_status(db, result.race_id)
        return result

    def delete_result(self, db: Session, result_id: int) -> None:
        result = self.repository.get_by_id(db, result_id)
        if result is None:
            raise LookupError("result not found")
        race_id = result.race_id
        self.repository.delete(db, result)
        self._recalculate_race_status(db, race_id)

    def list_race_results(self, db: Session, race_id: int) -> list[Result]:
        return self.repository.list_by_race(db, race_id)

    def race_results_payload(self, db: Session, race_id: int):
        race = self.race_repository.get_by_id(db, race_id)
        if race is None:
            raise LookupError("race not found")
        results = self.repository.list_by_race(db, race_id)
        return race, results

    def get_player_statistics(
        self,
        db: Session,
        player_id: int,
        *,
        track_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        last_n: int | None = None,
        grade: str | None = None,
    ) -> dict[str, object]:
        player = self.player_repository.get_by_id(db, player_id)
        if player is None:
            raise LookupError("player not found")
        results = self.repository.list_by_player(db, player_id)
        filtered_results = [
            result
            for result in results
            if (track_id is None or result.race.track_id == track_id)
            and (date_from is None or result.race.race_date >= date_from)
            and (date_to is None or result.race.race_date <= date_to)
            and (grade is None or result.player.grade == grade)
        ]
        ordered_results = sorted(
            filtered_results,
            key=lambda result: (result.race.race_date, result.race.scheduled_start_time, result.id),
            reverse=True,
        )
        if last_n is not None:
            ordered_results = ordered_results[:last_n]

        total_races = len(ordered_results)
        finished_results = [result for result in ordered_results if result.result_status == ResultStatus.finished.value]
        first = sum(1 for result in finished_results if result.finish_position == 1)
        second = sum(1 for result in finished_results if result.finish_position == 2)
        third = sum(1 for result in finished_results if result.finish_position == 3)
        dnf = sum(1 for result in ordered_results if result.result_status != ResultStatus.finished.value)
        win_rate = round(first / total_races, 4) if total_races else 0.0
        place_rate = round((first + second + third) / total_races, 4) if total_races else 0.0

        streak = 0
        for result in ordered_results:
            if result.result_status == ResultStatus.finished.value and result.finish_position == 1:
                streak += 1
            else:
                break

        return {
            "filters": PlayerStatisticsFiltersRead(
                track_id=track_id,
                date_from=date_from,
                date_to=date_to,
                last_n=last_n,
                grade=grade,
            ),
            "statistics": {
                "total_races": total_races,
                "finished_count": len(finished_results),
                "first_place_count": first,
                "second_place_count": second,
                "third_place_count": third,
                "win_rate": win_rate,
                "place_rate": place_rate,
                "dnf_count": dnf,
                "current_streak": streak,
                "recent_five_results": ordered_results[:5],
            },
        }

    def get_player_race_history(self, db: Session, player_id: int):
        player = self.player_repository.get_by_id(db, player_id)
        if player is None:
            raise LookupError("player not found")
        results = self.repository.list_by_player(db, player_id)
        return player, results

    def _recalculate_race_status(self, db: Session, race_id: int) -> None:
        race = self.race_repository.get_by_id(db, race_id)
        if race is None:
            return
        total_entries = len(self.entry_repository.list_by_race(db, race_id))
        total_results = len(self.repository.list_by_race(db, race_id))
        if total_results == 0:
            race.status = RaceStatus.scheduled.value
        elif total_results < total_entries:
            race.status = "in_progress"
        else:
            race.status = "completed"
        db.flush()
