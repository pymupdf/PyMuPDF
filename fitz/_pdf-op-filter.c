#include "mupdf/fitz.h"
#include "mupdf/pdf.h"

#include <string.h>

typedef struct filter_gstate_s filter_gstate;

typedef enum
{
	FLUSH_CTM = 1,
	FLUSH_COLOR_F = 2,
	FLUSH_COLOR_S = 4,
	FLUSH_TEXT = 8,

	FLUSH_ALL = 15,
	FLUSH_STROKE = 1+4,
	FLUSH_FILL = 1+2
} gstate_flush_flags;

typedef struct pdf_filter_gstate_s pdf_filter_gstate;

struct pdf_filter_gstate_s
{
	fz_matrix ctm;
	struct
	{
		char name[256];
		fz_colorspace *cs;
	} cs, CS;
	struct
	{
		char name[256];
		pdf_pattern *pat;
		fz_shade *shd;
		int n;
		float c[FZ_MAX_COLORS];
	} sc, SC;
	struct
	{
		fz_linecap linecap;
		fz_linejoin linejoin;
		float linewidth;
		float miterlimit;
	} stroke;
	pdf_text_state text;
};

struct filter_gstate_s
{
	filter_gstate *next;
	int pushed;
	pdf_filter_gstate pending;
	pdf_filter_gstate sent;
};

typedef struct pdf_filter_processor_s
{
	pdf_processor super;
	pdf_document *doc;
	pdf_processor *chain;
	filter_gstate *gstate;
	pdf_text_object_state tos;
	void *font_name;
	pdf_text_filter_fn *text_filter;
	pdf_after_text_object_fn *after_text;
	void *opaque;
	pdf_obj *old_rdb, *new_rdb;
} pdf_filter_processor;

static void
copy_resource(fz_context *ctx, pdf_filter_processor *p, pdf_obj *key, const char *name)
{
	pdf_obj *res, *obj;

	if (!name || name[0] == 0)
		return;

	res = pdf_dict_get(ctx, p->old_rdb, key);
	obj = pdf_dict_gets(ctx, res, name);
	if (obj)
	{
		res = pdf_dict_get(ctx, p->new_rdb, key);
		if (!res)
		{
			res = pdf_new_dict(ctx, pdf_get_bound_document(ctx, p->new_rdb), 1);
			pdf_dict_put_drop(ctx, p->new_rdb, key, res);
		}
		pdf_dict_putp(ctx, res, name, obj);
	}
}

static void
filter_push(fz_context *ctx, pdf_filter_processor *p)
{
	filter_gstate *gstate = p->gstate;
	filter_gstate *new_gstate = fz_malloc_struct(ctx, filter_gstate);
	*new_gstate = *gstate;
	new_gstate->pushed = 0;
	new_gstate->next = gstate;
	p->gstate = new_gstate;

	pdf_keep_font(ctx, new_gstate->pending.text.font);
	pdf_keep_font(ctx, new_gstate->sent.text.font);
}

static int
filter_pop(fz_context *ctx, pdf_filter_processor *p)
{
	filter_gstate *gstate = p->gstate;
	filter_gstate *old = gstate->next;

	/* We are at the top, so nothing to pop! */
	if (old == NULL)
		return 1;

	if (gstate->pushed)
		if (p->chain->op_Q)
			p->chain->op_Q(ctx, p->chain);

	pdf_drop_font(ctx, gstate->pending.text.font);
	pdf_drop_font(ctx, gstate->sent.text.font);
	fz_free(ctx, gstate);
	p->gstate = old;
	return 0;
}

/* We never allow the topmost gstate to be changed. This allows us
 * to pop back to the zeroth level and be sure that our gstate is
 * sane. This is important for being able to add new operators at
 * the end of pages in a sane way. */
static filter_gstate *
gstate_to_update(fz_context *ctx, pdf_filter_processor *p)
{
	filter_gstate *gstate = p->gstate;

	/* If we're not the top, that's fine */
	if (gstate->next != NULL)
		return gstate;

	/* We are the top. Push a group, so we're not */
	filter_push(ctx, p);
	gstate = p->gstate;
	gstate->pushed = 1;
	if (p->chain->op_q)
		p->chain->op_q(ctx, p->chain);

	return p->gstate;
}

