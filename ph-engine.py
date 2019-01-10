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
            iGo(uciIn[3:])
            #goThread = threading.Thread(target=iGo,name='Thread-1',args=(uciIn,))   # set up the go thread and let it run
            #goThread.start()
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
    random.seed(3570648568523766397)    # random 64bit prime number
    max64 = 9223372036854775807

    #generate the random num for the squares
    symbols = ['p', 'n', 'b', 'r', 'q', 'k', 'P', 'N', 'B', 'R', 'Q', 'K']
    for square in chess.SQUARES:
        zorbistSqaures[square] = dict()
        for sym in symbols:
            zorbistSqaures[square][sym] = random.randint(0,max64)
    
    #generate the random num for if blacks turn
    zorbistIsBlack = random.randint(0,max64)

    #generate the random num for casting and en passant
    for i in range(4):
        zorbistCastling[i] = random.randint(0,max64)
    for i in range(8):
        zorbistEnPassant[i] = random.randint(0,max64)
    print('readyok')


def iNewGame():
    # erase the hash table if you like
    pass

def iPosition(inStr):
    global board
    board.clear()
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
    
# this is the structure that we are going to use to store our past moves in the moveTable
class OldMove:
    bestMove = ''   # uci of the move
    depth = 0       # how deep did we find it
    evalu = 0       # what was it's evaluation

    def __init__(self, bestMove, depth, evalu): # constructor
        self.bestMove = bestMove
        self.depth = depth
        self.evalu = evalu

time = 0
startTime = 0
nodes = 0
def maxi(maxDepth, depth, alpha, beta):
    global moveTable
    global board
    global startTime
    global threadFlag
    global nodes
    global time
    timePast = (datetime.now()-startTime).seconds   # the time that past in sec
    if timePast > time: threadFlag = True           # if we are overtime, set flag to exit
    if depth >= maxDepth or threadFlag: return evalFunction(board)
    for move in board.legal_moves:          # now go through all our moves
        nodes += 1
        board.push(move)                    # update the board with that move
        zorbKey = boardToZorbistKey(board)
        try:
            with moveTable[zorbKey] as oldResults:
                score = oldResults.evalu if oldResults.eval >= depth and oldResults.evalu >= alpha else mini(maxDepth, depth+1, alpha, beta)
        except:
            score = mini(maxDepth, depth+1, alpha, beta)

        # if you havent seen it before then add it to the table
        board.pop()
        if score >= beta:       # beta cutoff, the score we processed is better then the sub tree's lowest score
                                # (recall beta was set to 9999999 at the start)
            return beta         # so bail, this tree is a lost cause
        if score > alpha:       # here the score is better then the best score in this tree
            alpha = score       # so update the bestMove
            moveTable[zorbKey] = OldMove(move.uci(), depth, score)  # update the moveTable too
    print('info time {} nodes {} depth {} score cp {}'.format(datetime.now() - startTime,nodes,depth,alpha))
    return alpha

def mini(maxDepth, depth, alpha, beta):
    global moveTable
    global board
    global startTime
    global threadFlag
    global nodes
    global time
    timePast = (datetime.now()-startTime).seconds   # the time that past in sec
    if timePast > time: threadFlag = True           # if we are overtime, set flag to exit
    if depth >= maxDepth or threadFlag: return -evalFunction(board)
    for move in board.legal_moves:          # now go through all our moves
        nodes += 1
        board.push(move)                    # update the board with that move
        zorbKey = boardToZorbistKey(board)
        try:
            with moveTable[zorbKey] as oldResults:
                score = oldResults.evalu if oldResults.eval >= depth and oldResults.evalu <= beta else maxi(maxDepth, depth+1, alpha, beta)
        except:
            score = maxi(maxDepth, depth+1, alpha, beta)

        # if you havent seen it before then add it to the table
        board.pop()
        if score <= alpha:      # alpha cutoff, the score we got is REALLY GOOD, we want the opponent to lose remember?
            return alpha        # (recall alpha was set to -999999 at the start)
        if score < beta:        # we got a worse score, great use it instead
            beta = score
            moveTable[zorbKey] = OldMove(move.uci(), depth, score)
    print('info time {} nodes {} depth {} score cp {}'.format(datetime.now() - startTime,nodes,depth,beta))
    return beta

