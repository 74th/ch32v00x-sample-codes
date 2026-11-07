#ifndef FIXTURE_H
#define FIXTURE_H
#include <stdbool.h>
bool fixture_allowed(unsigned pin);
bool fixture_claim(unsigned pin);
void fixture_safe(void);
#endif
