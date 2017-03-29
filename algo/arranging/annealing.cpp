#include <stdio.h>
#include <random>
#include <ctime>
#include <cmath>
#include <algorithm>

#define MAXN 1000
#define ATOMIC_ITERATIONS 1000

double A[MAXN+1][MAXN+1];
int path[MAXN+2];


// Requires two arguments: N and T, then N^2 numbers - the array
int main(int argc, char** argv) {
  int N = (int) sqrt(argc - 1);
  if (N * N + 1 != argc){printf ("Error. No matrix."); return 1;}
  if (N<2 || N>MAXN) {printf ("Error. Must be 2 <= N <= %d\n", MAXN); return 2;}


  clock_t run_time = std::max((N * CLOCKS_PER_SEC)/4, 25*CLOCKS_PER_SEC);
  clock_t start_time = clock();
  clock_t elapsed = 0;


  for (int i=1; i<=N; ++i) path[i] = i-1;
  std::random_shuffle (path+1, path+N+1);
  path[0] = path[N+1] = MAXN;
  for (int i=0;i<=N+1;++i) A[i][MAXN] = A[MAXN][i] = 0;

  for (int i=0; i<N; ++i)
    for(int j=0; j<N; ++j)
      A[i][j] = atof(argv[1+N*i+j]);

  for (int i=0; i<N;++i) {
    if (abs(A[i][i]>1e-9)) {printf ("Error. Diagonal elements must be zero."); return 3;}
  }

  std::mt19937 rnd_gen;
  double cur_weight = 0;
  double minus_q_inv;
  double RAND_MAX_DOUBLE = (double)rnd_gen.max();
  for (int i=1; i<=N; ++i) cur_weight += A[path[i]][path[i+1]];

  while (elapsed < run_time) {
    minus_q_inv = -1.0 / (cur_weight * 0.05 * (1 - (double)elapsed / (double)run_time));

    for (int c = 0; c < ATOMIC_ITERATIONS; ++c) {
      int i = rnd_gen() % N + 1;
      int j = rnd_gen() % N + 1;
      int pi = path[i];
      int pj = path[j];


      double change_weight = - A[pi][path[i-1]] - A[pi][path[i+1]]
                           - A[pj][path[j-1]] - A[pj][path[j+1]]
                           + A[pj][path[i-1]] + A[pj][path[i+1]]
                           + A[pi][path[j-1]] + A[pi][path[j+1]];

      if (change_weight < 0 || rnd_gen() < RAND_MAX_DOUBLE * exp(change_weight * minus_q_inv)) {
        //apply
        cur_weight += change_weight;
        path[i] = pj;
        path[j] = pi;
      }
    }

    elapsed = clock() - start_time;
  }

  for (int i = 1; i <= N;++i) printf("%d ", path[i]);
  return 0;
}