def boardToZorbistKey(mBoard):
    global zorbistSqaures 
    global zorbistIsBlack 
    global zorbistCastling 
    global zorbistEnPassant 
    result = 0

    # square
    for square,piece in mBoard.piece_map().items():
        symb = piece.symbol()
        result = result ^ zorbistSqaures[square][symb]
    
    result = result ^ zorbistIsBlack if mBoard.turn == False else result

    #castling
    whiteQueen = zorbistCastling[0]
    whiteKing = zorbistCastling[1]
    blackQueen = zorbistCastling[2]
    blackKing = zorbistCastling[3]
    if mBoard.has_queenside_castling_rights(chess.WHITE): result = result ^ whiteQueen
    if mBoard.has_kingside_castling_rights(chess.WHITE): result = result ^ whiteKing
    if mBoard.has_queenside_castling_rights(chess.BLACK): result = result ^ blackQueen
    if mBoard.has_kingside_castling_rights(chess.BLACK): result = result ^ blackKing
    
    #en passant, there can be a max of one en passant
    if mBoard.has_legal_en_passant(): result = result ^ zorbistEnPassant[chess.square_file(board.ep_square)]
    return result

def calcPV():
    global moveTable
    global board
    i = 0
    resStr = []
    zorbKey = boardToZorbistKey(board)
    while(zorbKey in moveTable):
        move = moveTable[zorbKey].bestMove
        resStr.append(move)
        board.push_uci(move)    # found the bug, duplicate zorbKeys, work on your zorbKey func
        zorbKey = boardToZorbistKey(board)
        i+=1
    for k in range(i):
        board.pop()
    return ' '.join(resStr)

        
# inStr is the parameters that the gui sends to go like 'movetime' 'depth' ...
def iGo(inStr):
    global moveTable
    global board
    global startTime
    global time                     # used to limit the search, not passed into the max/min func
    global bestMove
    global nodes
    global threadFlag
    time = 15                   # default time to search
    depth = 2                       # default depth is 2 for now
    inStr = inStr.split(' ')        # get the depth if the gui passed it in
    if 'depth' in inStr:
        depth = int(inStr[inStr.index('depth')+1])
    if 'movetime' in inStr:         # get the movetime if the gui passed it in
        time = int(inStr[inStr.index('movetime')+1]) / 1000
    startTime = datetime.now()  # set the startTime here, then the min and max function can display time passed

    nodes = 0           # nodes processed throught the search
    val = -999999       # the max score for a root move
    newVal = 0          # score of the current root move
    moveLen = board.legal_moves.count()
    moveList = [None]*moveLen

    # while the stop signal isn't recieved
    while (not threadFlag):
        i = 0
        # do iterative deepening on the root moves to fill up the movesTable
        for move in board.legal_moves:
            if threadFlag: break
            board.push(move)
            zorbKey = boardToZorbistKey(board)
            try:
                with moveTable[zorbKey] as oldResults:  # if the moves has been seen before then use that old eval to help you
                    #if the oldResults are deep enought
                    newVal = oldResults.evalu if oldResults.eval >= depth else mini(depth, 1, -99999, 99999)
            except:
                newVal = mini(depth, 1, -99999, 99999)
            board.pop()
            moveList[i] = (move.uci(),0+newVal)
            i += 1
        pair = max(moveList,key=itemgetter(1))
        bestMove = pair[0]
        depth += 1
    moveTable[boardToZorbistKey(board)] = OldMove(bestMove,depth,pair[1]-1)  # update the moveTable
    print('info nodes {} depth {} pv {}'.format(nodes, depth, calcPV()))
    threadFlag = False
    print('info time {}'.format(datetime.now()-startTime))  # print the time it took
    print ('bestmove {}'.format(bestMove))      # finally print out the best move
        
# stop the go thread
def stopThread():
    global threadFlag
    threadFlag = True
    #global goThread
    #goThread.join(1000)


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

