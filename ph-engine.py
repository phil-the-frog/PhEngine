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
            goThread = threading.Thread(target=iGo,name='Thread-1',args=(uciIn[3:],)).start()
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
    board.turn = chess.BLACK
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
# go through the board and check to see if that square as a moveTable entry if it doesn't generate one for it
# the moveTable is like this square -> list of moves possible for that piece on that square
    
#def generateMoves(piece):

# ignoring inStr right now
def iGo():
    startTime = datetime.now()
# go through the board and check to see if that square as a moveTable entry if it doesn't generate one for it
# the moveTable is like this square -> list of moves possible for that piece on that square
    moves = list(board.generate_legal_moves())
    total = len(moves)
    i = 0
    global threadFlag
    while not threadFlag:
        bestMove = moves[random.randint(0,total-1)].uci()
        print('info depth {} score cp {} time {}'.format(i,evalFunction(),datetime.now()-startTime))
        i += 1
    threadFlag = False      # reset the thread flag
    print ('bestmove {}'.format(bestMove))  # print out the best move
        
def stopThread():
    global threadFlag
    global goThread
    threadFlag = True
    goThread.join()


def evalFunction(board):
    scoreForKings = 200 * (board.pieces(chess.KING,chess.BLACK).__len__() - board.pieces(chess.KING,chess.WHITE).__len__())
    scoreForQueens = 9 * (board.pieces(chess.QUEEN,chess.BLACK).__len__() - board.pieces(chess.QUEEN,chess.WHITE).__len__())
    scoreForRook = 5 * (board.pieces(chess.ROOK,chess.BLACK).__len__() - board.pieces(chess.ROOK,chess.WHITE).__len__())
    return scoreForKings + scoreForQueens + scoreForRook
    # not done yet

def iPrint():
    print(board)

if __name__ == "__main__":
    main()