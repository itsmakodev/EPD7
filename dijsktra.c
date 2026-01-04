#include <stdio.h>

#define MAX_NODES 6
#define INFINITY 1000000000

enum node_label {
    permanent,
    tentative
};

int shortest_path(int s, int t, int path[])
{
    struct state {
        int predecessor;
        int length;
        enum node_label label;
    } state[MAX_NODES];

    int i, k, min;
    struct state *p;

    for (p = &state[0]; p < &state[MAX_NODES]; p++) {
        p->predecessor = -1;
        p->length = INFINITY;
        p->label = tentative;
    }

    state[t].length = 0;
    state[t].label = permanent;
    k = t;

    do {
        for (i = 0; i < MAX_NODES; i++) {
            if (dist[k][i] != 0 && state[i].label == tentative) {
                if (state[k].length + dist[k][i] < state[i].length) {
                    state[i].length = state[k].length + dist[k][i];
                    state[i].predecessor = k;
                }
            }
        }

        k = 0;
        min = INFINITY;
        for (i = 0; i < MAX_NODES; i++) {
            if (state[i].label == tentative && state[i].length < min) {
                min = state[i].length;
                k = i;
            }
        }

        state[k].label = permanent;

    } while (k != s);

    i = 0;
    k = s;
    do {
        path[i++] = k;
        k = state[k].predecessor;
    } while (k != t);

    path[i++] = t;
    return i;
}

int main(void)
{
    int path[MAX_NODES];
    int i, length;
    int source = 0;
    int destination = 5;

    length = shortest_path(source, destination, path);
}
