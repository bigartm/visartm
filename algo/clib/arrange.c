#include <stdio.h>

void* arrange(int n, double* x, int* answer)
{
    double sum = 0;
    for (int i=0;i<n;++i) {
        for(int j=0;j<n;j++)
        {
            sum += x[n*i+j];
        }
    }
    for(int i=0;i<n;++i) answer[i] = i;
    answer[0] = 1;
    answer[1] = 0;
}
