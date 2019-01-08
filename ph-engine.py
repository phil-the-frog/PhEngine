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

zorbistSqaures = [None]*64    # 64 dicts, each square will have a dict where the keys are the pieces and the values are the random gen vals
zorbistIsBlack = None         # one number if it's blacks turn
zorbistCastling = [None]*4    # 4 nums, 2 for each color, and 2 for kings/queens side
zorbistEnPassant = [None]*8   # 8 nums, one for each file where a valid en passant is possible

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
            #goThread = threading.Thread(target=iGo,name='Thread-1',args=(uciIn,))   # set up the go thread and let it run
            #goThread.start()
            iGo('movetime 60000')
        elif uciIn == 'stop':
            stopThread()
        elif uciIn == 'quit':
            stopThread()
            exit()
        elif uciIn == 'print':
            iPrint()
        
# prints the author and name of the engine to the GUI
def iUci():
    print('id name {}'.format(engineName))
    print('id author {}'.format(author))
    print('uciok')

def iSetOption(inStr):
    #set the option
    pass

def iIsReady():
    global zorbistSqaures 
    global zorbistIsBlack 
    global zorbistCastling 
    global zorbistEnPassant 
    random.seed(2530395)    # random seed from random.org

    #generate the random num for the squares
    symbols = ['p', 'n', 'b', 'r', 'q', 'k', 'P', 'N', 'B', 'R', 'Q', 'K']
    for square in chess.SQUARES:
        zorbistSqaures[square] = dict()
        for sym in symbols:
            zorbistSqaures[square][sym] = random.randint(0,9223372036854775807)
    
    #generate the random num for if blacks turn
    zorbistIsBlack = random.randint(0,9223372036854775807)

    #generate the random num for casting and en passant
    for i in range(4):
        zorbistCastling[i] = random.randint(0,9223372036854775807)
    for i in range(8):
        zorbistEnPassant[i] = random.randint(0,9223372036854775807)
    print('readyok')


def iNewGame():
    # erase the hash table if you like
    pass

def iPosition(inStr):
    global board
    board = chess.Board()
    if inStr.startswith('startpos'):    # if we have to start with the std chess startpos
        board.set_fen(chess.STARTING_FEN)
        #do a while loop till there's no more input
        if 'moves' in inStr:
            inStr = inStr.partition('moves ')[2]    # get the stuff after 'moves '
            inStr = inStr.split()                   # turn it into a list and iterate through
            for move in inStr:
                board.push_uci(move)                # push the move to the board's move stack
    elif inStr.startswith('fen'):
        board.set_fen(inStr.partition('fen ')[2])   # use the fen string at the end to build a new board
    
class OldMove:
    bestMove = ''
    depth = 0
    evalu = 0

    def __init__(self, bestMove, depth, evalu):
        self.bestMove = bestMove
        self.depth = depth
        self.evalu = evalu

startTime = 0
nodes = 0
def negaMax(maxDepth, depth, alpha, beta, pv, maximizing, time):
    global board
    global startTime
    global nodes
    global threadFlag
    myBestMove = ''                                 # isn't used anymore
    timePast = (datetime.now()-startTime).seconds   # the time that past in sec
    if timePast > time: threadFlag = True           # if we are overtime, set flag to exit
    if depth >= maxDepth or threadFlag: 
        return evalFunction(board) if maximizing else -evalFunction(board)  # use negative for opponent, we are trying to minimize them

    for move in board.legal_moves:          # now go through all our moves
        nodes += 1
        board.push(move)                    # update the board with that move
        zorbKey = boardToZorbistKey(board)
        if zorbKey in moveTable:            # if the moves has been seen before then use that old eval to help you
            oldResults = moveTable[zorbKey]
            if oldResults.depth >= depth:   # if the oldresult is deep enough use it
                if maximizing and oldResults.evalu >= alpha:        # old result's eval needs to be better then the current one
                    score = oldResults.evalu
                elif not maximizing and oldResults.evalu <= beta:
                    score = oldResults.evalu
                else:
                    score = negaMax(maxDepth, depth+1, alpha, beta, pv+' '+move.uci(), not maximizing, time)
            else:
                score = negaMax(maxDepth, depth+1, alpha, beta, pv+' '+move.uci(), not maximizing, time)
        else:
            score = negaMax(maxDepth, depth+1, alpha, beta, pv+' '+move.uci(), not maximizing, time)

        # if you havent seen it before then add it to the table
        board.pop()
        if maximizing:          
            if score >= beta:       # beta cutoff, the score we processed is better then the sub tree's lowest score
                                    # (recall beta was set to 9999999 at the start)
                return beta         # so bail, this tree is a lost cause
            if score > alpha:       # here the score is better then the best score in this tree
                alpha = score       # so update the bestMove
                myBestMove = move.uci()
                moveTable[zorbKey] = OldMove(move.uci(), depth, score)  # update the moveTable too
        elif not maximizing:
            if score <= alpha:      # alpha cutoff, the score we got is REALLY GOOD, we want the opponent to lose remember?
                return alpha        # (recall alpha was set to -999999 at the start)
            if score < beta:        # we got a worse score, great use it instead
                beta = score
                myBestMove = move.uci()
                moveTable[zorbKey] = OldMove(move.uci(), depth, score)
    print('info time {} nodes {} depth {} score cp {} pv {}'.format(datetime.now() - startTime,nodes,depth,alpha,pv))
    return alpha if maximizing else beta

