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
from operator import attrgetter
import traceback
from enum import Enum
import cProfile

p = cProfile.Profile()
p.enable()

board = chess.Board()       # internal state of the board
author = 'Phillip Sopt'
engineName = 'PhEngine'
goThread = None             # the thread on which the 'go' command will run
moveTable = dict()          # a hash table to store the moves for each square to avoid recalculating the moves
threadFlag = False          # a flag to tell the thread when to stop running
bestMove = ''               # the current best move found, stored in uci format
hashSize = 0xFFFF           # how much to max off the zorbist key and reduce our transposition tables size

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
            #iGo(uciIn[3:])
            goThread = threading.Thread(target=iGo,name='Thread-1',args=(uciIn[3:],))   # set up the go thread and let it run
            goThread.start()
        elif uciIn == 'stop':
            stopThread()
        elif uciIn == 'quit':
            stopThread()
            p.disable()
            p.print_stats(sort='time')
            exit()
        elif uciIn == 'print':
            iPrint()
        
# stop the go thread
def stopThread():
    global threadFlag
    threadFlag = True
    global goThread
    goThread.join(1000)

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
    
# enum used for evaluation flags
class EvalFlag(Enum):
    EXACT = 0
    ALPHA = 1
    BETA = 2
# this is the structure that we are going to use to store our past moves in the moveTable transposition table
class MyMove:
    zorbKey = 0     # the key used
    bestMove = ''   # uci of the move
    depth = 0       # how deep did we find it
    evalu = 0       # what was it's evaluation
    flag = 0

    def __init__(self, bestMove, depth, evalu, flag, zorbKey): # constructor
        self.bestMove = bestMove
        self.depth = depth
        self.evalu = evalu
        self.flag = flag
        self.zorbKey = zorbKey

    def __lt__(self,other):
        return self.evalu < other.evalu
    def __eq__(self,other):
        return self.evalu == other.evalu

nodes = 0
hashHits = 0

def probe_table(depth, alpha, beta):
    key = boardToZorbistKey(board)
    if (key & hashSize) not in moveTable: return None

    move = moveTable[key & hashSize]
    if move.zorbKey != key: return None
    global hashHits
    hashHits += 1
    
    if move.depth >= depth:
        if move.flag == EvalFlag.EXACT: return move.evalu
        if move.flag == EvalFlag.ALPHA and move.evalu <= alpha: return alpha
        if move.flag == EvalFlag.BETA and move.evalu >= beta: return beta
    return None

def record_table(depth, val, flag, move):
    global moveTable
    key = boardToZorbistKey(board)
    moveTable[key & hashSize] = MyMove(move,depth,val,flag,key)

# gets the smallest attacker on side that can attack square
def get_smallest_attacker(square, side):
    global board
    val = 999
    result = None
    attacks = list(board.attackers(side,square))
    for aSquare in attacks:
        newVal = board.piece_type_at(aSquare)
        if newVal < val:
            val = newVal
            result = aSquare
    return result   # returns square of attacker

#Static Exchange Evaluation - essentially, is this a good capture
def see(square,side):
    global board
    val = 0
    attackerSquare = get_smallest_attacker(square,side)
    if attackerSquare is not None:
        board.push(chess.Move(attackerSquare, square))  # don't know if it drops piece at square for me
        val = max(0, board.piece_type_at(square) - see(square,not side))
        board.pop()
    return val

def order_captures(captures):
    global board
    captureEvals = []
    for cap in captures:
        captureEvals.append((see(cap.to_square,board.turn),cap))
    return captureEvals.sort(key=itemgetter(0),reverse=True)

def is_capture(move):
    return True if move.drop is not None else False
def quiescent_search(alpha, beta):
    global board
    if board.is_check():
        nega_max(1,1,alpha,beta,'')
    val = evalFunction(board)
    if val >= beta:     # beta cutoff, the score we processed is better then the sub tree's lowest score
        return beta
    if val > alpha:
        alpha = val
    moveCaptures = order_captures(list(filter(is_capture,board.legal_moves)))   # order the captures using SEE so we don't
    # have a quiescent search explosion
    if moveCaptures is None: return alpha
    for move in moveCaptures:
        board.push(move)
        val = -quiescent_search(-beta,-alpha)
        board.pop()
        if val >= beta:     # beta cutoff, the score we processed is better then the sub tree's lowest score
            return beta
        if val > alpha:
            alpha = val
    return alpha

