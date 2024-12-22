import pygame
import time
import pygame.mixer # necessary for sound
from copy import deepcopy

# initializes all pygame functions at the start (necessary for it to run)
pygame.init()
pygame.mixer.init()

# define paramaters (board is a square with a sidebar)
WIDTH = 825
HEIGHT = 625
ROWS = 8
COLS = 8
SQUARE_SIZE = 575 // COLS
BORDER_SIZE = 25
SIDEBAR_WIDTH = 200
WHITE = (255,255,255)
GREY = (128,128,128)
BLACK = (0,0,0)
BROWN = (101,55,0)
TAN = (210,180,140)
RED = (255,0,0)
BLUE = (0,0,255)
SPRITE_WIDTH = 60
SPRITE_HEIGHT = 60

screen = pygame.display.set_mode([WIDTH,HEIGHT])
pygame.display.set_caption('Chess') # sets window title

# sprites
sprite_sheet = pygame.image.load('Chess/ChessPiecesArray.png')
chess_logo = pygame.image.load('Chess/Chess.png')
white_win_logo = pygame.image.load('Chess/White.png')
black_win_logo = pygame.image.load('Chess/Black.png')
wood_bg = pygame.image.load('Chess/Wood.jpg')
wood_bg = pygame.transform.scale(wood_bg, (SIDEBAR_WIDTH, HEIGHT))
chess_logo = pygame.transform.scale(chess_logo, (400,200))
white_win_logo = pygame.transform.scale(white_win_logo, (400,200))
black_win_logo = pygame.transform.scale(black_win_logo, (400,200))

# sound effects
move_sound = pygame.mixer.Sound('Chess/move-self.mp3')
capture_sound = pygame.mixer.Sound('Chess/capture.mp3')
save_sound = pygame.mixer.Sound('Chess/save.mp3')
error_sound = pygame.mixer.Sound('Chess/error.mp3')
check_sound = pygame.mixer.Sound('Chess/mgs-alert.mp3')
victory_sound = pygame.mixer.Sound('Chess/victory-fanfare-hd.mp3')
check_sound.set_volume(0.1)
save_sound.set_volume(0.25)
error_sound.set_volume(0.25)
victory_sound.set_volume(0.25)

def get_sprite(row,col,width,height):
    sprite = pygame.Surface((width,height), pygame.SRCALPHA) # sets the transparency on pixels from no background images
    sprite.blit(sprite_sheet, (0,0), (col*width,row*height,width,height))
    return sprite

white_pieces = []
black_pieces = []

for i in range(6):
    white_sprite = get_sprite(1,i,SPRITE_WIDTH,SPRITE_HEIGHT)
    white_pieces.append(white_sprite)
    black_sprite = get_sprite(0,i,SPRITE_WIDTH,SPRITE_HEIGHT)
    black_pieces.append(black_sprite)

