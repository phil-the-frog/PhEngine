import chess

author = 'Phillip Sopt'
engineName = 'PhEngine'

def main():
    while True:
        uciIn = input()
        if uciIn == 'uci':
            iUci()
        elif 'setoption' in uciIn[:9]:
            iSetOption(uciIn[10:])      # 10 to skip the whitespace
        elif uciIn == 'isready':
            iIsReady()
        elif uciIn == 'ucinewgame':
            iNewGame()
        elif 'position' in uciIn[:8]
    




def iUci():
    print('id name {}'.format(engineName))
    print('id author {}'.format(author))
    print('uciok')

def iSetOption(inStr):
    #set the option

def iIsReady():
    print('readyok')

            


if __name__ == "__main__":
    main()