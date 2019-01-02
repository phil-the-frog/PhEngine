import chess
import random
import threading
from datetime import datetime


board = chess.Board()
author = 'Phillip Sopt'
engineName = 'PhEngine'
goThread = threading.Thread(None,iGo,'Thread-1')
moveTable = dict()
threadFlag = False
bestMove = ''

def main():
    while True:
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
            goThread = threading.Thread(None,iGo,'Thread-1',(uciIn[3:]))
        elif uciIn == 'stop':
            global threadFlag
            threadFlag = True
            goThread.join()
        

    




def iUci():
    print('id name {}'.format(engineName))
    print('id author {}'.format(author))
    print('uciok')

def iSetOption(inStr):
    #set the option
    pass

def iIsReady():
    chess.WHITE = False
    chess.BLACK = True
    print('readyok')

def iNewGame():
    moveTable.clear()

def iPosition(inStr):
    if inStr.startswith('startpos'):
        board.set_fen(chess.STARTING_FEN)
        #do a while loop till there's no more input
        if 'moves' in inStr:
            inStr = inStr.partition('moves ')[2]    # get the stuff after 'moves '
            while inStr is not None:
                board.push_uci(inStr)

    elif inStr.startswith('fen'):
        board.set_fen(inStr.partition('fen ')[2])  # use the fen string at the end to build a new board
    
def generateMoves(piece):

# ignoring inStr right now
def iGo(inStr):
    startTime = datetime.now()
    for square in range(64):
        if board.piece_at(square) not None and board.piece_at(square).color == chess.BLACK:
# go through the board and check to see if that square as a moveTable entry if it doesn't generate one for it
# the moveTable is like this square -> list of moves possible for that piece on that square

    i = 0
    global threadFlag
    while not threadFlag:
        moves
        bestMove = moves[random.randint(0,total-1)].uci()
        print('info depth {} score cp {} time {}'.format(i,evalFunction(),datetime.now()-startTime))
        i += 1
    threadFlag = False      # reset the thread flag
    print ('bestmove {}'.format(bestMove))  # print out the best move
        

def evalFunction():
    scoreForKings = 200 * (board.pieces(chess.KING,chess.BLACK).__len__() - board.pieces(chess.KING,chess.WHITE).__len__())
    scoreForQueens = 9 * (board.pieces(chess.QUEEN,chess.BLACK).__len__() - board.pieces(chess.QUEEN,chess.WHITE).__len__())
    scoreForRook = 5 * (board.pieces(chess.ROOK,chess.BLACK).__len__() - board.pieces(chess.ROOK,chess.WHITE).__len__())
    return scoreForKings + scoreForQueens + scoreForRook
    # not done yet

if __name__ == "__main__":
    main()