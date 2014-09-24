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
  | Author: Michael Maclean <mgdm@php.net>                               |
  +----------------------------------------------------------------------+
*/

/* $Id$ */

/*  Based on the public domain algorithm found at
	http://www.isthe.com/chongo/tech/comp/fnv/index.html */

#include "fnv.h"

/* {{{ FNV132Init
 * 32-bit FNV-1 hash initialisation
 */
void FNV132Init(FNV132_CTX *context)
{
	context->state = FNV1_32_INIT;
}
/* }}} */

void FNV132Update(FNV132_CTX *context, const unsigned char *input,
		unsigned int inputLen)
{
	context->state = fnv_32_buf((void *)input, inputLen, context->state, 0);
}

void FNV1a32Update(FNV132_CTX *context, const unsigned char *input,
		unsigned int inputLen)
{
	context->state = fnv_32_buf((void *)input, inputLen, context->state, 1);
}

void FNV132Final(unsigned char digest[4], FNV132_CTX * context)
{
#ifdef WORDS_BIGENDIAN
	memcpy(digest, &context->state, 4);
#else
	int i = 0;
	unsigned char *c = (unsigned char *) &context->state;

	for (i = 0; i < 4; i++) {
		digest[i] = c[3 - i];
	}
#endif
}

/* {{{ FNV164Init
 * 64-bit FNV-1 hash initialisation
 */
void FNV164Init(FNV164_CTX *context)
{
	context->state = FNV1_64_INIT;
}
/* }}} */

void FNV164Update(FNV164_CTX *context, const unsigned char *input,
		unsigned int inputLen)
{
	context->state = fnv_64_buf((void *)input, inputLen, context->state, 0);
}

void FNV1a64Update(FNV164_CTX *context, const unsigned char *input,
		unsigned int inputLen)
{
	context->state = fnv_64_buf((void *)input, inputLen, context->state, 1);
}

void FNV164Final(unsigned char digest[8], FNV164_CTX * context)
{
#ifdef WORDS_BIGENDIAN
	memcpy(digest, &context->state, 8);
#else
	int i = 0;
	unsigned char *c = (unsigned char *) &context->state;

	for (i = 0; i < 8; i++) {
		digest[i] = c[7 - i];
	}
#endif
}


/*
 * fnv_32_buf - perform a 32 bit Fowler/Noll/Vo hash on a buffer
 *
 * input:
 *  buf - start of buffer to hash
 *  len - length of buffer in octets
 *  hval	- previous hash value or 0 if first call
 *  alternate - if > 0 use the alternate version
 *
 * returns:
 *  32 bit hash as a static hash type
 */
static uint32_t
fnv_32_buf(void *buf, size_t len, uint32_t hval, int alternate)
{
	unsigned char *bp = (unsigned char *)buf;   /* start of buffer */
	unsigned char *be = bp + len;	   /* beyond end of buffer */

	/*
	 * FNV-1 hash each octet in the buffer
	 */
	while (bp < be) {

		if (alternate == 0) {
			/* multiply by the 32 bit FNV magic prime mod 2^32 */
			hval *= FNV_32_PRIME;

			/* xor the bottom with the current octet */
			hval ^= (uint32_t)*bp++;
		} else {
			/* xor the bottom with the current octet */
			hval ^= (uint32_t)*bp++;

			/* multiply by the 32 bit FNV magic prime mod 2^32 */
			hval *= FNV_32_PRIME;
		}
	}

	/* return our new hash value */
	return hval;
}

/*
 * fnv_64_buf - perform a 64 bit Fowler/Noll/Vo hash on a buffer
 *
 * input:
 *  buf - start of buffer to hash
 *  len - length of buffer in octets
 *  hval	- previous hash value or 0 if first call
 *  alternate - if > 0 use the alternate version
 *
 * returns:
 *  64 bit hash as a static hash type
 */
static uint64_t
fnv_64_buf(void *buf, size_t len, uint64_t hval, int alternate)
{
	unsigned char *bp = (unsigned char *)buf;   /* start of buffer */
	unsigned char *be = bp + len;	   /* beyond end of buffer */

	/*
	 * FNV-1 hash each octet of the buffer
	 */
	while (bp < be) {

		if (alternate == 0) {
			/* multiply by the 64 bit FNV magic prime mod 2^64 */
			hval *= FNV_64_PRIME;

			/* xor the bottom with the current octet */
			hval ^= (uint64_t)*bp++;
		 } else {
			/* xor the bottom with the current octet */
			hval ^= (uint64_t)*bp++;

			/* multiply by the 64 bit FNV magic prime mod 2^64 */
			hval *= FNV_64_PRIME;
		 }
	}

	/* return our new hash value */
	return hval;
}
