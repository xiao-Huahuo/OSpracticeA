/*
 * Single-hart physical page allocator. Callers run in process or boot
 * context; UART and timer handlers never allocate or release pages.
 */
#include "types.h"
#include "riscv.h"
#include "memlayout.h"
#include "defs.h"
#include "vmcore.h"

struct page {
  struct page *next;
};

static struct page *free_pages;
static uint64 first_page;

void
kinit(uint64 start)
{
  first_page = PGROUNDUP(start);
  for (uint64 pa = first_page; pa + PGSIZE <= PHYSTOP; pa += PGSIZE)
    kfree((void *)pa);
}

void
kfree(void *page)
{
  uint64 pa = (uint64)page;
  struct page *entry;

  if (pa < first_page || pa >= PHYSTOP || (pa & (PGSIZE - 1))) {
    kprintf("lab2: invalid free %lx\n", pa);
    for (;;)
      asm volatile("wfi");
  }
  entry = (struct page *)page;
  entry->next = free_pages;
  free_pages = entry;
}

void *
kalloc(void)
{
  struct page *entry = free_pages;

  if (entry == 0)
    return 0;
  free_pages = entry->next;
  for (uint64 i = 0; i < PGSIZE; i++)
    ((char *)entry)[i] = 0;
  return entry;
}
