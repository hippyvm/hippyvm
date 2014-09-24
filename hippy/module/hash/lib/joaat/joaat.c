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
  | Author: Martin Jansen <mj@php.net>                                   |
  +----------------------------------------------------------------------+
*/

/* $Id$ */

/* Implements Jenkins's one-at-a-time hashing algorithm as presented on
 * http://www.burtleburtle.net/bob/hash/doobs.html.
 */

#include "joaat.h"


void JOAATInit(JOAAT_CTX *context)
{
	context->state = 0;
}

void JOAATUpdate(JOAAT_CTX *context, const unsigned char *input, unsigned int inputLen)
{
	context->state = joaat_buf((void *)input, inputLen, context->state);
}

void JOAATFinal(unsigned char digest[4], JOAAT_CTX * context)
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
    context->state = 0;
}

/*
 * joaat_buf - perform a Jenkins's one-at-a-time hash on a buffer
 *
 * input:
 *  buf - start of buffer to hash
 *  len - length of buffer in octets
 *
 * returns:
 *  32 bit hash as a static hash type
 */
static uint32_t
joaat_buf(void *buf, size_t len, uint32_t hval)
{
    size_t i;
    unsigned char *input = (unsigned char *)buf;

    for (i = 0; i < len; i++) {
        hval += input[i];
        hval += (hval << 10);
        hval ^= (hval >> 6);
    }

    hval += (hval << 3);
    hval ^= (hval >> 11);
    hval += (hval << 15);

    return hval;
}