def boardToZorbistKey(mBoard):
    global zorbistSqaures 
    global zorbistIsBlack 
    global zorbistCastling 
    global zorbistEnPassant 

    result = 0
    for square,piece in mBoard.piece_map().items():
        symb = piece.symbol()
        result = result ^ zorbistSqaures[square][symb]
    
    result = result ^ zorbistIsBlack if mBoard.turn == False else result
    # lets forget about castling and enPassant for now
    return result


# inStr is the parameters that the gui sends to go like 'movetime' 'depth' ...
def iGo(inStr):
    time = 999999                   # default time to search
    depth = 2                       # default depth is 2 for now
    inStr = inStr.split(' ')        # get the depth if the gui passed it in
    if 'depth' in inStr:
        depth = int(inStr[inStr.index('depth')+1])
    if 'movetime' in inStr:         # get the movetime if the gui passed it in
        time = int(inStr[inStr.index('movetime')+1]) / 1000
    global startTime
    global bestMove
    global nodes
    global threadFlag
    startTime = datetime.now()  # set the startTime here, then the min and max function can display time passed

    nodes = 0           # nodes processed throught the search
    val = -999999       # the max score for a root move
    newVal = 0          # score of the current root move

    # while the stop signal isn't recieved
    while (not threadFlag):
        # do iterative deepening on the root moves to fill up the movesTable
        for move in board.legal_moves:
            zorbKey = boardToZorbistKey(board)
            if zorbKey in moveTable:            # if the moves has been seen before then use that old eval to help you
                oldResults = moveTable[zorbKey]
                if oldResults.depth >= depth:   # make sure the old result's depth is deeper then the current depth
                    newVal = oldResults.evalu
                else:   # if the oldResults aren't deep enough, reprocess that sub tree
                    newVal = negaMax(depth, 0, -99999, 99999, '', False, time)  # use False because this fuction is maximising the ai
            else:
                newVal = negaMax(depth, 0, -99999, 99999, '', False, time)
            # if a better move was found set bestMove to that
            if newVal >= val:
                bestMove = move.uci()
                val = newVal
            print('info nodes {} currmove {} depth {}'.format(nodes, move.uci(), depth))
        depth += 1
    ''' old code
    for move in board.legal_moves:
        if threadFlag == True: break    # if the GUI wants the engine to stop then break out this loop
        print('info nodes {} currmove {} currmovenumber {}'.format(nodes, move.uci(),i))
        board.push(move)
        newVal = negaMax(depth, 1, -99999, 99999, move.uci(), False)
        board.pop()
        if val <= newVal:
            bestMove = move.uci()
            val = newVal
        i+=1
    '''
    threadFlag = False
    print('info time {}'.format(datetime.now()-startTime))  # print the time it took
    print ('bestmove {}'.format(bestMove))  # finally print out the best move
        
# stop the go thread
def stopThread():
    global threadFlag
    threadFlag = True
    global goThread
    goThread.join()

#position evaluation boards for each piece
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

def evalFunction(mBoard):
    color = mBoard.turn
    # material evaluation, might be really slow try to optimize
    scoreForKings = 20000 * (mBoard.pieces(chess.KING,color).__len__() - mBoard.pieces(chess.KING,not color).__len__())
    scoreForQueens = 900* (mBoard.pieces(chess.QUEEN,color).__len__() - mBoard.pieces(chess.QUEEN,not color).__len__())
    scoreForRook = 500 * (mBoard.pieces(chess.ROOK,color).__len__() - mBoard.pieces(chess.ROOK,not color).__len__())
    scoreForBishopKnight = (mBoard.pieces(chess.BISHOP,color).__len__()-mBoard.pieces(chess.BISHOP,not color).__len__())
    scoreForBishopKnight += (mBoard.pieces(chess.KNIGHT,color).__len__()-mBoard.pieces(chess.KNIGHT,not color).__len__())
    scoreForBishopKnight *= 330
    scoreForPawn = 100 * (mBoard.pieces(chess.PAWN,color).__len__() - mBoard.pieces(chess.PAWN,not color).__len__())

    # position evaluation
    pieceMap = mBoard.piece_map()
    for square,piece in pieceMap.items():
        if piece is not None and piece.color == color:
            if color == chess.WHITE:
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
    # Mobility evaluation
    scoreMobility = mBoard.legal_moves.count()  # my num of legal moves
    mBoard.push(chess.Move.null())              # push a null move to change to the other side
    scoreMobility -= mBoard.legal_moves.count() # -opponents num of legal moves
    scoreMobility *= 0.1
    mBoard.pop()    # pop the null move

    return scoreForKings + scoreForQueens + scoreForRook + scoreForBishopKnight + scoreForPawn + scoreMobility

def iPrint():
    print(board)

if __name__ == "__main__":
    main()