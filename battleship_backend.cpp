#include <iostream>
#include <vector>
#include <utility>
#include <cstring>

using namespace std;

const int N = 10;

struct Ship {
    vector<pair<int,int>> cells;
    bool sunk = false;
};

struct Board {
    int cells[N][N];          // 0 - empty, 1 - ship, 2 - hit, 3 - miss
    vector<Ship> ships;
    int totalShipCells;
    bool ready;
    Board() {
        memset(cells, 0, sizeof(cells));
        totalShipCells = 0;
        ready = false;
    }
};

Board boards[3];              // boards[1], boards[2]
int currentPlayer = 1;

bool inBounds(int x, int y) {
    return x >= 0 && x < N && y >= 0 && y < N;
}

// заборона дотику кораблів
bool canPlace(Board &b, int x, int y, int len, bool horiz) {
    for (int i = 0; i < len; i++) {
        int nx = x + (horiz ? 0 : i);
        int ny = y + (horiz ? i : 0);
        if (!inBounds(nx, ny)) return false;
        if (b.cells[nx][ny] != 0) return false;
        // заборона сусідства
        for (int dx = -1; dx <= 1; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                int xx = nx + dx;
                int yy = ny + dy;
                if (inBounds(xx, yy) && b.cells[xx][yy] == 1) {
                    return false;
                }
            }
        }
    }
    return true;
}

bool placeShip(Board &b, int x, int y, int len, bool horiz) {
    if (!canPlace(b, x, y, len, horiz)) return false;
    Ship s;
    for (int i = 0; i < len; i++) {
        int nx = x + (horiz ? 0 : i);
        int ny = y + (horiz ? i : 0);
        b.cells[nx][ny] = 1;
        s.cells.push_back({nx, ny});
        b.totalShipCells++;
    }
    b.ships.push_back(s);
    return true;
}

bool allSunk(Board &b) {
    int hits = 0;
    for (auto &ship : b.ships) {
        bool sunk = true;
        for (auto &c : ship.cells) {
            if (b.cells[c.first][c.second] != 2) {
                sunk = false;
            }
        }
        ship.sunk = sunk;
    }
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            if (b.cells[i][j] == 2) hits++;
    return hits == b.totalShipCells;
}

void printState(int p) {
    Board &me = boards[p];
    Board &enemy = boards[(p == 1) ? 2 : 1];
    cout << "PLAYER " << p << "\n";
    cout << "OWN\n";
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            char ch = '.';
            int c = me.cells[i][j];
            if (c == 0) ch = '.';
            else if (c == 1) ch = 'S';
            else if (c == 2) ch = 'H';
            else if (c == 3) ch = 'M';
            cout << ch;
        }
        cout << "\n";
    }
    cout << "ENEMY\n";
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            char ch = '.';
            int c = enemy.cells[i][j];
            if (c == 2) ch = 'H';
            else if (c == 3) ch = 'M';
            cout << ch;
        }
        cout << "\n";
    }
    cout << "END\n";
    cout.flush();
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string cmd;
    while (cin >> cmd) {
        if (cmd == "INIT") {
            boards[1] = Board();
            boards[2] = Board();
            currentPlayer = 1;
            cout << "OK INIT\n";
            cout.flush();
        }
        else if (cmd == "SET") {
            int p, len, x, y;
            char orient;
            cin >> p >> len >> x >> y >> orient;
            if (p != 1 && p != 2) { cout << "ERR SET\n"; cout.flush(); continue; }
            bool horiz = (orient == 'H');
            if (placeShip(boards[p], x, y, len, horiz)) {
                cout << "OK SET\n";
            } else {
                cout << "ERR SET\n";
            }
            cout.flush();
        }
        else if (cmd == "READY") {
            int p; cin >> p;
            if (p != 1 && p != 2) { cout << "ERR READY\n"; cout.flush(); continue; }
            boards[p].ready = true;
            cout << "OK READY " << p << "\n";
            cout.flush();
        }
        else if (cmd == "STATUS") {
            if (!boards[1].ready || !boards[2].ready) {
                cout << "NOTREADY\n";
            } else {
                cout << "TURN " << currentPlayer << "\n";
            }
            cout.flush();
        }
        else if (cmd == "STATE") {
            int p; cin >> p;
            if (p != 1 && p != 2) { cout << "ERR\n"; cout.flush(); continue; }
            printState(p);
        }
        else if (cmd == "SHOT") {
            int p, x, y;
            cin >> p >> x >> y;
            if (!boards[1].ready || !boards[2].ready) {
                cout << "ERR NOTREADY\n"; cout.flush(); continue;
            }
            if (p != currentPlayer) {
                cout << "ERR NOTYOURTURN\n"; cout.flush(); continue;
            }
            int enemyId = (p == 1) ? 2 : 1;
            Board &enemy = boards[enemyId];
            if (!inBounds(x, y)) {
                cout << "MISS\n";
                currentPlayer = enemyId;
                cout.flush();
                continue;
            }
            int &c = enemy.cells[x][y];
            if (c == 1) {
                c = 2;
                bool sunkShip = false;
                for (auto &ship : enemy.ships) {
                    bool sunk = true;
                    for (auto &cell : ship.cells) {
                        if (enemy.cells[cell.first][cell.second] != 2) {
                            sunk = false;
                            break;
                        }
                    }
                    if (sunk && !ship.sunk) {
                        ship.sunk = true;
                        sunkShip = true;
                    }
                }
                if (allSunk(enemy)) {
                    cout << "WIN " << p << "\n";
                } else if (sunkShip) {
                    cout << "SUNK\n";
                } else {
                    cout << "HIT\n";
                }
            } else if (c == 0) {
                c = 3;
                cout << "MISS\n";
                currentPlayer = enemyId;
            } else {
                // вже стріляли — рахуємо як промах
                cout << "MISS\n";
                currentPlayer = enemyId;
            }
            cout.flush();
        }
        else {
            cout << "ERR\n";
            cout.flush();
        }
    }
    return 0;
}