class ChessAI:
    def __init__(self, color, depth=3):
        self.color = color
        self.depth = depth

    def choose_move(self, board):
        best_move = None
        best_score = float('-inf') if self.color == 'white' else float('inf')
        alpha = float('-inf')
        beta = float('inf')

        for move in self.get_all_moves(board, self.color):
            new_board = self.make_hypothetical_move(board, move)
            score = self.minimax(new_board, self.depth - 1, alpha, beta, self.color != 'white')

            if self.color == 'white':
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)

            if beta <= alpha:
                break

        return best_move
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return self.evaluate_board(board)

        if maximizing_player:
            max_eval = float('-inf')
            for move in self.get_all_moves(board, 'white'):
                new_board = self.make_hypothetical_move(board, move)
                eval = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in self.get_all_moves(board, 'black'):
                new_board = self.make_hypothetical_move(board, move)
                eval = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_all_moves(self, board, color):
        moves = []
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if piece and piece.color == color:
                    for move in board.get_valid_moves(piece):
                        moves.append(((row, col), move))
        return moves

    def make_hypothetical_move(self, board, move):
        new_board = deepcopy(board)
        start, end = move
        new_board.move_piece(start, end)
        return new_board

    def evaluate_board(self, board):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if piece:
                    piece_value = PIECE_VALUES[type(piece)]
                    position_bonus = POSITION_BONUSES[type(piece)][row][col]
                    if piece.color == 'white':
                        score += piece_value + position_bonus
                    else:
                        score -= piece_value + position_bonus

        # Consider king safety
        white_king_safety = self.evaluate_king_safety(board, 'white')
        black_king_safety = self.evaluate_king_safety(board, 'black')
        score += white_king_safety - black_king_safety

        # Consider board control
        white_control = self.evaluate_board_control(board, 'white')
        black_control = self.evaluate_board_control(board, 'black')
        score += white_control - black_control

        return score

    def evaluate_king_safety(self, board, color):
        king_position = None
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if isinstance(piece, King) and piece.color == color:
                    king_position = (row, col)
                    break
            if king_position:
                break

        if not king_position:
            return 0

        safety_score = 0
        row, col = king_position

        # Check pawns in front of the king
        pawn_shield = 0
        pawn_row = row - 1 if color == 'white' else row + 1
        for c in range(max(0, col - 1), min(8, col + 2)):
            if 0 <= pawn_row < 8:
                piece = board.board[pawn_row][c]
                if isinstance(piece, Pawn) and piece.color == color:
                    pawn_shield += 1
        safety_score += pawn_shield * 10

        # Penalize open files near the king
        for c in range(max(0, col - 1), min(8, col + 2)):
            file_open = True
            for r in range(8):
                if board.board[r][c] is not None:
                    file_open = False
                    break
            if file_open:
                safety_score -= 20

        return safety_score

    def evaluate_board_control(self, board, color):
        control_score = 0
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if piece and piece.color == color:
                    control_score += len(board.get_valid_moves(piece))
        return control_score
        
class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.has_moved = False
        self.in_check = False

    def valid_moves(self, board):
        raise NotImplementedError
    
    def move(self, new_position):
        self.position = new_position
        self.has_moved = True

class Pawn(Piece):
    def valid_moves(self, board):
        row, col = self.position
        moves = []
        direction = -1 if self.color == 'white' else 1
        # move forward
        if 0 <= row + direction < 8 and board[row + direction][col] is None:
            moves.append((row + direction, col))
            # initial double move
            if (self.color == 'white' and row == 6) or (self.color == 'black' and row == 1):
                if board[row + 2*direction][col] is None:
                    moves.append((row+2*direction, col))
        
        # diagonal capture
        for dcol in [-1,1]:
            if 0 <= row + direction < 8 and 0 <= col + dcol < 8:
                if board[row+direction][col+dcol] is not None and board[row + direction][col + dcol].color != self.color:
                    moves.append((row + direction, col + dcol))

        return moves

    # queen me
    def move(self, new_position):
        super().move(new_position)
        # check is pawn has reached the opposited side
        if (self.color == 'white' and self.position[0] == 0) or (self.color == 'black' and self.position[0] == 7):
            return Queen(self.color, self.position)
        return self

class Rook(Piece):
    def valid_moves(self, board):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for direction in directions:
            for i in range(1, 8):
                row = self.position[0] + direction[0] * i
                col = self.position[1] + direction[1] * i
                if 0 <= row < 8 and 0 <= col < 8:
                    if board[row][col] is None:
                        moves.append((row, col))
                    elif board[row][col].color != self.color:
                        moves.append((row, col))
                        break
                    else:
                        break
                else:
                    break
        return moves
    
class Knight(Piece):
    def valid_moves(self, board):
        moves = [] # create a list that will serve as available moves
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)] # all possible moves for knight
        for move in knight_moves: # check to see where the move will go in relation to current position
            row = self.position[0] + move[0]
            col = self.position[1] + move[1]
            if 0 <= row < 8 and 0 <= col < 8: # if the position is on the game board
                if board[row][col] is None or board[row][col].color != self.color: # and if the position isnt already occupied by a friendly piece
                    moves.append((row, col))
        return moves
    
class Bishop(Piece):
    def valid_moves(self, board):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for direction in directions:
            for i in range(1, 8):
                row = self.position[0] + direction[0] * i
                col = self.position[1] + direction[1] * i
                if 0 <= row < 8 and 0 <= col < 8:
                    if board[row][col] is None:
                        moves.append((row, col))
                    elif board[row][col].color != self.color:
                        moves.append((row, col))
                        break
                    else:
                        break
                else:
                    break
        return moves
    
