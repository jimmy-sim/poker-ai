"""Exhaustively compare own Kuhn/Leduc rules with optional OpenSpiel."""

import importlib.metadata
import json

from poker_ai.toy.games import GameName
from poker_ai.validation.toy_games import validate_game_rules


def main() -> None:
    games: tuple[GameName, ...] = ("kuhn", "leduc")
    results = {game: validate_game_rules(game) for game in games}
    print(
        json.dumps(
            {
                "open_spiel": importlib.metadata.version("open_spiel"),
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
