from __future__ import annotations

from datetime import date, time, timedelta
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_engine, session_scope
from app.models.entries import Entry
from app.models.players import Player
from app.models.races import Race
from app.models.tracks import Track


def seed() -> None:
    engine = get_engine(f"sqlite:///{backend_root / 'kip.db'}")
    Base.metadata.create_all(bind=engine)

    with session_scope(f"sqlite:///{backend_root / 'kip.db'}") as db:
        if db.query(Track).count() == 0:
            tracks = [
                Track(code="SEOUL", name="Seoul Velodrome", region="Seoul", address="Seoul", status="active"),
                Track(code="BUSAN", name="Busan Velodrome", region="Busan", address="Busan", status="active"),
                Track(code="DAEGU", name="Daegu Velodrome", region="Daegu", address="Daegu", status="active"),
            ]
            db.add_all(tracks)
            db.flush()

        if db.query(Player).count() == 0:
            players = []
            for index in range(1, 11):
                players.append(
                    Player(
                        name=f"Player {index}",
                        player_number=1000 + index,
                        grade="A1" if index <= 3 else "B1",
                        region="Seoul" if index % 2 == 0 else "Busan",
                        status="active",
                    )
                )
            db.add_all(players)
            db.flush()

        if db.query(Race).count() == 0:
            track_map = {track.code: track.id for track in db.query(Track).all()}
            race_specs = [
                (date.today(), "SEOUL", 1, time(9, 0)),
                (date.today(), "BUSAN", 2, time(11, 0)),
                (date.today() + timedelta(days=1), "SEOUL", 3, time(14, 0)),
            ]
            races = []
            for race_date, track_code, race_number, start_time in race_specs:
                races.append(
                    Race(
                        race_date=race_date,
                        track_id=track_map[track_code],
                        race_number=race_number,
                        scheduled_start_time=start_time,
                        status="scheduled",
                    )
                )
            db.add_all(races)
            db.flush()

            players = db.query(Player).order_by(Player.player_number.asc()).all()
            entries = []
            for race_index, race in enumerate(races, start=0):
                for offset, player in enumerate(players[race_index : race_index + 5], start=1):
                    entries.append(
                        Entry(
                            race_id=race.id,
                            player_id=player.id,
                            entry_number=offset,
                            lane_number=offset,
                            lineup_position=offset,
                            status="confirmed",
                        )
                    )
            db.add_all(entries)


if __name__ == "__main__":
    seed()
    print("Sample data seeded successfully.")
