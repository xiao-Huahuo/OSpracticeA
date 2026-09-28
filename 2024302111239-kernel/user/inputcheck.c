/* Count a burst smaller than the assigned UART ring capacity. */
#include "kernel/types.h"
#include "kernel/course_sid.h"
#include "user/user.h"

int
main(void)
{
  int count = 0, sum = 0;
  char c;

  while (count < LAB2_BUF_SIZE / 2) {
    if (read(0, &c, 1) != 1)
      exit(1);
    sum += (uchar)c;
    count++;
  }
  printf("INPUTCHECK count=%d checksum=%d\n", count, sum);
  exit(0);
}