class Queen(Piece):
    def valid_moves(self, board):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for direction in directions:
            for i in range(1, 8):
                row = self.position[0] + direction[0] * i
                col = self.position[1] + direction[1] * i
                if 0 <= row < 8 and 0 <= col < 8:
                    if board[row][col] is None:
                        moves.append((row, col))
                    else: # the square is occupied
                        if board[row][col].color != self.color:
                            moves.append((row, col))
                        break # stop checking after encountering any piece
                else:
                    break # stop if were off board
        return moves

    
class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
        self.has_moved = False

    def move(self, new_position):
        self.has_moved = True
        self.position = new_position
        return self

    def valid_moves(self, board):
        moves = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        for direction in directions:
            row = self.position[0] + direction[0] 
            col = self.position[1] + direction[1]
            if 0 <= row < 8 and 0 <= col < 8:
                if board[row][col] is None or board[row][col].color != self.color:
                    moves.append((row, col))
        
        return moves

    # Castling
    def get_castling_moves(self, board):
        castling_moves = []
        if self.has_moved:
            return castling_moves
    
        row = self.position[0]
        # Kingside
        if isinstance(board[row][7], Rook) and not board[row][7].has_moved:
            if all(board[row][col] is None for col in range(5, 7)):
                castling_moves.append((row, 6))
        # Queenside
        if isinstance(board[row][0], Rook) and not board[row][0].has_moved:
            if all(board[row][col] is None for col in range(1, 4)):
                castling_moves.append((row, 2))

        return castling_moves
    
PIECE_VALUES = {
    Pawn: 100,
    Knight: 320,
    Bishop: 330,
    Rook: 500,
    Queen: 900,
    King: 20000
}
POSITION_BONUSES = {
    Pawn: [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 10, 25, 25, 10,  5,  5],
        [0,  0,  0, 20, 20,  0,  0,  0],
        [5, -5,-10,  0,  0,-10, -5,  5],
        [5, 10, 10,-20,-20, 10, 10,  5],
        [0,  0,  0,  0,  0,  0,  0,  0]
    ],
    Knight: [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50]
    ],
    Bishop: [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20]
    ],
    Rook: [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [0,  0,  0,  5,  5,  0,  0,  0]
    ],
    Queen: [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [-5,  0,  5,  5,  5,  5,  0, -5],
        [0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20]
    ],
    King: [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [20, 20,  0,  0,  0,  0, 20, 20],
        [20, 30, 10,  0,  0, 10, 30, 20]
    ]
}

