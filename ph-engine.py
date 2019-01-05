'''
Author: Phillip Sopt

Python Chess Engine using minmax and alpha-beta pruning

Description:
This is a simple chess engine that uses the Universal Chess Interface (UCI) protocol
'''
import chess
import random
import threading
from datetime import datetime

board = chess.Board()       # internal state of the board
author = 'Phillip Sopt'
engineName = 'PhEngine'
goThread = None             # the thread on which the 'go' command will run
moveTable = dict()          # a hash table to store the moves for each square to avoid recalculating the moves
threadFlag = False          # a flag to tell the thread when to stop running
bestMove = ''               # the current best move found, stored in uci format
color = False                # False for black, True for white

def main():
    global goThread
    while True:             # uci works with stdin and stdout so we'll loop for the duration of the program
                            # to recieve and send std i/o
        uciIn = input()
        if uciIn == 'uci':
            iUci()
        elif uciIn.startswith('setoption'):
            iSetOption(uciIn[10:])      # 10 to skip the 'setoption'
        elif uciIn == 'isready':
            iIsReady()
        elif uciIn == 'ucinewgame':
            iNewGame()
        elif uciIn.startswith('position'):
            iPosition(uciIn[9:])        # 9 to skip the 'position'
        elif uciIn.startswith('go'):
            goThread = threading.Thread(target=iGo,name='Thread-1',args=(uciIn[3:],))
            goThread.start()
        elif uciIn == 'stop':
            stopThread()
        elif uciIn == 'quit':
            stopThread()
            exit()
        elif uciIn == 'print':
            iPrint()
        
def iUci():
    print('id name {}'.format(engineName))
    print('id author {}'.format(author))
    print('uciok')

def iSetOption(inStr):
    #set the option
    pass

def iIsReady():
    global goThread
    global board
    goThread = threading.Thread(target=iGo, name='Thread-1')    # the thread on which the 'go' command will run
    print('readyok')

def iNewGame():
    moveTable.clear()

def iPosition(inStr):
    if inStr.startswith('startpos'):
        board.set_fen(chess.STARTING_FEN)
        #do a while loop till there's no more input
        if 'moves' in inStr:
            inStr = inStr.partition('moves ')[2]    # get the stuff after 'moves '
            inStr = inStr.split()
            for move in inStr:
                board.push_uci(move)
    elif inStr.startswith('fen'):
        board.set_fen(inStr.partition('fen ')[2])  # use the fen string at the end to build a new board
    color = board.turn
    
def maxi(depth, board):
    if depth == 0: return evalFunction(board)
    max = -9999999
    for move in list(board.generate_legal_moves()):
        board.push(move)
        score = mini( depth - 1, board)
        board.pop()
        if score > max:
            max = score
    return max

def mini(depth, board):
    if depth == 0: return -evalFunction(board)
    min = 9999999
    for move in list(board.generate_legal_moves()):
        board.push(move)
        score = maxi( depth - 1, board)
        board.pop()
        if score < min:
            min = score
    return min

# ignoring inStr right now
def iGo(inStr):
    startTime = datetime.now()
# go through the board and check to see if that square as a moveTable entry if it doesn't generate one for it
# the moveTable is like this square -> list of moves possible for that piece on that square
    i = 0
    global threadFlag
    while not threadFlag:
        print('info depth {} score cp {} time {}'.format(i,evalFunction(board,bestMove),datetime.now()-startTime))
        i += 1
    threadFlag = False      # reset the thread flag
    print ('bestmove {}'.format(bestMove))  # print out the best move
        
def stopThread():
    global threadFlag
    global goThread
    threadFlag = True
    goThread.join()

pawnTable = [0,  0,  0,  0,  0,  0,  0,  0,
50, 50, 50, 50, 50, 50, 50, 50,
10, 10, 20, 30, 30, 20, 10, 10,
5,  5, 10, 25, 25, 10,  5,  5,
0,  0,  0, 20, 20,  0,  0,  0,
5, -5,-10,  0,  0,-10, -5,  5,
5, 10, 10,-20,-20, 10, 10,  5,
0,  0,  0,  0,  0,  0,  0,  0]