static void filter_flush(fz_context *ctx, pdf_filter_processor *p, int flush)
{
	filter_gstate *gstate = gstate_to_update(ctx, p);
	int i;

	if (gstate->pushed == 0)
	{
		gstate->pushed = 1;
		if (p->chain->op_q)
			p->chain->op_q(ctx, p->chain);
	}

	if (flush & FLUSH_CTM)
	{
		if (gstate->pending.ctm.a != 1 || gstate->pending.ctm.b != 0 ||
			gstate->pending.ctm.c != 0 || gstate->pending.ctm.d != 1 ||
			gstate->pending.ctm.e != 0 || gstate->pending.ctm.f != 0)
		{
			fz_matrix current = gstate->sent.ctm;

			if (p->chain->op_cm)
				p->chain->op_cm(ctx, p->chain,
					gstate->pending.ctm.a,
					gstate->pending.ctm.b,
					gstate->pending.ctm.c,
					gstate->pending.ctm.d,
					gstate->pending.ctm.e,
					gstate->pending.ctm.f);

			fz_concat(&gstate->sent.ctm, &current, &gstate->pending.ctm);
			gstate->pending.ctm.a = 1;
			gstate->pending.ctm.b = 0;
			gstate->pending.ctm.c = 0;
			gstate->pending.ctm.d = 1;
			gstate->pending.ctm.e = 0;
			gstate->pending.ctm.f = 0;
		}
	}

	if (flush & FLUSH_COLOR_F)
	{
		if (gstate->pending.cs.cs == fz_device_gray(ctx) && !gstate->pending.sc.pat && !gstate->pending.sc.shd && gstate->pending.sc.n == 1 &&
			(gstate->sent.cs.cs != fz_device_gray(ctx) || gstate->sent.sc.pat || gstate->sent.sc.shd || gstate->sent.sc.n != 0 || gstate->pending.sc.c[0] != gstate->sent.sc.c[0]))
		{
			if (p->chain->op_g)
				p->chain->op_g(ctx, p->chain, gstate->pending.sc.c[0]);
			goto done_sc;
		}
		if (gstate->pending.cs.cs == fz_device_rgb(ctx) && !gstate->pending.sc.pat && !gstate->pending.sc.shd && gstate->pending.sc.n == 3 &&
			(gstate->sent.cs.cs != fz_device_rgb(ctx) || gstate->sent.sc.pat || gstate->sent.sc.shd || gstate->sent.sc.n != 3 || gstate->pending.sc.c[0] != gstate->sent.sc.c[0] ||
				gstate->pending.sc.c[1] != gstate->sent.sc.c[1] || gstate->pending.sc.c[1] != gstate->sent.sc.c[1]))
		{
			if (p->chain->op_rg)
				p->chain->op_rg(ctx, p->chain, gstate->pending.sc.c[0], gstate->pending.sc.c[1], gstate->pending.sc.c[2]);
			goto done_sc;
		}
		if (gstate->pending.cs.cs == fz_device_cmyk(ctx) && !gstate->pending.sc.pat && !gstate->pending.sc.shd && gstate->pending.sc.n == 4 &&
			(gstate->sent.cs.cs != fz_device_cmyk(ctx) || gstate->sent.sc.pat || gstate->sent.sc.shd || gstate->pending.sc.n != 4 || gstate->pending.sc.c[0] != gstate->sent.sc.c[0] ||
				gstate->pending.sc.c[1] != gstate->sent.sc.c[1] || gstate->pending.sc.c[2] != gstate->sent.sc.c[2] || gstate->pending.sc.c[3] != gstate->sent.sc.c[3]))
		{
			if (p->chain->op_k)
				p->chain->op_k(ctx, p->chain, gstate->pending.sc.c[0], gstate->pending.sc.c[1], gstate->pending.sc.c[2], gstate->pending.sc.c[3]);
			goto done_sc;
		}

		if (strcmp(gstate->pending.cs.name, gstate->sent.cs.name))
		{
			if (p->chain->op_cs)
				p->chain->op_cs(ctx, p->chain, gstate->pending.cs.name, gstate->pending.cs.cs);
		}

		/* pattern or shading */
		if (gstate->pending.sc.name[0])
		{
			int emit = 0;
			if (strcmp(gstate->pending.sc.name, gstate->sent.sc.name))
				emit = 1;
			if (gstate->pending.sc.n != gstate->sent.sc.n)
				emit = 1;
			else
				for (i = 0; i < gstate->pending.sc.n; ++i)
					if (gstate->pending.sc.c[i] != gstate->sent.sc.c[i])
						emit = 1;
			if (emit)
			{
				if (gstate->pending.sc.pat)
					if (p->chain->op_sc_pattern)
						p->chain->op_sc_pattern(ctx, p->chain, gstate->pending.sc.name, gstate->pending.sc.pat, gstate->pending.sc.n, gstate->pending.sc.c);
				if (gstate->pending.sc.shd)
					if (p->chain->op_sc_shade)
						p->chain->op_sc_shade(ctx, p->chain, gstate->pending.sc.name, gstate->pending.sc.shd);
			}
		}

		/* plain color */
		else
		{
			int emit = 0;
			if (gstate->pending.sc.n != gstate->sent.sc.n)
				emit = 1;
			else
				for (i = 0; i < gstate->pending.sc.n; ++i)
					if (gstate->pending.sc.c[i] != gstate->sent.sc.c[i])
						emit = 1;
			if (emit)
			{
				if (p->chain->op_sc_color)
					p->chain->op_sc_color(ctx, p->chain, gstate->pending.sc.n, gstate->pending.sc.c);
			}
		}

done_sc:
		gstate->sent.cs = gstate->pending.cs;
		gstate->sent.sc = gstate->pending.sc;
	}

	if (flush & FLUSH_COLOR_S)
	{
		if (gstate->pending.CS.cs == fz_device_gray(ctx) && !gstate->pending.SC.pat && !gstate->pending.SC.shd && gstate->pending.SC.n == 1 &&
			(gstate->sent.CS.cs != fz_device_gray(ctx) || gstate->sent.SC.pat || gstate->sent.SC.shd || gstate->sent.SC.n != 0 || gstate->pending.SC.c[0] != gstate->sent.SC.c[0]))
		{
			if (p->chain->op_G)
				p->chain->op_G(ctx, p->chain, gstate->pending.SC.c[0]);
			goto done_SC;
		}
		if (gstate->pending.CS.cs == fz_device_rgb(ctx) && !gstate->pending.SC.pat && !gstate->pending.SC.shd && gstate->pending.SC.n == 3 &&
			(gstate->sent.CS.cs != fz_device_rgb(ctx) || gstate->sent.SC.pat || gstate->sent.SC.shd || gstate->sent.SC.n != 3 || gstate->pending.SC.c[0] != gstate->sent.SC.c[0] ||
				gstate->pending.SC.c[1] != gstate->sent.SC.c[1] || gstate->pending.SC.c[1] != gstate->sent.SC.c[1]))
		{
			if (p->chain->op_RG)
				p->chain->op_RG(ctx, p->chain, gstate->pending.SC.c[0], gstate->pending.SC.c[1], gstate->pending.SC.c[2]);
			goto done_SC;
		}
		if (gstate->pending.CS.cs == fz_device_cmyk(ctx) && !gstate->pending.SC.pat && !gstate->pending.SC.shd && gstate->pending.SC.n == 4 &&
			(gstate->sent.CS.cs != fz_device_cmyk(ctx) || gstate->sent.SC.pat || gstate->sent.SC.shd || gstate->pending.SC.n != 4 || gstate->pending.SC.c[0] != gstate->sent.SC.c[0] ||
				gstate->pending.SC.c[1] != gstate->sent.SC.c[1] || gstate->pending.SC.c[2] != gstate->sent.SC.c[2] || gstate->pending.SC.c[3] != gstate->sent.SC.c[3]))
		{
			if (p->chain->op_K)
				p->chain->op_K(ctx, p->chain, gstate->pending.SC.c[0], gstate->pending.SC.c[1], gstate->pending.SC.c[2], gstate->pending.SC.c[3]);
			goto done_SC;
		}

		if (strcmp(gstate->pending.CS.name, gstate->sent.CS.name))
		{
			if (p->chain->op_CS)
				p->chain->op_CS(ctx, p->chain, gstate->pending.CS.name, gstate->pending.CS.cs);
		}

		/* pattern or shading */
		if (gstate->pending.SC.name[0])
		{
			int emit = 0;
			if (strcmp(gstate->pending.SC.name, gstate->sent.SC.name))
				emit = 1;
			if (gstate->pending.SC.n != gstate->sent.SC.n)
				emit = 1;
			else
				for (i = 0; i < gstate->pending.SC.n; ++i)
					if (gstate->pending.SC.c[i] != gstate->sent.SC.c[i])
						emit = 1;
			if (emit)
			{
				if (gstate->pending.SC.pat)
					if (p->chain->op_SC_pattern)
						p->chain->op_SC_pattern(ctx, p->chain, gstate->pending.SC.name, gstate->pending.SC.pat, gstate->pending.SC.n, gstate->pending.SC.c);
				if (gstate->pending.SC.shd)
					if (p->chain->op_SC_shade)
						p->chain->op_SC_shade(ctx, p->chain, gstate->pending.SC.name, gstate->pending.SC.shd);
			}
		}

		/* plain color */
		else
		{
			int emit = 0;
			if (gstate->pending.SC.n != gstate->sent.SC.n)
				emit = 1;
			else
				for (i = 0; i < gstate->pending.SC.n; ++i)
					if (gstate->pending.SC.c[i] != gstate->sent.SC.c[i])
						emit = 1;
			if (emit)
			{
				if (p->chain->op_SC_color)
					p->chain->op_SC_color(ctx, p->chain, gstate->pending.SC.n, gstate->pending.SC.c);
			}
		}

done_SC:
		gstate->sent.CS = gstate->pending.CS;
		gstate->sent.SC = gstate->pending.SC;
	}

	if (flush & FLUSH_STROKE)
	{
		if (gstate->pending.stroke.linecap != gstate->sent.stroke.linecap)
		{
			if (p->chain->op_J)
				p->chain->op_J(ctx, p->chain, gstate->pending.stroke.linecap);
		}
		if (gstate->pending.stroke.linejoin != gstate->sent.stroke.linejoin)
		{
			if (p->chain->op_j)
				p->chain->op_j(ctx, p->chain, gstate->pending.stroke.linejoin);
		}
		if (gstate->pending.stroke.linewidth != gstate->sent.stroke.linewidth)
		{
			if (p->chain->op_w)
				p->chain->op_w(ctx, p->chain, gstate->pending.stroke.linewidth);
		}
		if (gstate->pending.stroke.miterlimit != gstate->sent.stroke.miterlimit)
		{
			if (p->chain->op_M)
				p->chain->op_M(ctx, p->chain, gstate->pending.stroke.miterlimit);
		}
		gstate->sent.stroke = gstate->pending.stroke;
	}

	if (flush & FLUSH_TEXT)
	{
		if (gstate->pending.text.char_space != gstate->sent.text.char_space)
		{
			if (p->chain->op_Tc)
				p->chain->op_Tc(ctx, p->chain, gstate->pending.text.char_space);
		}
		if (gstate->pending.text.word_space != gstate->sent.text.word_space)
		{
			if (p->chain->op_Tw)
				p->chain->op_Tw(ctx, p->chain, gstate->pending.text.word_space);
		}
		if (gstate->pending.text.scale != gstate->sent.text.scale)
		{
			if (p->chain->op_Tz)
				p->chain->op_Tz(ctx, p->chain, gstate->pending.text.scale);
		}
		if (gstate->pending.text.leading != gstate->sent.text.leading)
		{
			if (p->chain->op_TL)
				p->chain->op_TL(ctx, p->chain, gstate->pending.text.leading);
		}
		if (gstate->pending.text.font != gstate->sent.text.font ||
			gstate->pending.text.size != gstate->sent.text.size)
		{
			if (p->chain->op_Tf)
				p->chain->op_Tf(ctx, p->chain, p->font_name, gstate->pending.text.font, gstate->pending.text.size);
		}
		if (gstate->pending.text.render != gstate->sent.text.render)
		{
			if (p->chain->op_Tr)
				p->chain->op_Tr(ctx, p->chain, gstate->pending.text.render);
		}
		if (gstate->pending.text.rise != gstate->sent.text.rise)
		{
			if (p->chain->op_Ts)
				p->chain->op_Ts(ctx, p->chain, gstate->pending.text.rise);
		}
		pdf_drop_font(ctx, gstate->sent.text.font);
		gstate->sent.text = gstate->pending.text; // <=== fix 699368
		gstate->sent.text.font = pdf_keep_font(ctx, gstate->pending.text.font);
	}
}