class Board:
    def __init__(self):
        self.board = self.create_board()
        self.setup_pieces()

    def create_board(self):
        board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        return board

    def setup_pieces(self):
        # set up pawns
        for col in range(8):
            self.board[1][col] = Pawn('black', (1, col))
            self.board[6][col] = Pawn('white', (6, col))

        # set up the rest
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, piece_class in enumerate(piece_order):
            self.board[0][col] = piece_class('black', (0, col))
            self.board[7][col] = piece_class('white', (7, col))
        
    def move_piece(self, start, end):
        if self.is_valid_move(start, end):
            start_row, start_col = start
            end_row, end_col = end
            piece = self.board[start_row][start_col]
            captured_piece = self.board[end_row][end_col]
            new_piece = piece.move((end_row, end_col)) 
            self.board[end_row][end_col] = new_piece if new_piece else piece
            self.board[start_row][start_col] = None

            if isinstance(piece, King) and abs(start_col - end_col) == 2:
                if end_col == 6:  # Kingside castling
                    rook = self.board[start_row][7]
                    self.board[start_row][5] = rook
                    self.board[start_row][7] = None
                    rook.move((start_row, 5))
                elif end_col == 2:  # Queenside castling
                    rook = self.board[start_row][0]
                    self.board[start_row][3] = rook
                    self.board[start_row][0] = None
                    rook.move((start_row, 3))

            if isinstance(captured_piece, King):
                return True, piece.color
            return True, None
        return False, None
    
    def is_in_check(self, color):
        king_position = None
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if isinstance(piece, King) and piece.color == color:
                    king_position = (row, col)
                    break
            if king_position:
                break

        if not king_position:
            return False
        
        return self.is_square_under_attack(king_position[0], king_position[1], color)

    def is_square_under_attack(self, row, col, color):
        opponent_color = 'black' if color == 'white' else 'white'
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == opponent_color:
                    if isinstance(piece, King):
                        if abs(r-row) <= 1 and abs(c-col) <= 1:
                            return True
                    else:
                        moves = piece.valid_moves(self.board)
                        if (row, col) in moves:
                            return True
        return False

    def get_valid_moves(self, piece):
        valid_moves = []
        potential_moves = piece.valid_moves(self.board)
        if isinstance(piece, King):
            potential_moves.extend(piece.get_castling_moves(self.board))
    
        for move in potential_moves:
            if self.is_valid_move(piece.position, move):
                valid_moves.append(move)
    
        return valid_moves
    
    def is_valid_move(self, start, end):
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        if piece:
            valid_moves = piece.valid_moves(self.board)
            if isinstance(piece, King):
                valid_moves.extend(piece.get_castling_moves(self.board))
            if (end_row, end_col) in valid_moves:
                # Create a temporary board to test the move
                temp_board = [row[:] for row in self.board]
                temp_board[end_row][end_col] = piece
                temp_board[start_row][start_col] = None

                # Special handling for castling
                if isinstance(piece, King) and abs(start_col - end_col) == 2:
                    # Check if the king passes through check
                    direction = 1 if end_col > start_col else -1
                    for col in range(start_col, end_col, direction):
                        if self.is_square_under_attack(start_row, col, piece.color):
                            return False
                            
                # Check if the move puts or leaves the player in check
                temp_board_obj = Board()
                temp_board_obj.board = temp_board
                
                return not temp_board_obj.is_in_check(piece.color)
        return False

