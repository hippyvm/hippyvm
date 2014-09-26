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

/* $Id*/

#include <stdint.h>
#include <stddef.h>

typedef struct {
	uint32_t state;
} JOAAT_CTX;

void JOAATInit(JOAAT_CTX *context);
void JOAATUpdate(JOAAT_CTX *context, const unsigned char *input, unsigned int inputLen);
void JOAATFinal(unsigned char digest[16], JOAAT_CTX * context);

static uint32_t joaat_buf(void *buf, size_t len, uint32_t hval);
