from unittest import mock
import pytest

from server import GameStatsService, LobbyConnection
from server.abc.base_game import BaseGame
from server.games import Game
from server.gameconnection import GameConnection, GameConnectionState
from server.players import Player, PlayerState
from tests import CoroMock

@pytest.fixture()
def lobbythread():
    return mock.Mock(
        sendJSON=lambda obj: None
    )


@pytest.fixture
def game_connection(request, game, loop, player_service, players, game_service, transport):
    from server import GameConnection, LobbyConnection
    conn = GameConnection(loop=loop,
                          lobby_connection=mock.create_autospec(LobbyConnection(loop)),
                          player_service=player_service,
                          game_service=game_service,
                          player=players.hosting,
                          game=game)
    conn._transport = transport
    conn.lobby = mock.Mock(spec=LobbyConnection)

    def fin():
        conn.abort()

    request.addfinalizer(fin)
    return conn


@pytest.fixture
def mock_game_connection(state=GameConnectionState.INITIALIZING, player=None):
    gc = mock.create_autospec(spec=GameConnection)
    gc.state = state
    gc.player = player
    return gc


@pytest.fixture()
def game_stats_service():
    service = mock.Mock(spec=GameStatsService)
    service.process_game_stats = CoroMock()
    return service


@pytest.fixture
def connections(loop, player_service, game_service, transport, game):
    from server import GameConnection

    def make_connection(player):
        lc = LobbyConnection(loop)
        lc.protocol = mock.Mock()
        conn = GameConnection(loop=loop,
                              lobby_connection=lc,
                              player_service=player_service,
                              game_service=game_service,
                              player=player,
                              game=game)
        conn._transport = transport
        return conn

    return mock.Mock(
        make_connection=make_connection
    )

def add_connected_player(game: Game, player):
    game.game_service.player_service[player.id] = player
    gc = mock_game_connection(state=GameConnectionState.CONNECTED_TO_HOST, player=player)
    game.set_player_option(player.id, 'Army', 0)
    game.set_player_option(player.id, 'StartSpot', 0)
    game.set_player_option(player.id, 'Team', 0)
    game.set_player_option(player.id, 'Faction', 0)
    game.set_player_option(player.id, 'Color', 0)
    game.add_game_connection(gc)


def add_connected_players(game: Game, players):
    """
    Utility to add players with army and StartSpot indexed by a list
    """
    for army, player in enumerate(players):
        add_connected_player(game, player)
        game.set_player_option(player.id, 'Army', army)
        game.set_player_option(player.id, 'StartSpot', army)
        game.set_player_option(player.id, 'Team', army)
        game.set_player_option(player.id, 'Faction', 0)
        game.set_player_option(player.id, 'Color', 0)
    game.host = players[0]


def add_players(gameobj: Game, n: int, team: int=None):
    game = gameobj
    current = len(game.players)
    players = []
    for i in range(current, current+n):
        players.append(Player(id=i+1, login='Player '+str(i+1), global_rating=(1500, 500), state=PlayerState.JOINING))

    add_connected_players(game, players)

    if team is not None:
        for p in players:
            game.set_player_option(p.id, 'Team', team)

    return players