static int
filter_show_char(fz_context *ctx, pdf_filter_processor *p, int cid)
{
	filter_gstate *gstate = p->gstate;
	pdf_font_desc *fontdesc = gstate->pending.text.font;
	fz_matrix trm;
	int ucsbuf[8];
	int ucslen;
	int remove = 0;

	(void)pdf_tos_make_trm(ctx, &p->tos, &gstate->pending.text, fontdesc, cid, &trm);

	ucslen = 0;
	if (fontdesc->to_unicode)
		ucslen = pdf_lookup_cmap_full(fontdesc->to_unicode, cid, ucsbuf);
	if (ucslen == 0 && (size_t)cid < fontdesc->cid_to_ucs_len)
	{
		ucsbuf[0] = fontdesc->cid_to_ucs[cid];
		ucslen = 1;
	}
	if (ucslen == 0 || (ucslen == 1 && ucsbuf[0] == 0))
	{
		ucsbuf[0] = FZ_REPLACEMENT_CHARACTER;
		ucslen = 1;
	}

	if (p->text_filter)
		remove = p->text_filter(ctx, p->opaque, ucsbuf, ucslen, &trm, &p->tos.char_bbox);

	pdf_tos_move_after_char(ctx, &p->tos);

	return remove;
}

static void
filter_show_space(fz_context *ctx, pdf_filter_processor *p, float tadj)
{
	filter_gstate *gstate = p->gstate;
	pdf_font_desc *fontdesc = gstate->pending.text.font;

	if (fontdesc->wmode == 0)
		fz_pre_translate(&p->tos.tm, tadj * gstate->pending.text.scale, 0);
	else
		fz_pre_translate(&p->tos.tm, 0, tadj);
}

/* Process a string (from buf, of length len), from position *pos onwards.
 * Stop when we hit the end, or when we find a character to remove. The
 * caller will restart us again later. On exit, *pos = the point we got to,
 * *inc = The number of bytes to skip to step over the next character (unless
 * we hit the end).
 */
static void
filter_string_to_segment(fz_context *ctx, pdf_filter_processor *p, unsigned char *buf, int len, int *pos, int *inc)
{
	filter_gstate *gstate = p->gstate;
	pdf_font_desc *fontdesc = gstate->pending.text.font;
	unsigned char *end = buf + len;
	unsigned int cpt;
	int cid;
	int remove;

	buf += *pos;

	while (buf < end)
	{
		*inc = pdf_decode_cmap(fontdesc->encoding, buf, end, &cpt);
		buf += *inc;

		cid = pdf_lookup_cmap(fontdesc->encoding, cpt);
		if (cid < 0)
		{
			fz_warn(ctx, "cannot encode character");
		}
		else
			remove = filter_show_char(ctx, p, cid);
		if (cpt == 32 && *inc == 1)
			filter_show_space(ctx, p, gstate->pending.text.word_space);
		if (remove)
			return;
		*pos += *inc;
	}
}

