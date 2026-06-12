from __future__ import annotations

from html import escape

from .config import PublicSiteConfig
from .render import join_url, render_page


def render_home_redirect(config: PublicSiteConfig) -> str:
    body = '<p><a href="/series/">continue to works</a></p>'
    return render_page(
        config,
        title="dotlineform",
        body=body,
        path="/",
        section="series",
        extra_head=(
            '<meta http-equiv="refresh" content="0; url=/series/">',
            '<link rel="canonical" href="/series/">',
        ),
    )


def render_404(config: PublicSiteConfig) -> str:
    body = "\n".join(
        (
            '<article class="page page--error">',
            '  <h1>page unavailable</h1>',
            "  <p>This page is unavailable.</p>",
            '  <p><a href="/series/">return to works</a></p>',
            "</article>",
        )
    )
    return render_page(config, title="page unavailable", body=body, path="/404.html", section="page")


def render_about(config: PublicSiteConfig) -> str:
    hero_base = join_url(config.home_media["base"], config.home_media["prefix"])
    body = f"""
<header class="about-header visually-hidden">
  <h1>about</h1>
</header>

<figure class="about-hero about-hero--flush">
  <img
    src="{escape(hero_base + 'forest-4.webp', quote=True)}"
    srcset="{escape(hero_base + 'forest-4-1280.webp', quote=True)} 1280w,
            {escape(hero_base + 'forest-4-2560.webp', quote=True)} 2560w,
            {escape(hero_base + 'forest-4-3840.webp', quote=True)} 3840w"
    sizes="100vw"
    alt="forest [4]"
    loading="lazy"
    decoding="async"
  >
</figure>

<nav class="about-links" aria-label="Site links">
  <div class="about-link-item">
    <span class="about-link-prefix">photography</span>
    <a class="about-link" href="https://www.behance.net/dotlineform" target="_blank" rel="noopener noreferrer">Behance</a>
  </div>
  <div class="about-link-item">
    <span class="about-link-prefix">video</span>
    <a class="about-link" href="https://vimeo.com/dotlineform" target="_blank" rel="noopener noreferrer">Vimeo</a>
  </div>
  <div class="about-link-item">
    <span class="about-link-prefix">music</span>
    <a class="about-link" href="https://dotlineform.bandcamp.com" target="_blank" rel="noopener noreferrer">Bandcamp</a>
  </div>
</nav>""".strip()
    return render_page(config, title="about", body=body, path="/about/", section="page")