knightTable = [-50,-40,-30,-30,-30,-30,-40,-50,
-40,-20,  0,  0,  0,  0,-20,-40,
-30,  0, 10, 15, 15, 10,  0,-30,
-30,  5, 15, 20, 20, 15,  5,-30,
-30,  0, 15, 20, 20, 15,  0,-30,
-30,  5, 10, 15, 15, 10,  5,-30,
-40,-20,  0,  5,  5,  0,-20,-40,
-50,-40,-30,-30,-30,-30,-40,-50]

bishopTable = [-20,-10,-10,-10,-10,-10,-10,-20,
-10,  0,  0,  0,  0,  0,  0,-10,
-10,  0,  5, 10, 10,  5,  0,-10,
-10,  5,  5, 10, 10,  5,  5,-10,
-10,  0, 10, 10, 10, 10,  0,-10,
-10, 10, 10, 10, 10, 10, 10,-10,
-10,  5,  0,  0,  0,  0,  5,-10,
-20,-10,-10,-10,-10,-10,-10,-20]

rookTable = [0,  0,  0,  0,  0,  0,  0,  0,
5, 10, 10, 10, 10, 10, 10,  5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
-5,  0,  0,  0,  0,  0,  0, -5,
0,  0,  0,  5,  5,  0,  0,  0]

queenTable = [-20,-10,-10, -5, -5,-10,-10,-20,
-10,  0,  0,  0,  0,  0,  0,-10,
-10,  0,  5,  5,  5,  5,  0,-10,
-5,  0,  5,  5,  5,  5,  0, -5,
0,  0,  5,  5,  5,  5,  0, -5,
-10,  5,  5,  5,  5,  5,  0,-10,
-10,  0,  5,  0,  0,  0,  0,-10,
-20,-10,-10, -5, -5,-10,-10,-20]

kingTable = [-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-30,-40,-40,-50,-50,-40,-40,-30,
-20,-30,-30,-40,-40,-30,-30,-20,
-10,-20,-20,-20,-20,-20,-20,-10,
20, 20,  0,  0,  0,  0, 20, 20,
20, 30, 10,  0,  0, 10, 30, 20]

kingEndGameTable = [-50,-40,-30,-20,-20,-30,-40,-50,
-30,-20,-10,  0,  0,-10,-20,-30,
-30,-10, 20, 30, 30, 20,-10,-30,
-30,-10, 30, 40, 40, 30,-10,-30,
-30,-10, 30, 40, 40, 30,-10,-30,
-30,-10, 20, 30, 30, 20,-10,-30,
-30,-30,  0,  0,  0,  0,-30,-30,
-50,-30,-30,-30,-30,-30,-30,-50]

def evalFunction(board):
    scoreForKings = 20000 * (board.pieces(chess.KING,color).__len__() - board.pieces(chess.KING,not color).__len__())
    scoreForQueens = 900* (board.pieces(chess.QUEEN,color).__len__() - board.pieces(chess.QUEEN,not color).__len__())
    scoreForRook = 500 * (board.pieces(chess.ROOK,color).__len__() - board.pieces(chess.ROOK,not color).__len__())
    scoreForBishopKnight = (board.pieces(chess.BISHOP,color).__len__()-board.pieces(chess.BISHOP,not color).__len__())
    scoreForBishopKnight += (board.pieces(chess.KNIGHT,color).__len__()-board.pieces(chess.KNIGHT,not color).__len__())
    scoreForBishopKnight *= 330
    scoreForPawn = 100 * (board.pieces(chess.PAWN,color).__len__() - board.pieces(chess.PAWN,not color).__len__())
    pieceMap = board.piece_map()
    for square in chess.SQUARES:
        piece = pieceMap[square]
        if piece not None and piece.color == color:
            if piece.piece_type == chess.PAWN:
                scoreForPawn += pawnTable[square]
            elif piece.piece_type == chess.KNIGHT:
                scoreForBishopKnight += knightTable[square]
            elif piece.piece_type == chess.BISHOP:
                scoreForBishopKnight += bishopTable[square]
            elif piece.piece_type == chess.ROOK:
                scoreForRook += rookTable[square]
            elif piece.piece_type == chess.QUEEN:
                scoreForQueens += queenTable[square]
            elif piece.piece_type == chess.KING:
                scoreForKings += kingTable[square]
    return scoreForKings + scoreForQueens + scoreForRook + scoreForBishopKnight + scoreForPawn
    # not done yet

def iPrint():
    print(board)

if __name__ == "__main__":
    main()