static void
send_adjustment(fz_context *ctx, pdf_filter_processor *p, fz_point skip)
{
	pdf_obj *arr = pdf_new_array(ctx, p->doc, 1);
	pdf_obj *skip_obj = NULL;

	fz_var(skip_obj);

	fz_try(ctx)
	{
		float skip_dist = p->tos.fontdesc->wmode == 1 ? -skip.y : -skip.x;
		skip_dist = skip_dist / p->gstate->pending.text.size;
		skip_obj = pdf_new_real(ctx, p->doc, skip_dist * 1000);

		pdf_array_insert(ctx, arr, skip_obj, 0);

		if (p->chain->op_TJ)
			p->chain->op_TJ(ctx, p->chain, arr);
	}
	fz_always(ctx)
	{
		pdf_drop_obj(ctx, arr);
		pdf_drop_obj(ctx, skip_obj);
	}
	fz_catch(ctx)
		fz_rethrow(ctx);
}

static void
filter_show_string(fz_context *ctx, pdf_filter_processor *p, unsigned char *buf, int len)
{
	filter_gstate *gstate = p->gstate;
	pdf_font_desc *fontdesc = gstate->pending.text.font;
	int i, inc;
	fz_point skip = { 0, 0 };

	if (!fontdesc)
		return;

	i = 0;
	while (i < len)
	{
		int start = i;
		filter_string_to_segment(ctx, p, buf, len, &i, &inc);
		if (start != i)
		{
			/* We have *some* chars to send at least */
			if (skip.x != 0 || skip.y != 0)
			{
				send_adjustment(ctx, p, skip);
				skip.x = skip.y = 0;
			}
			if (p->chain->op_Tj && start != i)
				p->chain->op_Tj(ctx, p->chain, (char *)buf+start, i-start);
		}
		if (i != len)
		{
			skip.x += p->tos.char_tx;
			skip.y += p->tos.char_ty;
			i += inc;
		}
	}
	if (skip.x != 0 || skip.y != 0)
		send_adjustment(ctx, p, skip);
}

static float
adjustment(fz_context *ctx, pdf_filter_processor *p, fz_point skip)
{
	float skip_dist = p->tos.fontdesc->wmode == 1 ? -skip.y : -skip.x;
	skip_dist = skip_dist / p->gstate->pending.text.size;
	return skip_dist * 1000;
}


static void
filter_show_text(fz_context *ctx, pdf_filter_processor *p, pdf_obj *text)
{
	filter_gstate *gstate = p->gstate;
	pdf_font_desc *fontdesc = gstate->pending.text.font;
	int i, n;
	fz_point skip;
	pdf_obj *new_arr;
	pdf_document *doc;

	if (!fontdesc)
		return;

	if (pdf_is_string(ctx, text))
	{
		filter_show_string(ctx, p, (unsigned char *)pdf_to_str_buf(ctx, text), pdf_to_str_len(ctx, text));
		return;
	}
	if (!pdf_is_array(ctx, text))
		return;

	p->tos.fontdesc = fontdesc;
	n = pdf_array_len(ctx, text);
	skip.x = skip.y = 0;
	doc = pdf_get_bound_document(ctx, text);
	new_arr = pdf_new_array(ctx, doc, 4);
	fz_try(ctx)
	{
		for (i = 0; i < n; i++)
		{
			pdf_obj *item = pdf_array_get(ctx, text, i);
			if (pdf_is_string(ctx, item))
			{
				unsigned char *buf = (unsigned char *)pdf_to_str_buf(ctx, item);
				int len = pdf_to_str_len(ctx, item);
				int j = 0;
				while (j < len)
				{
					int inc;
					int start = j;
					filter_string_to_segment(ctx, p, buf, len, &j, &inc);
					if (start != j)
					{
						/* We have *some* chars to send at least */
						if (skip.x != 0 || skip.y != 0)
						{
							pdf_array_push_real(ctx, new_arr, adjustment(ctx, p, skip));
							skip.x = skip.y = 0;
						}
						pdf_array_push_string(ctx, new_arr, (char *)buf+start, j-start);
					}
					if (j != len)
					{
						skip.x += p->tos.char_tx;
						skip.y += p->tos.char_ty;
						j += inc;
					}
				}
			}
			else
			{
				float tadj = - pdf_to_real(ctx, item) * gstate->pending.text.size * 0.001f;
				if (fontdesc->wmode == 0)
				{
					skip.x += tadj;
					fz_pre_translate(&p->tos.tm, tadj * p->gstate->pending.text.scale, 0);
				}
				else
				{
					skip.y += tadj;
					fz_pre_translate(&p->tos.tm, 0, tadj);
				}

			}
		}
		if (skip.x != 0 || skip.y != 0)
			pdf_array_push_real(ctx, new_arr, adjustment(ctx, p, skip));
		if (p->chain->op_TJ && pdf_array_len(ctx, new_arr))
			p->chain->op_TJ(ctx, p->chain, new_arr);
	}
	fz_always(ctx)
		pdf_drop_obj(ctx, new_arr);
	fz_catch(ctx)
		fz_rethrow(ctx);
}

/* general graphics state */

static void
pdf_filter_w(fz_context *ctx, pdf_processor *proc, float linewidth)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	gstate->pending.stroke.linewidth = linewidth;
}

static void
pdf_filter_j(fz_context *ctx, pdf_processor *proc, int linejoin)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	gstate->pending.stroke.linejoin = linejoin;
}

static void
pdf_filter_J(fz_context *ctx, pdf_processor *proc, int linecap)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	gstate->pending.stroke.linecap = linecap;
}

static void
pdf_filter_M(fz_context *ctx, pdf_processor *proc, float miterlimit)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	gstate->pending.stroke.miterlimit = miterlimit;
}

static void
pdf_filter_d(fz_context *ctx, pdf_processor *proc, pdf_obj *array, float phase)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_d)
		p->chain->op_d(ctx, p->chain, array, phase);
}

static void
pdf_filter_ri(fz_context *ctx, pdf_processor *proc, const char *intent)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_ri)
		p->chain->op_ri(ctx, p->chain, intent);
}

static void
pdf_filter_gs_OP(fz_context *ctx, pdf_processor *proc, int b)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_gs_OP)
		p->chain->op_gs_OP(ctx, p->chain, b);
}

static void
pdf_filter_gs_op(fz_context *ctx, pdf_processor *proc, int b)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_gs_op)
		p->chain->op_gs_op(ctx, p->chain, b);
}

static void
pdf_filter_gs_OPM(fz_context *ctx, pdf_processor *proc, int i)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_gs_OPM)
		p->chain->op_gs_OPM(ctx, p->chain, i);
}

