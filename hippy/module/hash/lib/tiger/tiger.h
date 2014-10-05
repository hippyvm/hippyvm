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
#include <stddef.h>

typedef struct {
	uint64_t state[3];
	uint64_t passed;
	unsigned char buffer[64];
	unsigned int passes:1;
	unsigned int length:7;
} TIGER_CTX;

void TIGER3Init(TIGER_CTX *context);
void TIGER4Init(TIGER_CTX *context);
void TIGERUpdate(TIGER_CTX *context, const unsigned char *input, size_t len);
void TIGER128Final(unsigned char digest[16], TIGER_CTX *context);
void TIGER160Final(unsigned char digest[20], TIGER_CTX *context);
void TIGER192Final(unsigned char digest[24], TIGER_CTX *context);
