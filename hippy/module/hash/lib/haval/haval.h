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

#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* HAVAL context. */
typedef struct {
	uint32_t state[8];
	uint32_t count[2];
	unsigned char buffer[128];

	char passes;
	short output;
	void (*Transform)(uint32_t state[8], const unsigned char block[128]);
} HAVAL_CTX;

void HAVALUpdate(HAVAL_CTX *, const unsigned char *, unsigned int);

#define HASH_HAVAL_INIT_DECL(p,b)   void HAVAL##p##_##b##Init(HAVAL_CTX *); \
                                    void HAVAL##b##Final(unsigned char*, HAVAL_CTX *);


HASH_HAVAL_INIT_DECL(3,128)
HASH_HAVAL_INIT_DECL(3,160)
HASH_HAVAL_INIT_DECL(3,192)
HASH_HAVAL_INIT_DECL(3,224)
HASH_HAVAL_INIT_DECL(3,256)

HASH_HAVAL_INIT_DECL(4,128)
HASH_HAVAL_INIT_DECL(4,160)
HASH_HAVAL_INIT_DECL(4,192)
HASH_HAVAL_INIT_DECL(4,224)
HASH_HAVAL_INIT_DECL(4,256)

HASH_HAVAL_INIT_DECL(5,128)
HASH_HAVAL_INIT_DECL(5,160)
HASH_HAVAL_INIT_DECL(5,192)
HASH_HAVAL_INIT_DECL(5,224)
HASH_HAVAL_INIT_DECL(5,256)