static void
pdf_filter_gs_UseBlackPtComp(fz_context *ctx, pdf_processor *proc, pdf_obj *name)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_gs_UseBlackPtComp)
		p->chain->op_gs_UseBlackPtComp(ctx, p->chain, name);
}

static void
pdf_filter_i(fz_context *ctx, pdf_processor *proc, float flatness)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_i)
		p->chain->op_i(ctx, p->chain, flatness);
}

static void
pdf_filter_gs_begin(fz_context *ctx, pdf_processor *proc, const char *name, pdf_obj *extgstate)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_gs_begin)
		p->chain->op_gs_begin(ctx, p->chain, name, extgstate);
	copy_resource(ctx, p, PDF_NAME_ExtGState, name);
}

static void
pdf_filter_gs_BM(fz_context *ctx, pdf_processor *proc, const char *blendmode)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	if (p->chain->op_gs_BM)
		p->chain->op_gs_BM(ctx, p->chain, blendmode);
}

static void
pdf_filter_gs_CA(fz_context *ctx, pdf_processor *proc, float alpha)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	if (p->chain->op_gs_CA)
		p->chain->op_gs_CA(ctx, p->chain, alpha);
}

static void
pdf_filter_gs_ca(fz_context *ctx, pdf_processor *proc, float alpha)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	if (p->chain->op_gs_ca)
		p->chain->op_gs_ca(ctx, p->chain, alpha);
}

static void
pdf_filter_gs_SMask(fz_context *ctx, pdf_processor *proc, pdf_obj *smask, pdf_obj *page_resources, float *bc, int luminosity)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	if (p->chain->op_gs_SMask)
		p->chain->op_gs_SMask(ctx, p->chain, smask, page_resources, bc, luminosity);
}

static void
pdf_filter_gs_end(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	if (p->chain->op_gs_end)
		p->chain->op_gs_end(ctx, p->chain);
}

/* special graphics state */

static void
pdf_filter_q(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_push(ctx, p);
}

static void
pdf_filter_Q(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_pop(ctx, p);
}

static void
pdf_filter_cm(fz_context *ctx, pdf_processor *proc, float a, float b, float c, float d, float e, float f)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	fz_matrix old, ctm;

	/* If we're being given an identity matrix, don't bother sending it */
	if (a == 1 && b == 0 && c == 0 && d == 1 && e == 0 && f == 0)
		return;

	ctm.a = a;
	ctm.b = b;
	ctm.c = c;
	ctm.d = d;
	ctm.e = e;
	ctm.f = f;

	old = gstate->pending.ctm;
	fz_concat(&gstate->pending.ctm, &ctm, &old);
}

/* path construction */

static void
pdf_filter_m(fz_context *ctx, pdf_processor *proc, float x, float y)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_m)
		p->chain->op_m(ctx, p->chain, x, y);
}

static void
pdf_filter_l(fz_context *ctx, pdf_processor *proc, float x, float y)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_l)
		p->chain->op_l(ctx, p->chain, x, y);
}

static void
pdf_filter_c(fz_context *ctx, pdf_processor *proc, float x1, float y1, float x2, float y2, float x3, float y3)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_c)
		p->chain->op_c(ctx, p->chain, x1, y1, x2, y2, x3, y3);
}

static void
pdf_filter_v(fz_context *ctx, pdf_processor *proc, float x2, float y2, float x3, float y3)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_v)
		p->chain->op_v(ctx, p->chain, x2, y2, x3, y3);
}

static void
pdf_filter_y(fz_context *ctx, pdf_processor *proc, float x1, float y1, float x3, float y3)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_y)
		p->chain->op_y(ctx, p->chain, x1, y1, x3, y3);
}

static void
pdf_filter_h(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_h)
		p->chain->op_h(ctx, p->chain);
}

static void
pdf_filter_re(fz_context *ctx, pdf_processor *proc, float x, float y, float w, float h)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_re)
		p->chain->op_re(ctx, p->chain, x, y, w, h);
}

/* path painting */

static void
pdf_filter_S(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_STROKE);
	if (p->chain->op_S)
		p->chain->op_S(ctx, p->chain);
}

static void
pdf_filter_s(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_STROKE);
	if (p->chain->op_s)
		p->chain->op_s(ctx, p->chain);
}

static void
pdf_filter_F(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_FILL);
	if (p->chain->op_F)
		p->chain->op_F(ctx, p->chain);
}

static void
pdf_filter_f(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_FILL);
	if (p->chain->op_f)
		p->chain->op_f(ctx, p->chain);
}

static void
pdf_filter_fstar(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_FILL);
	if (p->chain->op_fstar)
		p->chain->op_fstar(ctx, p->chain);
}

static void
pdf_filter_B(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_B)
		p->chain->op_B(ctx, p->chain);
}

static void
pdf_filter_Bstar(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_Bstar)
		p->chain->op_Bstar(ctx, p->chain);
}

static void
pdf_filter_b(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_b)
		p->chain->op_b(ctx, p->chain);
}

static void
pdf_filter_bstar(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_bstar)
		p->chain->op_bstar(ctx, p->chain);
}

static void
pdf_filter_n(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_n)
		p->chain->op_n(ctx, p->chain);
}

/* clipping paths */

static void
pdf_filter_W(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_W)
		p->chain->op_W(ctx, p->chain);
}

static void
pdf_filter_Wstar(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_CTM);
	if (p->chain->op_Wstar)
		p->chain->op_Wstar(ctx, p->chain);
}

/* text objects */

static void
pdf_filter_BT(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->tos.tm = fz_identity;
	p->tos.tlm = fz_identity;
	if (p->chain->op_BT)
		p->chain->op_BT(ctx, p->chain);
}

static void
pdf_filter_ET(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_ET)
		p->chain->op_ET(ctx, p->chain);
	if (p->after_text)
	{
		fz_matrix ctm;

		fz_concat(&ctm, &p->gstate->sent.ctm, &p->gstate->pending.ctm);
		if (p->chain->op_q)
			p->chain->op_q(ctx, p->chain);
		p->after_text(ctx, p->opaque, p->doc, p->chain, &ctm);
		if (p->chain->op_Q)
			p->chain->op_Q(ctx, p->chain);
	}
}

/* text state */

static void
pdf_filter_Tc(fz_context *ctx, pdf_processor *proc, float charspace)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->gstate->pending.text.char_space = charspace;
}

static void
pdf_filter_Tw(fz_context *ctx, pdf_processor *proc, float wordspace)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->gstate->pending.text.word_space = wordspace;
}

static void
pdf_filter_Tz(fz_context *ctx, pdf_processor *proc, float scale)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->gstate->pending.text.scale = scale / 100;
}

static void
pdf_filter_TL(fz_context *ctx, pdf_processor *proc, float leading)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->gstate->pending.text.leading = leading;
}

