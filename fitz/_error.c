#include "mupdf/fitz.h"

#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _MSC_VER
#ifndef NDEBUG
#define USE_OUTPUT_DEBUG_STRING
#include <windows.h>
#endif
#endif

#ifdef __ANDROID__
#define USE_ANDROID_LOG
#include <android/log.h>
#endif

/* Warning context */

void fz_var_imp(void *var)
{
	/* Do nothing */
}

void fz_flush_warnings(fz_context *ctx)
{
	if (ctx->warn->count > 1)
	{
		fz_write_printf(ctx, fz_stderr(ctx), "warning: ... repeated %d times ...\n", ctx->warn->count);
	}
	ctx->warn->message[0] = 0;
	ctx->warn->count = 0;
}

void fz_vwarn(fz_context *ctx, const char *fmt, va_list ap)
{
	char buf[sizeof ctx->warn->message];

	fz_vsnprintf(buf, sizeof buf, fmt, ap);
	buf[sizeof(buf) - 1] = 0;
#ifdef USE_OUTPUT_DEBUG_STRING
	OutputDebugStringA(buf);
	OutputDebugStringA("\n");
#endif
#ifdef USE_ANDROID_LOG
	__android_log_print(ANDROID_LOG_WARN, "libmupdf", "%s", buf);
#endif

	if (!strcmp(buf, ctx->warn->message))
	{
		ctx->warn->count++;
	}
	else
	{
		fz_flush_warnings(ctx);
		fz_write_printf(ctx, fz_stderr(ctx), "warning: %s\n", buf);
		fz_strlcpy(ctx->warn->message, buf, sizeof ctx->warn->message);
		ctx->warn->count = 1;
	}
}

void fz_warn(fz_context *ctx, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	fz_vwarn(ctx, fmt, ap);
	va_end(ap);
}

/* Error context */

/* When we first setjmp, code is set to 0. Whenever we throw, we add 2 to
 * this code. Whenever we enter the always block, we add 1.
 *
 * fz_push_try sets code to 0.
 * If (fz_throw called within fz_try)
 *     fz_throw makes code = 2.
 *     If (no always block present)
 *         enter catch region with code = 2. OK.
 *     else
 *         fz_always entered as code < 3; Makes code = 3;
 *         if (fz_throw called within fz_always)
 *             fz_throw makes code = 5
 *             fz_always is not reentered.
 *             catch region entered with code = 5. OK.
 *         else
 *             catch region entered with code = 3. OK
 * else
 *     if (no always block present)
 *         catch region not entered as code = 0. OK.
 *     else
 *         fz_always entered as code < 3. makes code = 1
 *         if (fz_throw called within fz_always)
 *             fz_throw makes code = 3;
 *             fz_always NOT entered as code >= 3
 *             catch region entered with code = 3. OK.
 *         else
 *             catch region entered with code = 1.
 */

FZ_NORETURN static void throw(fz_context *ctx)
{
	if (ctx->error->top >= ctx->error->stack)
	{
		ctx->error->top->code += 2;
		fz_longjmp(ctx->error->top->buffer, 1);
	}
	else
	{
		fz_write_printf(ctx, fz_stderr(ctx), "uncaught error: %s\n", ctx->error->message);
#ifdef USE_OUTPUT_DEBUG_STRING
		OutputDebugStringA("uncaught error: ");
		OutputDebugStringA(ctx->error->message);
		OutputDebugStringA("\n");
#endif
#ifdef USE_ANDROID_LOG
		__android_log_print(ANDROID_LOG_ERROR, "libmupdf", "(uncaught) %s", ctx->error->message);
#endif
		exit(EXIT_FAILURE);
	}
}

/* Only called when we hit the bottom of the exception stack.
 * Do the same as fz_throw, but don't actually throw. */
static int fz_fake_throw(fz_context *ctx, int code, const char *fmt, ...)
{
	va_list args;
	ctx->error->errcode = code;
	va_start(args, fmt);
	fz_vsnprintf(ctx->error->message, sizeof ctx->error->message, fmt, args);
	ctx->error->message[sizeof(ctx->error->message) - 1] = 0;
	va_end(args);

	if (code != FZ_ERROR_ABORT)
	{
		fz_flush_warnings(ctx);
		fz_write_printf(ctx, fz_stderr(ctx), "error: %s\n", ctx->error->message);
#ifdef USE_OUTPUT_DEBUG_STRING
		OutputDebugStringA("error: ");
		OutputDebugStringA(ctx->error->message);
		OutputDebugStringA("\n");
#endif
#ifdef USE_ANDROID_LOG
		__android_log_print(ANDROID_LOG_ERROR, "libmupdf", "%s", ctx->error->message);
#endif
	}

	/* We need to arrive in the always/catch block as if throw
	 * had taken place. */
	ctx->error->top++;
	ctx->error->top->code = 2;
	return 0;
}

int fz_push_try(fz_context *ctx)
{
	/* If we would overflow the exception stack, throw an exception instead
	 * of entering the try block. We assume that we always have room for
	 * 1 extra level on the stack here - i.e. we throw the error on us
	 * starting to use the last level. */
	if (ctx->error->top + 2 >= ctx->error->stack + nelem(ctx->error->stack))
		return fz_fake_throw(ctx, FZ_ERROR_GENERIC, "exception stack overflow!");

	ctx->error->top++;
	ctx->error->top->code = 0;
	return 1;
}

int fz_caught(fz_context *ctx)
{
	assert(ctx && ctx->error && ctx->error->errcode >= FZ_ERROR_NONE);
	return ctx->error->errcode;
}

const char *fz_caught_message(fz_context *ctx)
{
	assert(ctx && ctx->error && ctx->error->errcode >= FZ_ERROR_NONE);
	return ctx->error->message;
}

FZ_NORETURN void fz_vthrow(fz_context *ctx, int code, const char *fmt, va_list ap)
{
	ctx->error->errcode = code;
	fz_vsnprintf(ctx->error->message, sizeof ctx->error->message, fmt, ap);
	ctx->error->message[sizeof(ctx->error->message) - 1] = 0;

	if (code != FZ_ERROR_ABORT)
	{
		fz_flush_warnings(ctx);
		fz_write_printf(ctx, fz_stderr(ctx), "error: %s\n", ctx->error->message);
#ifdef USE_OUTPUT_DEBUG_STRING
		OutputDebugStringA("error: ");
		OutputDebugStringA(ctx->error->message);
		OutputDebugStringA("\n");
#endif
#ifdef USE_ANDROID_LOG
		__android_log_print(ANDROID_LOG_ERROR, "libmupdf", "%s", ctx->error->message);
#endif
	}

	throw(ctx);
}

FZ_NORETURN void fz_throw(fz_context *ctx, int code, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	fz_vthrow(ctx, code, fmt, ap);
	va_end(ap);
}

FZ_NORETURN void fz_rethrow(fz_context *ctx)
{
	assert(ctx && ctx->error && ctx->error->errcode >= FZ_ERROR_NONE);
	throw(ctx);
}

void fz_rethrow_if(fz_context *ctx, int err)
{
	assert(ctx && ctx->error && ctx->error->errcode >= FZ_ERROR_NONE);
	if (ctx->error->errcode == err)
		fz_rethrow(ctx);
}
