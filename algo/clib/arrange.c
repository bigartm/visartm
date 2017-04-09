#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#define MAXN 1000

int shot_i[MAXN*MAXN];
int shot_j[MAXN*MAXN];

int perm[MAXN+2];
double X[MAXN+2][MAXN+2];

int N;

/*
double energy(int N) {
    double ans = 0;
    int i;
    for (i=1;i<N;++i) ans += X[perm[i]][perm[i+1]];
    return ans;
}
*/


// clusters_num - number of clusters
// clusters_size - lengthes of clusters

void arrange(int N, double Tmin, double Tmax, int steps,
              double* dist, int* answer,
              int clusters_num, int* clusters_size) {
    if (N <= 2) return;
    if (N > MAXN) return;
    int i, j, step, cl;
    //freopen("D:\\visartm\\algo\\clib\\log.txt", "w", stdout);

    // Clusers preprocessing
    int cluster_offset = 1;
    int pairs_count = 0;
    for (cl = 0; cl < clusters_num; ++cl) {
        int cs = clusters_size[cl];
        for (i = cluster_offset; i < cluster_offset + cs; ++i) {
            for (j = i + 1; j < cluster_offset + cs; j++) {
                shot_i[pairs_count] = i;
                shot_j[pairs_count] = j;
                pairs_count++;
            }
        }
        cluster_offset += cs;
    }

    // Initial permutation
    for (i = 1; i <= N; ++i) perm[i] = answer[i-1] + 1;
    perm[0] = 0;
    perm[N+1] = 0;

    double E = 0;
    for (i=1;i<N;++i) E += X[perm[i]][perm[i+1]];
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
        cl = (rand()*(RAND_MAX+1)+rand()) % pairs_count;
        i = shot_i[cl];
        j = shot_j[cl];

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

    //fflush(stdout);
}

int main() {
    double dist[4];
    int clusters[1];
    clusters[0] = 2;
    int ans[100];
    ans[0]=0;
    ans[1]=1;

    arrange(2,1,100,4,dist,ans,1,clusters);
    return 0;
}