static void
pdf_filter_Tf(fz_context *ctx, pdf_processor *proc, const char *name, pdf_font_desc *font, float size)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	fz_free(ctx, p->font_name);
	p->font_name = NULL;
	p->font_name = name ? fz_strdup(ctx, name) : NULL;
	pdf_drop_font(ctx, p->gstate->pending.text.font);
	p->gstate->pending.text.font = pdf_keep_font(ctx, font);
	p->gstate->pending.text.size = size;
	copy_resource(ctx, p, PDF_NAME_Font, name);
}

static void
pdf_filter_Tr(fz_context *ctx, pdf_processor *proc, int render)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->gstate->pending.text.render = render;
}

static void
pdf_filter_Ts(fz_context *ctx, pdf_processor *proc, float rise)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	p->gstate->pending.text.rise = rise;
}

/* text positioning */

static void
pdf_filter_Td(fz_context *ctx, pdf_processor *proc, float tx, float ty)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	pdf_tos_translate(&p->tos, tx, ty);
	if (p->chain->op_Td)
		p->chain->op_Td(ctx, p->chain, tx, ty);
}

static void
pdf_filter_TD(fz_context *ctx, pdf_processor *proc, float tx, float ty)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	p->gstate->pending.text.leading = -ty;
	pdf_tos_translate(&p->tos, tx, ty);
	if (p->chain->op_TD)
		p->chain->op_TD(ctx, p->chain, tx, ty);
}

static void
pdf_filter_Tm(fz_context *ctx, pdf_processor *proc, float a, float b, float c, float d, float e, float f)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	pdf_tos_set_matrix(&p->tos, a, b, c, d, e, f);
	if (p->chain->op_Tm)
		p->chain->op_Tm(ctx, p->chain, a, b, c, d, e, f);
}

static void
pdf_filter_Tstar(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	pdf_tos_newline(&p->tos, p->gstate->pending.text.leading);
	if (p->chain->op_Tstar)
		p->chain->op_Tstar(ctx, p->chain);
}

/* text showing */

static void
pdf_filter_TJ(fz_context *ctx, pdf_processor *proc, pdf_obj *array)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	filter_show_text(ctx, p, array);
}

static void
pdf_filter_Tj(fz_context *ctx, pdf_processor *proc, char *str, int len)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	filter_show_string(ctx, p, (unsigned char *)str, len);
}

static void
pdf_filter_squote(fz_context *ctx, pdf_processor *proc, char *str, int len)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	pdf_tos_newline(&p->tos, p->gstate->pending.text.leading);
	if (p->chain->op_Tstar)
		p->chain->op_Tstar(ctx, p->chain);
	filter_show_string(ctx, p, (unsigned char *)str, len);
}

static void
pdf_filter_dquote(fz_context *ctx, pdf_processor *proc, float aw, float ac, char *str, int len)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	p->gstate->pending.text.word_space = aw;
	p->gstate->pending.text.char_space = ac;
	filter_flush(ctx, p, FLUSH_ALL);
	pdf_tos_newline(&p->tos, p->gstate->pending.text.leading);
	if (p->chain->op_Tstar)
		p->chain->op_Tstar(ctx, p->chain);
	filter_show_string(ctx, p, (unsigned char*)str, len);
}

/* type 3 fonts */

static void
pdf_filter_d0(fz_context *ctx, pdf_processor *proc, float wx, float wy)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_d0)
		p->chain->op_d0(ctx, p->chain, wx, wy);
}

static void
pdf_filter_d1(fz_context *ctx, pdf_processor *proc, float wx, float wy, float llx, float lly, float urx, float ury)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_d1)
		p->chain->op_d1(ctx, p->chain, wx, wy, llx, lly, urx, ury);
}

/* color */

static void
pdf_filter_CS(fz_context *ctx, pdf_processor *proc, const char *name, fz_colorspace *cs)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	fz_strlcpy(gstate->pending.CS.name, name, sizeof gstate->pending.CS.name);
	gstate->pending.CS.cs = cs;
	copy_resource(ctx, p, PDF_NAME_ColorSpace, name);
}

static void
pdf_filter_cs(fz_context *ctx, pdf_processor *proc, const char *name, fz_colorspace *cs)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	fz_strlcpy(gstate->pending.cs.name, name, sizeof gstate->pending.cs.name);
	gstate->pending.cs.cs = cs;
	copy_resource(ctx, p, PDF_NAME_ColorSpace, name);
}

static void
pdf_filter_SC_pattern(fz_context *ctx, pdf_processor *proc, const char *name, pdf_pattern *pat, int n, float *color)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	int i;
	fz_strlcpy(gstate->pending.SC.name, name, sizeof gstate->pending.SC.name);
	gstate->pending.SC.pat = pat;
	gstate->pending.SC.shd = NULL;
	gstate->pending.SC.n = n;
	for (i = 0; i < n; ++i)
		gstate->pending.SC.c[i] = color[i];
	copy_resource(ctx, p, PDF_NAME_Pattern, name);
}

static void
pdf_filter_sc_pattern(fz_context *ctx, pdf_processor *proc, const char *name, pdf_pattern *pat, int n, float *color)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	int i;
	fz_strlcpy(gstate->pending.sc.name, name, sizeof gstate->pending.sc.name);
	gstate->pending.sc.pat = pat;
	gstate->pending.sc.shd = NULL;
	gstate->pending.sc.n = n;
	for (i = 0; i < n; ++i)
		gstate->pending.sc.c[i] = color[i];
	copy_resource(ctx, p, PDF_NAME_Pattern, name);
}

static void
pdf_filter_SC_shade(fz_context *ctx, pdf_processor *proc, const char *name, fz_shade *shade)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	fz_strlcpy(gstate->pending.SC.name, name, sizeof gstate->pending.SC.name);
	gstate->pending.SC.pat = NULL;
	gstate->pending.SC.shd = shade;
	gstate->pending.SC.n = 0;
	copy_resource(ctx, p, PDF_NAME_Pattern, name);
}

static void
pdf_filter_sc_shade(fz_context *ctx, pdf_processor *proc, const char *name, fz_shade *shade)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	fz_strlcpy(gstate->pending.sc.name, name, sizeof gstate->pending.sc.name);
	gstate->pending.sc.pat = NULL;
	gstate->pending.sc.shd = shade;
	gstate->pending.sc.n = 0;
	copy_resource(ctx, p, PDF_NAME_Pattern, name);
}

static void
pdf_filter_SC_color(fz_context *ctx, pdf_processor *proc, int n, float *color)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	int i;
	gstate->pending.SC.name[0] = 0;
	gstate->pending.SC.pat = NULL;
	gstate->pending.SC.shd = NULL;
	gstate->pending.SC.n = n;
	for (i = 0; i < n; ++i)
		gstate->pending.SC.c[i] = fz_clamp(color[i], 0, 1);
}

