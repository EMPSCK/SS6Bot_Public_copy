import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from abc import ABC, abstractmethod


class Color(str, Enum):
    white = 'white'
    black = 'black'


class Error(str, Enum):
    INVALID_MOVE = "The piece cannot make the specified move."
    WRONG_INPUT = 'Wrong input format.'


@dataclass
class Position:
    x: int
    y: int

    @classmethod
    def fromStr(cls, position: str):
        x, y = position
        # 97 - ASCII номер для 'a'
        return cls(ord(x) - 96, int(y))

    def __str__(self):
        return f'{chr(self.x + 96)}{self.y}'

    def __sub__(self, other: 'Position') -> 'Position':
        return Position(x=self.x - other.x, y=self.y - other.y)

    def __abs__(self):
        return Position(x=abs(self.x), y=abs(self.y))

    def __eq__(self, other: 'Position'):
        return (other.x == self.x) and (other.y == self.y)


@dataclass
class Result:
    is_success: bool
    data: Optional[str] = None
    error_message: Optional[Error] = None


class Board:
    def __init__(self):
        self._setup_default_board()

    def _setup_default_board(self) -> List[List['Piece']]:
        self._board = [[None for _ in range(8)] for _ in range(8)]

        self._board[0] = [
            Rook(Color.white),
            Knight(Color.white),
            Bishop(Color.white),
            Queen(Color.white),
            King(Color.white),
            Bishop(Color.white),
            Knight(Color.white),
            Rook(Color.white),
        ]

        self._board[-1] = [
            Rook(Color.black),
            Knight(Color.black),
            Bishop(Color.black),
            Queen(Color.black),
            King(Color.black),
            Bishop(Color.black),
            Knight(Color.black),
            Rook(Color.black),
        ]

        self._board[-2] = [Pawn(Color.black) for _ in range(8)]
        self._board[1] = [Pawn(Color.white) for _ in range(8)]

    def num_white_pieces(self) -> int:
        # Считаю сумму вхождений белых фигур в выпрямленную доску
        return sum(map(lambda piece: piece is not None and piece.color == Color.white, sum(self._board)))

    def num_black_pieces(self) -> int:
        # Считаю сумму вхождений черных фигур в выпрямленную доску
        return sum(map(lambda piece: piece is not None and piece.color == Color.black, sum(self._board)))

    def balance(self) -> None:
        # вообще объект доски не должен иметь реализацию баланса
        # это зона ответственности самой игры
        # поэтому реализовал ее в GameState
        ...

    def __getitem__(self, pos: Position):
        return self._board[pos.y - 1][pos.x - 1]

    def __setitem__(self, pos: Position, piece: Optional['Piece']):
        self._board[pos.y - 1][pos.x - 1] = piece

    # TODO item: Piece
    def __contains__(self, item: Position):
        return self[item] is not None

    def __str__(self):
        s = "\n   A B C D E F G H\n\n"

        for row_i in range(7, -1, -1):
            s += str(row_i + 1) + "  "

            for row_j in range(8):
                s += str(self._board[row_i][row_j] or '.') + ' '

            s += f" {row_i + 1}\n"
        s += "\n   A B C D E F G H\n"
        return s


# PIECES -------------

class Piece(ABC):
    _color: Color
    _symbol: str

    __slots__ = ('_color', '_symbol',)

    def __init__(self, color: Color):
        self._color = color

    @property
    def color(self):
        return self._color

    def __str__(self) -> str:
        return (self._symbol.upper()
                if self._color == Color.white
                else self._symbol)

    @abstractmethod
    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        ...

    def check_obstacles(self, pos: Position, new_pos: Position, board: Board) -> bool:
        """Проверка преград на пути"""

        # прямой, а не по диагонали
        is_direct = pos.x == new_pos.x or pos.y == new_pos.y

        if is_direct:
            return self._check_direct(pos, new_pos, board)

        else:
            return self._check_diagonal(pos, new_pos, board)

    @staticmethod
    def _check_direct(pos: Position, new_pos: Position, board: Board) -> bool:
        # Вертикальное движение
        if pos.x == new_pos.x:
            y_range = (range(pos.y + 1, new_pos.y)
                       if pos.y < new_pos.y
                       else range(pos.y - 1, new_pos.y, -1))

            return all(board[Position(pos.x, y)] is None for y in y_range)

        # Горизонтальное движение
        else:
            x_range = (range(pos.x + 1, new_pos.x)
                       if pos.x < new_pos.x
                       else range(pos.x - 1, new_pos.x, -1))
            return all(board[Position(x, pos.y)] is None for x in x_range)

    @staticmethod
    def _check_diagonal(pos: Position, new_pos: Position, board: Board) -> bool:
        x_step = 1 if new_pos.x > pos.x else -1
        y_step = 1 if new_pos.y > pos.y else -1

        current_x, current_y = pos.x + x_step, pos.y + y_step

        while current_x != new_pos.x and current_y != new_pos.y:

            if board[Position(current_x, current_y)] is not None:
                return False

            current_x += x_step
            current_y += y_step

        return True


class Bishop(Piece):
    """Слон"""

    _symbol = 'b'

    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        vector: Position = abs(pos - new_pos)

        return vector.x == vector.y


class King(Piece):
    """Король"""

    _symbol = 'k'

    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        vector: Position = abs(pos - new_pos)

        return vector.x <= 1 and vector.y <= 1


