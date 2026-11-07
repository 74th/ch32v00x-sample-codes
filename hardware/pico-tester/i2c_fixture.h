#ifndef I2C_FIXTURE_H
#define I2C_FIXTURE_H
void i2c_fixture_selftest(unsigned long id, char *args);
void i2c_fixture_faulttest(unsigned long id, char *args);
void i2c_fixture_probe(unsigned long id, char *args);
void i2c_fixture_master(unsigned long id, char *args);
void i2c_fixture_slave(unsigned long id, char *args);
#endif