static void
pdf_filter_sc_color(fz_context *ctx, pdf_processor *proc, int n, float *color)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gstate = gstate_to_update(ctx, p);
	int i;
	gstate->pending.sc.name[0] = 0;
	gstate->pending.sc.pat = NULL;
	gstate->pending.sc.shd = NULL;
	gstate->pending.sc.n = n;
	for (i = 0; i < n; ++i)
		gstate->pending.sc.c[i] = fz_clamp(color[i], 0, 1);
}

static void
pdf_filter_G(fz_context *ctx, pdf_processor *proc, float g)
{
	float color[1] = { g };
	pdf_filter_CS(ctx, proc, "DeviceGray", fz_device_gray(ctx));
	pdf_filter_SC_color(ctx, proc, 1, color);
}

static void
pdf_filter_g(fz_context *ctx, pdf_processor *proc, float g)
{
	float color[1] = { g };
	pdf_filter_cs(ctx, proc, "DeviceGray", fz_device_gray(ctx));
	pdf_filter_sc_color(ctx, proc, 1, color);
}

static void
pdf_filter_RG(fz_context *ctx, pdf_processor *proc, float r, float g, float b)
{
	float color[3] = { r, g, b };
	pdf_filter_CS(ctx, proc, "DeviceRGB", fz_device_rgb(ctx));
	pdf_filter_SC_color(ctx, proc, 3, color);
}

static void
pdf_filter_rg(fz_context *ctx, pdf_processor *proc, float r, float g, float b)
{
	float color[3] = { r, g, b };
	pdf_filter_cs(ctx, proc, "DeviceRGB", fz_device_rgb(ctx));
	pdf_filter_sc_color(ctx, proc, 3, color);
}

static void
pdf_filter_K(fz_context *ctx, pdf_processor *proc, float c, float m, float y, float k)
{
	float color[4] = { c, m, y, k };
	pdf_filter_CS(ctx, proc, "DeviceCMYK", fz_device_cmyk(ctx));
	pdf_filter_SC_color(ctx, proc, 4, color);
}

static void
pdf_filter_k(fz_context *ctx, pdf_processor *proc, float c, float m, float y, float k)
{
	float color[4] = { c, m, y, k };
	pdf_filter_cs(ctx, proc, "DeviceCMYK", fz_device_cmyk(ctx));
	pdf_filter_sc_color(ctx, proc, 4, color);
}

/* shadings, images, xobjects */

static void
pdf_filter_BI(fz_context *ctx, pdf_processor *proc, fz_image *img)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_BI)
		p->chain->op_BI(ctx, p->chain, img);
}

static void
pdf_filter_sh(fz_context *ctx, pdf_processor *proc, const char *name, fz_shade *shade)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_sh)
		p->chain->op_sh(ctx, p->chain, name, shade);
	copy_resource(ctx, p, PDF_NAME_Shading, name);
}

static void
pdf_filter_Do_image(fz_context *ctx, pdf_processor *proc, const char *name, fz_image *image)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_Do_image)
		p->chain->op_Do_image(ctx, p->chain, name, image);
	copy_resource(ctx, p, PDF_NAME_XObject, name);
}

static void
pdf_filter_Do_form(fz_context *ctx, pdf_processor *proc, const char *name, pdf_obj *xobj, pdf_obj *page_resources)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, FLUSH_ALL);
	if (p->chain->op_Do_form)
		p->chain->op_Do_form(ctx, p->chain, name, xobj, page_resources);
	copy_resource(ctx, p, PDF_NAME_XObject, name);
}

/* marked content */

static void
pdf_filter_MP(fz_context *ctx, pdf_processor *proc, const char *tag)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_MP)
		p->chain->op_MP(ctx, p->chain, tag);
}

static void
pdf_filter_DP(fz_context *ctx, pdf_processor *proc, const char *tag, pdf_obj *raw, pdf_obj *cooked)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_DP)
		p->chain->op_DP(ctx, p->chain, tag, raw, cooked);
}

static void
pdf_filter_BMC(fz_context *ctx, pdf_processor *proc, const char *tag)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_BMC)
		p->chain->op_BMC(ctx, p->chain, tag);
}

static void
pdf_filter_BDC(fz_context *ctx, pdf_processor *proc, const char *tag, pdf_obj *raw, pdf_obj *cooked)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_BDC)
		p->chain->op_BDC(ctx, p->chain, tag, raw, cooked);
}

static void
pdf_filter_EMC(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_EMC)
		p->chain->op_EMC(ctx, p->chain);
}

/* compatibility */

static void
pdf_filter_BX(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_BX)
		p->chain->op_BX(ctx, p->chain);
}

static void
pdf_filter_EX(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_flush(ctx, p, 0);
	if (p->chain->op_EX)
		p->chain->op_EX(ctx, p->chain);
}

static void
pdf_filter_END(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	while (!filter_pop(ctx, p))
	{
		/* Nothing to do in the loop, all work done above */
	}
}

static void
pdf_drop_filter_processor(fz_context *ctx, pdf_processor *proc)
{
	pdf_filter_processor *p = (pdf_filter_processor*)proc;
	filter_gstate *gs = p->gstate;
	while (gs)
	{
		filter_gstate *next = gs->next;
		pdf_drop_font(ctx, gs->pending.text.font);
		pdf_drop_font(ctx, gs->sent.text.font);
		fz_free(ctx, gs);
		gs = next;
	}
	pdf_drop_document(ctx, p->doc);
	fz_free(ctx, p->font_name);
}

pdf_processor *
pdf_new_filter_processor(fz_context *ctx, pdf_document *doc, pdf_processor *chain, pdf_obj *old_rdb, pdf_obj *new_rdb)
{
	return pdf_new_filter_processor_with_text_filter(ctx, doc, chain, old_rdb, new_rdb, NULL, NULL, NULL);
}