# evals will be positive if white is winning and negative if black is winning
def evalFunction(mBoard):
    color = mBoard.turn
    ''' OLD SLOW CODE
    # material evaluation, might be really slow try to optimize
    scoreForKings = 20000 * (mBoard.pieces(chess.KING,color).__len__() - mBoard.pieces(chess.KING,not color).__len__())
    scoreForQueens = 900* (mBoard.pieces(chess.QUEEN,color).__len__() - mBoard.pieces(chess.QUEEN,not color).__len__())
    scoreForRook = 500 * (mBoard.pieces(chess.ROOK,color).__len__() - mBoard.pieces(chess.ROOK,not color).__len__())
    scoreForBishopKnight = (mBoard.pieces(chess.BISHOP,color).__len__()-mBoard.pieces(chess.BISHOP,not color).__len__())
    scoreForBishopKnight += (mBoard.pieces(chess.KNIGHT,color).__len__()-mBoard.pieces(chess.KNIGHT,not color).__len__())
    scoreForBishopKnight *= 330
    scoreForPawn = 100 * (mBoard.pieces(chess.PAWN,color).__len__() - mBoard.pieces(chess.PAWN,not color).__len__())
    '''
    scoreForKings = 0
    scoreForQueens = 0
    scoreForRook = 0
    scoreForBishopKnight = 0
    scoreForPawn = 0

    # position evaluation
    pieceMap = mBoard.piece_map()
    for square,piece in pieceMap.items():
        if piece.color == chess.WHITE:        # if white reverse the position tables
            mfile = chess.square_file(square)
            mrank = chess.square_rank(square)
            mrank = 7 - mrank
            reversedSquare = chess.square(mfile,mrank)
            if piece.piece_type == chess.PAWN:
                scoreForPawn += pawnTable[reversedSquare]
                scoreForPawn += 100
            elif piece.piece_type == chess.KNIGHT:
                scoreForBishopKnight += knightTable[reversedSquare]
                scoreForBishopKnight += 320
            elif piece.piece_type == chess.BISHOP:
                scoreForBishopKnight += bishopTable[reversedSquare]
                scoreForBishopKnight += 330
            elif piece.piece_type == chess.ROOK:
                scoreForRook += rookTable[reversedSquare]
                scoreForRook += 500
            elif piece.piece_type == chess.QUEEN:
                scoreForQueens += queenTable[reversedSquare]
                scoreForQueens += 900
            elif piece.piece_type == chess.KING:
                scoreForKings += kingTable[reversedSquare]
                scoreForKings += 20000
        else:
            if piece.piece_type == chess.PAWN:
                scoreForPawn -= pawnTable[square]
                scoreForPawn -= 100
            elif piece.piece_type == chess.KNIGHT:
                scoreForBishopKnight -= knightTable[square]
                scoreForBishopKnight -= 320
            elif piece.piece_type == chess.BISHOP:
                scoreForBishopKnight -= bishopTable[square]
                scoreForBishopKnight -= 330
            elif piece.piece_type == chess.ROOK:
                scoreForRook -= rookTable[square]
                scoreForRook -= 500
            elif piece.piece_type == chess.QUEEN:
                scoreForQueens -= queenTable[square]
                scoreForQueens -= 900
            elif piece.piece_type == chess.KING:
                scoreForKings -= kingTable[square]
                scoreForKings -= 20000
    '''
    # Mobility evaluation, This might be slow too
    scoreMobility = mBoard.legal_moves.count()  # my num of legal moves
    mBoard.push(chess.Move.null())              # push a null move to change to the other side
    scoreMobility -= mBoard.legal_moves.count() # -opponents num of legal moves
    scoreMobility *= 0.1
    mBoard.pop()    # pop the null move
    return scoreForKings + scoreForQueens + scoreForRook + scoreForBishopKnight + scoreForPawn + scoreMobility
    '''
    return (scoreForKings + scoreForQueens + scoreForRook + scoreForBishopKnight + scoreForPawn) * (1 if color else -1)

def iPrint():
    print(board)

if __name__ == "__main__":
    main()
