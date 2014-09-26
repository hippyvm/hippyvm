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
   | SHA1 Author: Stefan Esser <sesser@php.net>                           |
   | SHA256 Author: Sara Golemon <pollita@php.net>                        |
   +----------------------------------------------------------------------+
*/

/* $Id$ */

#include <stdint.h>
#include <string.h>

#define L64(x) x##LL

/* SHA1 context. */
typedef struct {
	uint32_t state[5];		/* state (ABCD) */
	uint32_t count[2];		/* number of bits, modulo 2^64 */
	unsigned char buffer[64];	/* input buffer */
} SHA1_CTX;

void SHA1Init(SHA1_CTX *);
void SHA1Update(SHA1_CTX *, const unsigned char *, unsigned int);
void SHA1Final(unsigned char[20], SHA1_CTX *);


/* SHA224 context. */
typedef struct {
	uint32_t state[8];		/* state */
	uint32_t count[2];		/* number of bits, modulo 2^64 */
	unsigned char buffer[64];	/* input buffer */
} SHA224_CTX;

void SHA224Init(SHA224_CTX *);
void SHA224Update(SHA224_CTX *, const unsigned char *, unsigned int);
void SHA224Final(unsigned char[28], SHA224_CTX *);

/* SHA256 context. */
typedef struct {
	uint32_t state[8];		/* state */
	uint32_t count[2];		/* number of bits, modulo 2^64 */
	unsigned char buffer[64];	/* input buffer */
} SHA256_CTX;

void SHA256Init(SHA256_CTX *);
void SHA256Update(SHA256_CTX *, const unsigned char *, unsigned int);
void SHA256Final(unsigned char[32], SHA256_CTX *);

/* SHA384 context */
typedef struct {
	uint64_t state[8];	/* state */
	uint64_t count[2];	/* number of bits, modulo 2^128 */
	unsigned char buffer[128];	/* input buffer */
} SHA384_CTX;

void SHA384Init(SHA384_CTX *);
void SHA384Update(SHA384_CTX *, const unsigned char *, unsigned int);
void SHA384Final(unsigned char[48], SHA384_CTX *);

/* SHA512 context */
typedef struct {
	uint64_t state[8];	/* state */
	uint64_t count[2];	/* number of bits, modulo 2^128 */
	unsigned char buffer[128];	/* input buffer */
} SHA512_CTX;

void SHA512Init(SHA512_CTX *);
void SHA512Update(SHA512_CTX *, const unsigned char *, unsigned int);
void SHA512Final(unsigned char[64], SHA512_CTX *);