pdf_processor *
pdf_new_filter_processor_with_text_filter(fz_context *ctx, pdf_document *doc, pdf_processor *chain, pdf_obj *old_rdb, pdf_obj *new_rdb, pdf_text_filter_fn *text_filter, pdf_after_text_object_fn *after, void *text_filter_opaque)
{
	pdf_filter_processor *proc = pdf_new_processor(ctx, sizeof *proc);
	{
		proc->super.drop_processor = pdf_drop_filter_processor;

		/* general graphics state */
		proc->super.op_w = pdf_filter_w;
		proc->super.op_j = pdf_filter_j;
		proc->super.op_J = pdf_filter_J;
		proc->super.op_M = pdf_filter_M;
		proc->super.op_d = pdf_filter_d;
		proc->super.op_ri = pdf_filter_ri;
		proc->super.op_i = pdf_filter_i;
		proc->super.op_gs_begin = pdf_filter_gs_begin;
		proc->super.op_gs_end = pdf_filter_gs_end;

		/* transparency graphics state */
		proc->super.op_gs_BM = pdf_filter_gs_BM;
		proc->super.op_gs_CA = pdf_filter_gs_CA;
		proc->super.op_gs_ca = pdf_filter_gs_ca;
		proc->super.op_gs_SMask = pdf_filter_gs_SMask;

		/* special graphics state */
		proc->super.op_q = pdf_filter_q;
		proc->super.op_Q = pdf_filter_Q;
		proc->super.op_cm = pdf_filter_cm;

		/* path construction */
		proc->super.op_m = pdf_filter_m;
		proc->super.op_l = pdf_filter_l;
		proc->super.op_c = pdf_filter_c;
		proc->super.op_v = pdf_filter_v;
		proc->super.op_y = pdf_filter_y;
		proc->super.op_h = pdf_filter_h;
		proc->super.op_re = pdf_filter_re;

		/* path painting */
		proc->super.op_S = pdf_filter_S;
		proc->super.op_s = pdf_filter_s;
		proc->super.op_F = pdf_filter_F;
		proc->super.op_f = pdf_filter_f;
		proc->super.op_fstar = pdf_filter_fstar;
		proc->super.op_B = pdf_filter_B;
		proc->super.op_Bstar = pdf_filter_Bstar;
		proc->super.op_b = pdf_filter_b;
		proc->super.op_bstar = pdf_filter_bstar;
		proc->super.op_n = pdf_filter_n;

		/* clipping paths */
		proc->super.op_W = pdf_filter_W;
		proc->super.op_Wstar = pdf_filter_Wstar;

		/* text objects */
		proc->super.op_BT = pdf_filter_BT;
		proc->super.op_ET = pdf_filter_ET;

		/* text state */
		proc->super.op_Tc = pdf_filter_Tc;
		proc->super.op_Tw = pdf_filter_Tw;
		proc->super.op_Tz = pdf_filter_Tz;
		proc->super.op_TL = pdf_filter_TL;
		proc->super.op_Tf = pdf_filter_Tf;
		proc->super.op_Tr = pdf_filter_Tr;
		proc->super.op_Ts = pdf_filter_Ts;

		/* text positioning */
		proc->super.op_Td = pdf_filter_Td;
		proc->super.op_TD = pdf_filter_TD;
		proc->super.op_Tm = pdf_filter_Tm;
		proc->super.op_Tstar = pdf_filter_Tstar;

		/* text showing */
		proc->super.op_TJ = pdf_filter_TJ;
		proc->super.op_Tj = pdf_filter_Tj;
		proc->super.op_squote = pdf_filter_squote;
		proc->super.op_dquote = pdf_filter_dquote;

		/* type 3 fonts */
		proc->super.op_d0 = pdf_filter_d0;
		proc->super.op_d1 = pdf_filter_d1;

		/* color */
		proc->super.op_CS = pdf_filter_CS;
		proc->super.op_cs = pdf_filter_cs;
		proc->super.op_SC_color = pdf_filter_SC_color;
		proc->super.op_sc_color = pdf_filter_sc_color;
		proc->super.op_SC_pattern = pdf_filter_SC_pattern;
		proc->super.op_sc_pattern = pdf_filter_sc_pattern;
		proc->super.op_SC_shade = pdf_filter_SC_shade;
		proc->super.op_sc_shade = pdf_filter_sc_shade;

		proc->super.op_G = pdf_filter_G;
		proc->super.op_g = pdf_filter_g;
		proc->super.op_RG = pdf_filter_RG;
		proc->super.op_rg = pdf_filter_rg;
		proc->super.op_K = pdf_filter_K;
		proc->super.op_k = pdf_filter_k;

		/* shadings, images, xobjects */
		proc->super.op_BI = pdf_filter_BI;
		proc->super.op_sh = pdf_filter_sh;
		proc->super.op_Do_image = pdf_filter_Do_image;
		proc->super.op_Do_form = pdf_filter_Do_form;

		/* marked content */
		proc->super.op_MP = pdf_filter_MP;
		proc->super.op_DP = pdf_filter_DP;
		proc->super.op_BMC = pdf_filter_BMC;
		proc->super.op_BDC = pdf_filter_BDC;
		proc->super.op_EMC = pdf_filter_EMC;

		/* compatibility */
		proc->super.op_BX = pdf_filter_BX;
		proc->super.op_EX = pdf_filter_EX;

		/* extgstate */
		proc->super.op_gs_OP = pdf_filter_gs_OP;
		proc->super.op_gs_op = pdf_filter_gs_op;
		proc->super.op_gs_OPM = pdf_filter_gs_OPM;
		proc->super.op_gs_UseBlackPtComp = pdf_filter_gs_UseBlackPtComp;

		proc->super.op_END = pdf_filter_END;
	}

	proc->doc = pdf_keep_document(ctx, doc);
	proc->chain = chain;
	proc->old_rdb = old_rdb;
	proc->new_rdb = new_rdb;

	proc->text_filter = text_filter;
	proc->after_text = after;
	proc->opaque = text_filter_opaque;

	fz_try(ctx)
	{
		proc->gstate = fz_malloc_struct(ctx, filter_gstate);
		proc->gstate->pending.ctm = fz_identity;
		proc->gstate->sent.ctm = fz_identity;

		proc->gstate->pending.stroke = proc->gstate->pending.stroke; /* ? */
		proc->gstate->sent.stroke = proc->gstate->pending.stroke;
		proc->gstate->pending.text.char_space = 0;
		proc->gstate->pending.text.word_space = 0;
		proc->gstate->pending.text.scale = 1;
		proc->gstate->pending.text.leading = 0;
		proc->gstate->pending.text.font = NULL;
		proc->gstate->pending.text.size = -1;
		proc->gstate->pending.text.render = 0;
		proc->gstate->pending.text.rise = 0;
		proc->gstate->sent.text.char_space = 0;
		proc->gstate->sent.text.word_space = 0;
		proc->gstate->sent.text.scale = 1;
		proc->gstate->sent.text.leading = 0;
		proc->gstate->sent.text.font = NULL;
		proc->gstate->sent.text.size = -1;
		proc->gstate->sent.text.render = 0;
		proc->gstate->sent.text.rise = 0;
	}
	fz_catch(ctx)
	{
		pdf_drop_processor(ctx, (pdf_processor *) proc);
		fz_rethrow(ctx);
	}

	return (pdf_processor*)proc;
}