def draw_board():
    screen.fill(BROWN)
    for row in range(ROWS):
        for col in range(row % 2, COLS, 2):
            pygame.draw.rect(screen, TAN, (col * SQUARE_SIZE + BORDER_SIZE, row * SQUARE_SIZE + BORDER_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    # border
    pygame.draw.rect(screen, BLACK, (0,0,WIDTH - SIDEBAR_WIDTH,HEIGHT), BORDER_SIZE)
    font = pygame.font.Font(None,24)
    for i in range(8):
        letter = chr(65+i)
        text = font.render(letter, True, WHITE)
        screen.blit(text,(i * SQUARE_SIZE + BORDER_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2, HEIGHT - BORDER_SIZE // 2 - text.get_height() // 2))

        number = str(8-i)
        text = font.render(number, True, WHITE)
        screen.blit(text, (BORDER_SIZE // 2 - text.get_width() // 2, i * SQUARE_SIZE + BORDER_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2))

    # sidebar
    screen.blit(wood_bg, (WIDTH - SIDEBAR_WIDTH, 0))
    
def draw_pieces(chess_board):
    for row in range(ROWS):
        for col in range(COLS):
            piece = chess_board.board[row][col]
            if piece:
                if piece.color == 'white':
                    sprite = white_pieces[piece_type_to_index(type(piece))]
                else:
                    sprite = black_pieces[piece_type_to_index(type(piece))]
                screen.blit(sprite, (col * SQUARE_SIZE + BORDER_SIZE + (SQUARE_SIZE - SPRITE_WIDTH) // 2,
                                     row * SQUARE_SIZE + BORDER_SIZE + (SQUARE_SIZE - SPRITE_HEIGHT) // 2))

# creates an index so program knows what each piece is
def piece_type_to_index(piece_type):
    return {Queen: 0, King: 1, Rook: 2, Knight: 3, Bishop: 4, Pawn: 5}[piece_type]

# gets sqaure coordinate if square is valid 
def get_square_under_mouse(pos):
    x, y = pos
    row = (y - BORDER_SIZE) // SQUARE_SIZE
    col = (x - BORDER_SIZE) // SQUARE_SIZE
    return (row, col) if 0 <= row < 8 and 0 <= col < 8 else None

def draw_button(screen, text, position, size, color, text_color):
    font = pygame.font.Font(None, 36)
    button_rect = pygame.Rect(position, size)
    pygame.draw.rect(screen, color, button_rect)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    screen.blit(text_surf, text_rect)
    return button_rect

def main_menu():
    start_button = None
    time_control_button = None
    time_control = None
    ai_button = None
    ai_enabled = False
    while True:
        screen.fill(WHITE)
        screen.blit(chess_logo, ((WIDTH - chess_logo.get_width()) // 2, 50))
        start_button = draw_button(screen, "Start Game", ((WIDTH - 200) // 2, 300), (200, 50), BLACK, WHITE)
        time_control_button = draw_button(screen, "Time Control", ((WIDTH-200) // 2, 375), (200, 50), BLACK, WHITE)
        ai_button = draw_button(screen, "AI: " + ("ON" if ai_enabled else "OFF"), ((WIDTH-200) // 2, 450), (200, 50), BLACK, WHITE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, None, False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    return True, time_control, ai_enabled
                if time_control_button.collidepoint(event.pos):
                    time_control = set_time_control()
                if ai_button.collidepoint(event.pos):
                    ai_enabled = not ai_enabled

def set_time_control():
    minutes_box = pygame.Rect(100,100,140,32)
    increment_box = pygame.Rect(400,100,140,32)
    save_button = pygame.Rect(625,100,165,32)
    back_button = pygame.Rect(625, 150, 165, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color_minutes = color_inactive
    color_increment = color_inactive
    active_minutes = False
    active_increment = False
    minutes_text = ''
    increment_text = ''
    font = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if minutes_box.collidepoint(event.pos):
                    active_minutes = not active_minutes
                    active_increment = False
                elif increment_box.collidepoint(event.pos):
                    active_increment = not active_increment
                    active_minutes = False
                elif save_button.collidepoint(event.pos):
                    try:
                        minutes = int(minutes_text)
                        increment = int(increment_text)
                        if minutes >= 1 and increment >= 0:
                            save_sound.play()
                            return minutes, increment
                        else:
                            error_sound.play()
                    except ValueError:
                        pass
                elif back_button.collidepoint(event.pos):
                    return 'main_menu'
                else:
                    active_minutes = False
                    active_increment = False
                color_minutes = color_active if active_minutes else color_inactive
                color_increment = color_active if active_increment else color_inactive
            if event.type == pygame.KEYDOWN:
                if active_minutes:
                    if event.key == pygame.K_BACKSPACE:
                        minutes_text = minutes_text[:-1]
                    else:
                        minutes_text += event.unicode
                elif active_increment:
                    if event.key == pygame.K_BACKSPACE:
                        increment_text = increment_text[:-1]
                    else:
                        increment_text += event.unicode

        screen.fill((30, 30, 30))
        minutes_surface = font.render(minutes_text, True, color_minutes)
        increment_surface = font.render(increment_text, True, color_increment)
        screen.blit(minutes_surface, (minutes_box.x+5, minutes_box.y+5))
        screen.blit(increment_surface, (increment_box.x+5, increment_box.y+5))
        pygame.draw.rect(screen, color_minutes, minutes_box, 2)
        pygame.draw.rect(screen, color_increment, increment_box, 2)

        minutes_label = font.render("Minutes:", True, WHITE)
        increment_label = font.render("Increment:", True, WHITE)
        screen.blit(minutes_label, (50, 70))
        screen.blit(increment_label, (325, 70))

        save_text = font.render("Save Changes", True, BLACK)
        pygame.draw.rect(screen, WHITE, save_button)
        screen.blit(save_text, (save_button.x + 5, save_button.y + 5))

        back_text = font.render("Back", True, BLACK) 
        pygame.draw.rect(screen, WHITE, back_button) 
        back_text_rect = back_text.get_rect(center=back_button.center)
        screen.blit(back_text, back_text_rect)

        pygame.display.flip()
        clock.tick(30)


def end_game_menu(winner, move_count):
    menu_button = None
    font = pygame.font.Font(None,32)
    text = font.render('in '+str(move_count)+' moves', True, BLACK, WHITE)
    button_rect = pygame.Rect((WIDTH - 200) // 2, 225, 200, 50)
    text_rect = text.get_rect(center = button_rect.center)
    victory_sound.play()
    while True:
        screen.fill(WHITE)
        if winner == 'white':
            screen.blit(white_win_logo, ((WIDTH - white_win_logo.get_width()) // 2, 50)) 
        else:
            screen.blit(black_win_logo, ((WIDTH - black_win_logo.get_width()) // 2, 50))
        screen.blit(text, text_rect)
        menu_button = draw_button(screen, "Main Menu", ((WIDTH - 200) // 2, 300), (200, 50), BLACK, WHITE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_button.collidepoint(event.pos):
                    victory_sound.stop()
                    return True

# def print_board(board):
#         for row in board:
#             print([type(piece).__name__ if piece else None for piece in row])

def draw_sidebar(current_turn, in_check, white_time, black_time):
    forfeit_button = draw_button(screen, "Forfeit", (WIDTH-SIDEBAR_WIDTH +25, HEIGHT - 100), (150,50), BLACK, WHITE)

    font = pygame.font.Font(None, 32)
    turn_text = font.render(f"{current_turn.capitalize()}'s Turn", True, BLACK if current_turn == 'black' else WHITE)
    screen.blit(turn_text, (WIDTH - SIDEBAR_WIDTH + 35, 37))

    if in_check:
        check_text = font.render("CHECK!", True, RED)
        screen.blit(check_text, (WIDTH-SIDEBAR_WIDTH+57, 99))
    if white_time != float('inf'):
        white_minutes, white_seconds = divmod(int(white_time), 60)
        white_time_text = font.render(f"White: {white_minutes:02d}:{white_seconds:02d}", True, WHITE)
    else:
        white_time_text = font.render("White: Infinite", True, WHITE)
    if black_time != float('inf'):
        black_minutes, black_seconds = divmod(int(black_time), 60)    
        black_time_text = font.render(f"Black: {black_minutes:02d}:{black_seconds:02d}", True, BLACK)
    else:
        black_time_text = font.render("Black: Infinite", True, BLACK)

    screen.blit(white_time_text, (WIDTH - SIDEBAR_WIDTH + 30, 162))
    screen.blit(black_time_text, (WIDTH - SIDEBAR_WIDTH + 30, 225))

    return forfeit_button

def draw_thinking_indicator(screen):
    font = pygame.font.Font(None, 36)
    text = font.render("AI is thinking...", True, RED)
    text_rect = text.get_rect(center=(WIDTH - SIDEBAR_WIDTH + 105, 360))
    screen.blit(text, text_rect)
    pygame.display.flip()

# Flash red border when in check
def flash_border(duration):
    check_flash_start = time.time()
    while time.time() - check_flash_start < duration: # flash for a quarter of a sec
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        pygame.draw.rect(screen, RED, (0, 0, WIDTH - SIDEBAR_WIDTH, HEIGHT), BORDER_SIZE)
        pygame.display.update()


# constantly draws on screen until QUIT is called
def chess_game(time_control, ai_enabled):
    chess_board = Board()
    selected_piece = None
    running = True
    current_turn = 'white'
    move_count = 0
    in_check = False
    forfeit_button = None
    check_flash_start = None
    clock = pygame.time.Clock()

    # Initialize timers
    if time_control:
        minutes, increment = time_control
        white_time = black_time = minutes * 60
    else:
        white_time = black_time = float('inf')
        increment = 0
    last_move_time = time.time()

    ai = ChessAI('black') if ai_enabled else None

    while running:
        current_time = time.time()
        if white_time != float('inf') and black_time != float('inf'):
            if current_turn == 'white':
                white_time -= current_time - last_move_time
            else:
                black_time -= current_time - last_move_time
        last_move_time = current_time

        if white_time != float('inf') and white_time <= 0:
            return end_game_menu('black', move_count)
        elif black_time != float('inf') and black_time <= 0:
            return end_game_menu('white', move_count)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if forfeit_button and forfeit_button.collidepoint(event.pos):
                        winner = 'black' if current_turn == 'white' else 'white'
                        return end_game_menu(winner, move_count)

                    if current_turn == 'white' or not ai_enabled:
                        square = get_square_under_mouse(event.pos)
                        if square:
                            row, col = square
                            piece = chess_board.board[row][col]
                            if selected_piece:
                                start_row, start_col = selected_piece
                                start_piece = chess_board.board[start_row][start_col]
                                if start_piece and start_piece.color == current_turn:
                                    valid_moves = chess_board.get_valid_moves(start_piece)
                                    if (row, col) in valid_moves:
                                        end_piece = chess_board.board[row][col]
                                        move_made, winner = chess_board.move_piece(selected_piece, square)
                                        if move_made:
                                            if end_piece is not None:
                                                capture_sound.play()
                                            else:
                                                move_sound.play()
                                            if winner:
                                                move_count += 1
                                                return end_game_menu(winner, move_count)
                                            # Switch turns after a successful move
                                            if current_turn == 'white':
                                                if white_time != float('inf'):
                                                    white_time += increment
                                                current_turn = 'black'
                                            else:
                                                if black_time != float('inf'):
                                                    black_time += increment
                                                current_turn = 'white'
                                            selected_piece = None
                                            move_count += 1
                                            in_check = chess_board.is_in_check(current_turn)
                                            if in_check:
                                                flash_border(0.25)
                                                check_sound.play()
                                        else:
                                            # If the move was invalid, keep the same piece selected or deselect if clicking on empty square
                                            selected_piece = square if piece and piece.color == current_turn else None
                                    else:
                                        # If the move is not in valid_moves, deselect the piece
                                        selected_piece = None
                                else:
                                    # If it's not the current player's turn, ignore the move
                                    selected_piece = None
                            else:
                                # Select a piece only if it's the current player's turn
                                if piece and piece.color == current_turn:
                                    selected_piece = square

        draw_board()
        draw_pieces(chess_board)
        if selected_piece:
            row, col = selected_piece
            pygame.draw.rect(screen, RED if current_turn == 'white' else BLUE,  # Player 1 = red, Player 2 = blue
                             (col * SQUARE_SIZE + BORDER_SIZE, row * SQUARE_SIZE + BORDER_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
            # Highlight valid moves
            piece = chess_board.board[row][col]
            valid_moves = chess_board.get_valid_moves(piece)
            for move in valid_moves:
                move_row, move_col = move
                pygame.draw.circle(screen, GREY,
                                   (move_col * SQUARE_SIZE + BORDER_SIZE + SQUARE_SIZE // 2,
                                    move_row * SQUARE_SIZE + BORDER_SIZE + SQUARE_SIZE // 2),
                                   10)

        forfeit_button = draw_sidebar(current_turn, in_check, white_time, black_time)

        if ai_enabled and current_turn == 'black':
            draw_thinking_indicator(screen)
            ai_move = None
            for _ in range(10):
                ai_move = ai.choose_move(chess_board)
                if ai_move:
                    break
                pygame.display.flip()
                clock.tick(30)

            if ai_move:
                start, end = ai_move
                start_piece = chess_board.board[start[0]][start[1]]
                end_piece = chess_board.board[end[0]][end[1]]
                move_made, winner = chess_board.move_piece(start, end)
                if move_made:
                    if end_piece is not None:
                        capture_sound.play()
                    else:
                        move_sound.play()
                    if winner:
                        move_count += 1
                        return end_game_menu(winner, move_count)
                    if black_time != float('inf'):
                        black_time += increment
                    current_turn = 'white'
                    move_count += 1
                    in_check = chess_board.is_in_check(current_turn)
                    if in_check:
                        flash_border(0.25)
                        check_sound.play()

        pygame.display.flip()  # update contents of entire screen (display.update() can target specific areas)
        clock.tick(30)  # limit frame rate to 30


def main():
    running = True
    while running:
        start_game, time_control, ai_enabled = main_menu()
        if start_game:
            if not chess_game(time_control, ai_enabled):
                running = False
        else:
            running = False
    
    pygame.quit()

if __name__ == "__main__":
    main()