import chess



board = chess.Board()
author = 'Phillip Sopt'
engineName = 'PhEngine'

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
        

    




def iUci():
    print('id name {}'.format(engineName))
    print('id author {}'.format(author))
    print('uciok')

def iSetOption(inStr):
    #set the option
    pass

def iIsReady():
    print('readyok')

def iNewGame():
    pass

def iPosition(inStr):
    if inStr.startswith('startpos'):
        inStr = inStr.partition(' ')[3]     # partition string 
        board.set_board_fen(chess.STARTING_BOARD_FEN)
        #do a while loop till there's no more input
        if

    elif inStr.startswith('fen'):
        board.set_board_fen(inStr[4:])  # use the fen string at the end to build a new board
    


            


if __name__ == "__main__":
    main()