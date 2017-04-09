#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#define MAXN 1000

int perm[MAXN+2];
double X[MAXN+2][MAXN+2];

int N;


double energy(int N) {
    double ans = 0;
    for(int i=1;i<N;++i) ans += X[perm[i]][perm[i+1]];
    return ans;
}


void* arrange(int N, double Tmin, double Tmax, int steps, double* dist, int* answer) {
    int i, j, step;
    freopen("D:\\visartm\\algo\\clib\\log.txt", "w", stdout);

    for (i = 1; i <= N; ++i) perm[i] = answer[i-1] + 1;
    perm[0] = 0;
    perm[N+1] = 0;

    double E = energy(N);
    double Emin = E;
    double Tfactor = -log(Tmax/Tmin) / steps;
    double T = Tmax;

    for(i=0;i<=N;i++) {
        X[i][0] = X[0][i] = 0;
    }

    for (i=1; i<=N; i++)
        for (j=1; j<=N; j++) {
            X[i][j] = dist[(i-1)*N + (j-1)];
        }


    for (step = 0; step < steps; step++) {
        T = Tmax * exp(Tfactor * step);
        i = rand() % N + 1;
        j = rand() % N + 1;
        int pi = perm[i];
        int pj = perm[j];

        double dE = - X[perm[i-1]][pi] - X[perm[i+1]][pi]
                    - X[perm[j-1]][pj] - X[perm[j+1]][pj];

        perm[i] = pj;
        perm[j] = pi;

        dE +=  X[perm[i-1]][pj] + X[perm[i+1]][pj]
             + X[perm[j-1]][pi] + X[perm[j+1]][pi];

        //printf("%d %d dE=%lg\n", i,j,dE);

        if (dE > 0.0 && exp(-dE / T) < (double)rand()/(double)RAND_MAX ) {
            // Revoke
            perm[i] = pi;
            perm[j] = pj;
        } else {
            // Accept
            E += dE;
            if (E < Emin) {
                Emin = E;
                for (i=0;i<N;i++) answer[i] = perm[i + 1] - 1;
            }
        }
    }

    fflush(stdout);
}

int main() {
    double dist[1];
    int ans[100];

    arrange(1,1,100,4,dist,ans);
    return 0;
}
