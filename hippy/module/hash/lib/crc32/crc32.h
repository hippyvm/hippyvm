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
	uint32_t state;
} CRC32_CTX;

void CRC32Init(CRC32_CTX *context);
void CRC32Update(CRC32_CTX *context, const unsigned char *input, size_t len);
void CRC32BUpdate(CRC32_CTX *context, const unsigned char *input, size_t len);
void CRC32Final(unsigned char digest[4], CRC32_CTX *context);
void CRC32BFinal(unsigned char digest[4], CRC32_CTX *context);
