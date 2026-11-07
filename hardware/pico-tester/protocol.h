#ifndef PROTOCOL_H
#define PROTOCOL_H
#include <stdbool.h>
bool protocol_number(const char *s, unsigned long max, unsigned long *out);
void protocol_error(unsigned long id, const char *kind, const char *message);
void protocol_process(char *line);
#endif
