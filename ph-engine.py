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
from operator import itemgetter

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
            goThread = threading.Thread(target=iGo,name='Thread-1',args=(uciIn,))
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
    #goThread = threading.Thread(target=iGo, name='Thread-1')    # the thread on which the 'go' command will run
    print('readyok')

def iNewGame():
    moveTable.clear()

def iPosition(inStr):
    global color
    global board
    board = chess.Board()
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
    
startTime = 0
nodes = 0
def maxi(currDepth,depth, alpha, beta):
    global board
    global startTime
    global nodes
    if currDepth >= depth or threadFlag == True: return evalFunction()
    for move in list(board.generate_legal_moves()):
        nodes += 1
        print('info depth {} nodes {} score cp {} time {}'.format(currDepth,nodes,evalFunction(),datetime.now()-startTime))
        board.push(move)
        score = mini(currDepth+1,depth, alpha, beta)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def mini(currDepth, depth, alpha, beta):
    global board
    global startTime
    global nodes
    if currDepth >= depth or threadFlag == True: return -evalFunction()
    for move in list(board.generate_legal_moves()):
        nodes += 1
        board.push(move)
        #print('info depth {} nodes {} score cp {} time {} color {}'.format(depth,nodes,evalFunction(board),datetime.now()-startTime,board.turn))
        score = maxi(currDepth+1,depth, alpha, beta)
        board.pop()
        if score <= alpha:
            return alpha
        if score < beta:
            beta = score
    return beta

# ignoring inStr right now
def iGo(inStr):
    depth = 3
    inStr = inStr.split(' ')        # get the depth if the gui passed it in
    if 'depth' in inStr:
        depth = int(inStr[inStr.index('depth')+1])
    global startTime
    global threadFlag
    global bestMove
    global nodes
    startTime = datetime.now()
    # go through the board and check to see if that square as a moveTable entry if it doesn't generate one for it
    # the moveTable is like this square -> list of moves possible for that piece on that square
    nodes = 0
    #iPrint()
    rootList = []
    for move in list(board.generate_legal_moves()):
        rootList.append((move,maxi(0,depth-1,-9999999,9999999)))
    bestMove = max(rootList,key=itemgetter(1))[0].uci()
    #iPrint()
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

def evalFunction():
    global color
    global board
    scoreForKings = 20000 * (board.pieces(chess.KING,color).__len__() - board.pieces(chess.KING,not color).__len__())
    scoreForQueens = 900* (board.pieces(chess.QUEEN,color).__len__() - board.pieces(chess.QUEEN,not color).__len__())
    scoreForRook = 500 * (board.pieces(chess.ROOK,color).__len__() - board.pieces(chess.ROOK,not color).__len__())
    scoreForBishopKnight = (board.pieces(chess.BISHOP,color).__len__()-board.pieces(chess.BISHOP,not color).__len__())
    scoreForBishopKnight += (board.pieces(chess.KNIGHT,color).__len__()-board.pieces(chess.KNIGHT,not color).__len__())
    scoreForBishopKnight *= 330
    scoreForPawn = 100 * (board.pieces(chess.PAWN,color).__len__() - board.pieces(chess.PAWN,not color).__len__())
    pieceMap = board.piece_map()
    for square,piece in pieceMap.items():
        if piece.color == color:
            if color == chess.BLACK:
                mfile = chess.square_file(square)
                mrank = chess.square_rank(square)
                mrank = 7 - mrank
                reversedSquare = chess.square(mfile,mrank)
                if piece.piece_type == chess.PAWN:
                    scoreForPawn += pawnTable[reversedSquare]
                elif piece.piece_type == chess.KNIGHT:
                    scoreForBishopKnight += knightTable[reversedSquare]
                elif piece.piece_type == chess.BISHOP:
                    scoreForBishopKnight += bishopTable[reversedSquare]
                elif piece.piece_type == chess.ROOK:
                    scoreForRook += rookTable[reversedSquare]
                elif piece.piece_type == chess.QUEEN:
                    scoreForQueens += queenTable[reversedSquare]
                elif piece.piece_type == chess.KING:
                    scoreForKings += kingTable[reversedSquare]
            else:
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

def iPrint():
    print(board)

if __name__ == "__main__":
    main()