class Knight(Piece):
    """Конь"""

    _symbol = 'n'

    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        vector: Position = abs(pos - new_pos)

        return (vector.x == 1 and vector.y == 2) or (vector.x == 2 and vector.y == 1)

    # Для коня всегда True
    def check_obstacles(self, pos: Position, new_pos: Position, board: Board) -> bool:
        return True


class Pawn(Piece):
    """Пешка"""

    _symbol = 'p'

    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        # Получение цвета пешки
        is_white = self.color == Color.white

        # Рассчитываем направление движения: для белых - вверх, для черных - вниз
        direction = 1 if is_white else -1

        # Пешка может двигаться на одну клетку вперед
        if new_pos == Position(pos.x, pos.y + direction):
            # Проверяем, что на новой позиции нет другой фигуры (или она пустая)
            return board[new_pos] is None

        # Пешка может двигаться на две клетки вперед с начальной позиции
        elif pos.y == (2 if is_white else 7) and new_pos == Position(pos.x, pos.y + 2 * direction):
            # Проверяем, что обе клетки впереди (первая и вторая) пустые
            return (board[Position(pos.x, pos.y + direction)] is None and
                    board[new_pos] is None)

        # Пешка может бить по диагонали
        elif new_pos == Position(pos.x - 1, pos.y + direction) or new_pos == Position(pos.x + 1, pos.y + direction):
            # Проверяем, что там есть вражеская фигура
            return board[new_pos] is not None and board[new_pos].color != self.color

        # Если ни одно из условий не выполнено, ход не допустим
        return False


class Queen(Piece):
    """Королева"""

    _symbol = 'q'

    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        vector: Position = abs(pos - new_pos)

        return (vector.x == vector.y) or vector.x == 0 or vector.y == 0


class Rook(Piece):
    """Ладья"""

    _symbol = 'r'

    def verify_move(self, pos: Position, new_pos: Position, board: Board) -> bool:
        vector: Position = abs(pos - new_pos)

        return vector.x == 0 or vector.y == 0


# GAME ---------------

class GameState:
    move: Color = Color.white  # начинают белые
    count: int = 1
    white_balance: int = 0
    black_balance: int = 0

    _piece_score = {
        Pawn: 1,
        Knight: 3,
        Bishop: 3,
        Rook: 5,
        Queen: 7
    }

    # его нужно было бы менять если бы произошел шах и мат, но по условию это не нужно
    is_end = False

    def next(self):
        self.move = Color.black \
            if self.move == Color.white \
            else Color.white

        if self.move == Color.white:
            self.count += 1

    def kill(self, piece: Piece):
        score = self._piece_score[type(piece)]

        if piece.color == Color.white:
            self.black_balance += score
            self.white_balance -= score

        else:
            self.white_balance += score
            self.black_balance -= score


class ChessGame:
    _move_pattern = re.compile(r'^[a-h][1-8]-[a-h][1-8]$')
    _balance_pattern = re.compile(r'^balance (white|black)$')

    def __init__(self):
        self._board = Board()
        self._state = GameState()

    def start(self):
        while not self._state.is_end:
            expr: str = input(f'{self._state.move.value} {self._state.count}:\n')

            if expr == 'exit':
                break

            result: Result = self._handle(expr)

            if result.data is not None:
                print(result.data)

            if not result.is_success:
                print(f'Error. Type: {result.error_message.value}')

    def _handle(self, expr: str) -> Result:
        if expr == 'draw':
            return Result(is_success=True, data=str(self._board))

        elif self._is_move(expr):
            return self._move_handler(expr)

        elif self._is_get_balance(expr):
            return self._get_balance_handler(expr)

        else:
            return Result(is_success=False, error_message=Error.WRONG_INPUT)

    def _is_move(self, expr: str) -> bool:
        return bool(self._move_pattern.match(expr))

    def _move_handler(self, expr) -> Result:
        pos, new_pos = list(map(Position.fromStr, expr.split('-')))

        piece: Optional[Piece] = self._board[pos]
        second_piece: Optional[Piece] = self._board[new_pos]

        if (piece is None
                or self._is_not_your_color(piece)
                or self._is_not_possible(pos, new_pos, piece)
                or self._is_not_enemy(second_piece)):
            return Result(is_success=False, error_message=Error.INVALID_MOVE)

        if second_piece is not None:
            self._state.kill(second_piece)

        self._board[pos] = None
        self._board[new_pos] = piece
        self._state.next()
        return Result(is_success=True)

    def _is_not_your_color(self, piece: Piece) -> bool:
        # if piece.color != self._state.move:
        #     print('is not your color')

        return piece.color != self._state.move

    def _is_not_possible(self, pos: Position, new_pos: Position, piece: Piece) -> bool:
        is_not_available = not piece.verify_move(pos=pos, new_pos=new_pos, board=self._board)
        have_obstacles = not piece.check_obstacles(pos, new_pos, self._board)

        # if is_not_available:
        #     print('is_not_available')
        #
        # if have_obstacles:
        #     print('have_obstacles')

        return is_not_available or have_obstacles

    def _is_not_enemy(self, second_piece: Optional[Piece]) -> bool:
        # if second_piece is not None and self._state.move == second_piece.color:
        #     print('is not enemy')

        return second_piece is not None and self._state.move == second_piece.color

    def _is_get_balance(self, expr: str) -> bool:
        return bool(self._balance_pattern.match(expr))

    def _get_balance_handler(self, expr: str) -> Result:
        _, color = expr.split()

        return Result(
            is_success=True,
            data=(self._state.white_balance
                  if color == Color.white.value
                  else self._state.black_balance)
        )


if __name__ == '__main__':
    ChessGame().start()