def nega_max(maxDepth, depth, alpha, beta, pv):
    global nodes
    global board
    global threadFlag
    bestMove = ''
    nodes += 1
    print('info nodes {} pv {}'.format(nodes, pv))
    hashFlag = EvalFlag.ALPHA
    val = probe_table(maxDepth - depth, alpha, beta)
    if val is not None: return val
    if depth >= maxDepth or threadFlag:
        if not board.is_check:
            val = quiescent_search(alpha, beta)
        else:
            val = evalFunction(board)
        record_table(depth, val, EvalFlag.EXACT, '')
        return val
    
    for move in board.legal_moves:
        board.push(move)
        val = nega_max(maxDepth, depth+1, -beta, -alpha, pv+' '+move.uci()) * -1
        board.pop()
        if val >= beta:     # beta cutoff, the score we processed is better then the sub tree's lowest score
            record_table(depth, beta, EvalFlag.BETA, move.uci())
            return beta
        if val > alpha:
            hashFlag = EvalFlag.EXACT
            bestMove = move.uci()
            alpha = val
    record_table(depth,alpha,hashFlag, bestMove)
    return alpha

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
        move = moveTable[zorbKey & hashSize].bestMove
        resStr.append(move)
        board.push_uci(move)    # found the bug, duplicate zorbKeys, work on your zorbKey func
        zorbKey = boardToZorbistKey(board)
        i+=1
    for k in range(i):
        board.pop()
    return ' '.join(resStr)
# this will run in another thread and will stop the go function if time is set
def timer(maxTime,startTime):
    while(maxTime > (datetime.now()-startTime).seconds):
        continue
    stopThread()

# inStr is the parameters that the gui sends to go like 'movetime' 'depth' ...
def iGo(inStr):
    global hashHits
    global moveTable
    global board
    global bestMove
    global nodes
    global threadFlag
    hashHits = 0
    time = 15                       # default time to search in seconds
    depth = 1                       # default starting depth is 1 for now
    inStr = inStr.split(' ')        # get the depth if the gui passed it in
    if 'depth' in inStr:
        depth = int(inStr[inStr.index('depth')+1])
    if 'movetime' in inStr:         # get the movetime if the gui passed it in
        time = int(inStr[inStr.index('movetime')+1]) / 1000
    startTime = datetime.now()  # set the startTime here, then the min and max function can display time passed
    timeThread = threading.Thread(target=timer,args=(time,startTime))   # start the timer thread
    timeThread.start()

    nodes = 0           # nodes processed throught the search
    moveList = []
    for move in board.legal_moves:
        moveList.append(MyMove(move.uci(),0,0,0,0))

    # probe the table and save the order the move list
    for move in moveList:
        board.push_uci(move.bestMove)
        newVal = probe_table(0, -99999, 99999)
        board.pop()
        if newVal is not None:
            move.evalu = newVal
    moveList.sort(reverse=True)

    # while the stop signal isn't recieved
    while (not threadFlag):
        # do iterative deepening on the root moves to fill up the movesTable
        for move in moveList:
            board.push_uci(move.bestMove)
            newVal = nega_max(depth, 1, -99999, 99999, move.bestMove) * -1
            board.pop()
            move.evalu = newVal
            if threadFlag : 
                moveList.sort(reverse=True)
                break
        depth += 1
        moveList.sort(reverse=True)
        print('info depth {}'.format(depth))
    print('info depth {}'.format(depth))
    threadFlag = False
    print('info time {}'.format(datetime.now()-startTime))  # print the time it took
    print('info hashHits {}'.format(hashHits))
    print ('bestmove {}'.format(moveList[0].bestMove))      # finally print out the best move



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
    return scoreForKings + scoreForQueens + scoreForRook + scoreForBishopKnight + scoreForPawn + scoreMobility * (1 if color else -1)
    '''
    
    return (scoreForKings + scoreForQueens + scoreForRook + scoreForBishopKnight + scoreForPawn) * (1 if color else -1)

def iPrint():
    print(board)

if __name__ == "__main__":
    main()
