/* SPDX-License-Identifier: GPL-2.0 */
/* Excerpt: the timer API as this tree declares it. */
#ifndef _LINUX_TIMER_H
#define _LINUX_TIMER_H

#include <linux/list.h>
#include <linux/ktime.h>
#include <linux/stddef.h>
#include <linux/debugobjects.h>
#include <linux/stringify.h>

struct timer_list {
	struct hlist_node	entry;
	unsigned long		expires;
	void			(*function)(struct timer_list *);
	u32			flags;
};

#define timer_setup(timer, callback, flags)			\
	__init_timer((timer), (callback), (flags))

#define from_timer(var, callback_timer, timer_fieldname) \
	container_of(callback_timer, typeof(*var), timer_fieldname)

extern void add_timer_on(struct timer_list *timer, int cpu);
extern int del_timer(struct timer_list * timer);
extern int mod_timer(struct timer_list *timer, unsigned long expires);
extern int mod_timer_pending(struct timer_list *timer, unsigned long expires);
extern int timer_reduce(struct timer_list *timer, unsigned long expires);

extern void add_timer(struct timer_list *timer);

extern int try_to_del_timer_sync(struct timer_list *timer);

#if defined(CONFIG_SMP) || defined(CONFIG_PREEMPT_RT)
  extern int del_timer_sync(struct timer_list *timer);
#else
# define del_timer_sync(t)		del_timer(t)
#endif

#define del_singleshot_timer_sync(t) del_timer_sync(t)

#endif
