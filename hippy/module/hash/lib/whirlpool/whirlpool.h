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
   | Author: Michael Wallner <mike@php.net>                               |
   +----------------------------------------------------------------------+
*/

#include <stdint.h>
#include <string.h>

/* WHIRLPOOL context */
typedef struct {
	uint64_t state[8];
	unsigned char bitlength[32];
	struct {
		int pos;
		int bits;
		unsigned char data[64];
	} buffer;
} WHIRLPOOL_CTX;

void WHIRLPOOLInit(WHIRLPOOL_CTX *);
void WHIRLPOOLUpdate(WHIRLPOOL_CTX *, const unsigned char *, size_t);
void WHIRLPOOLFinal(unsigned char[64], WHIRLPOOL_CTX *);
