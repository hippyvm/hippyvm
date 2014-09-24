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

#include <stdint.h>
#include <stddef.h>

#define FNV1_32_INIT ((uint32_t)0x811c9dc5)
#define FNV1_32A_INIT FNV1_32_INIT

#define FNV_32_PRIME ((uint32_t)0x01000193)

#define FNV1_64_INIT ((uint64_t)0xcbf29ce484222325ULL)
#define FNV1A_64_INIT FNV1_64_INIT

#define FNV_64_PRIME ((uint64_t)0x100000001b3ULL)


typedef struct {
	uint32_t state;
} FNV132_CTX;

typedef struct {
	uint64_t state;
} FNV164_CTX;


void FNV132Init(FNV132_CTX *context);
void FNV132Update(FNV132_CTX *context, const unsigned char *input, unsigned int inputLen);
void FNV1a32Update(FNV132_CTX *context, const unsigned char *input, unsigned int inputLen);
void FNV132Final(unsigned char digest[16], FNV132_CTX * context);

void FNV164Init(FNV164_CTX *context);
void FNV164Update(FNV164_CTX *context, const unsigned char *input, unsigned int inputLen);
void FNV1a64Update(FNV164_CTX *context, const unsigned char *input, unsigned int inputLen);
void FNV164Final(unsigned char digest[16], FNV164_CTX * context);

static uint32_t fnv_32_buf(void *buf, size_t len, uint32_t hval, int alternate);
static uint64_t fnv_64_buf(void *buf, size_t len, uint64_t hval, int alternate);
