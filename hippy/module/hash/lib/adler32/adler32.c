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
  | Authors: Michael Wallner <mike@php.net>                              |
  |          Sara Golemon <pollita@php.net>                              |
  +----------------------------------------------------------------------+
*/

/* $Id$ */

#include "adler32.h"

void ADLER32Init(ADLER32_CTX *context)
{
	context->state = 1;
}

void ADLER32Update(ADLER32_CTX *context, const unsigned char *input, size_t len)
{
	uint32_t i, s[2];

	s[0] = context->state & 0xffff;
	s[1] = (context->state >> 16) & 0xffff;
	for (i = 0; i < len; ++i) {
		s[0] += input[i];
		s[1] += s[0];
		if (s[1]>=0x7fffffff)
		{
			s[0] = s[0] % 65521;
			s[1] = s[1] % 65521;
		}
	}
	s[0] = s[0] % 65521;
	s[1] = s[1] % 65521;
	context->state = s[0] + (s[1] << 16);
}

void ADLER32Final(unsigned char digest[4], ADLER32_CTX *context)
{
	digest[0] = (unsigned char) ((context->state >> 24) & 0xff);
	digest[1] = (unsigned char) ((context->state >> 16) & 0xff);
	digest[2] = (unsigned char) ((context->state >> 8) & 0xff);
	digest[3] = (unsigned char) (context->state & 0xff);
	context->state = 0;
}
