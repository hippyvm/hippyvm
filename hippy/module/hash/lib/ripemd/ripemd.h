/*
   +----------------------------------------------------------------------+
   | PHP Version 5                                                        |
   +----------------------------------------------------------------------+
   | Copyright (c) 1997-2013 The PHP Group                                |
   +----------------------------------------------------------------------+
   | This source file is subject to version 3.01 of the PHP license,      |
   | that is bundled with this package in the file LICENSE, and is        |
   | available through the world-wide-web at the following url:           |
   | http://www.php.net/license/3_01.txt                                  |
   | If you did not receive a copy of the PHP license and are unable to   |
   | obtain it through the world-wide-web, please send a note to          |
   | license@php.net so we can mail you a copy immediately.               |
   +----------------------------------------------------------------------+
   | Author: Sara Golemon <pollita@php.net>                               |
   +----------------------------------------------------------------------+
*/
#include <stdint.h>
#include <string.h>

/* $Id$ */

/* RIPEMD context. */
typedef struct {
	uint32_t state[4];		/* state (ABCD) */
	uint32_t count[2];		/* number of bits, modulo 2^64 (lsb first) */
	unsigned char buffer[64];	/* input buffer */
} ripemd128_ctx;

typedef struct {
	uint32_t state[5];		/* state (ABCD) */
	uint32_t count[2];		/* number of bits, modulo 2^64 (lsb first) */
	unsigned char buffer[64];	/* input buffer */
} ripemd160_ctx;

typedef struct {
	uint32_t state[8];		/* state (ABCD) */
	uint32_t count[2];		/* number of bits, modulo 2^64 (lsb first) */
	unsigned char buffer[64];	/* input buffer */
} ripemd256_ctx;

typedef struct {
	uint32_t state[10];		/* state (ABCD) */
	uint32_t count[2];		/* number of bits, modulo 2^64 (lsb first) */
	unsigned char buffer[64];	/* input buffer */
} ripemd320_ctx;

void ripemd128_init(ripemd128_ctx *);
void ripemd128_update(ripemd128_ctx *, const unsigned char *, unsigned int);
void ripemd128_final(unsigned char[16], ripemd128_ctx *);

void ripemd160_init(ripemd160_ctx *);
void ripemd160_update(ripemd160_ctx *, const unsigned char *, unsigned int);
void ripemd160_final(unsigned char[20], ripemd160_ctx *);

void ripemd256_init(ripemd256_ctx *);
void ripemd256_update(ripemd256_ctx *, const unsigned char *, unsigned int);
void ripemd256_final(unsigned char[32], ripemd256_ctx *);

void ripemd320_init(ripemd320_ctx *);
void ripemd320_update(ripemd320_ctx *, const unsigned char *, unsigned int);
void ripemd320_final(unsigned char[40], ripemd320_ctx *);
