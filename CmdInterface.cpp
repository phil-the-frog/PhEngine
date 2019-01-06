#include <unistd.h>

int main(){
    char* temp[] = {"python.exe", "C:\\Users\\Windows 10 64-bit\\Documents\\ChessBot\\ph-engine.py", (char*)NULL};
    execvp("python.exe", temp);
}