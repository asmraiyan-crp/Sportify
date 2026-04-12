import { HERO_GRADIENTS } from "../../data";
import type { HeroSlide } from "../../types";
import { useHeroSlider } from "../../hooks";
import { HeroBadge } from "../shared";

interface HeroSliderProps {
  slides: HeroSlide[];
}

export function HeroSlider({ slides }: HeroSliderProps) {
  const { idx, goTo, prev, next } = useHeroSlider(slides.length);

  return (
    <div className="relative mb-8 rounded-card overflow-hidden group">
      {/* Track */}
      <div
        className="flex transition-transform duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]"
        style={{ transform: `translateX(-${idx * 100}%)` }}
      >
        {slides.map(slide => <SlideItem key={slide.id} slide={slide} />)}
      </div>

      {/* Prev / Next arrows — visible on hover */}
      <button
        onClick={prev}
        aria-label="Previous slide"
        className="absolute left-3 top-1/2 -translate-y-1/2 z-20 w-9 h-9 rounded-full bg-black/40 border border-white/20 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-black/60"
      >
        ‹
      </button>
      <button
        onClick={next}
        aria-label="Next slide"
        className="absolute right-3 top-1/2 -translate-y-1/2 z-20 w-9 h-9 rounded-full bg-black/40 border border-white/20 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-black/60"
      >
        ›
      </button>

      {/* Dots */}
      <div className="absolute bottom-4 right-6 flex gap-1.5 z-20">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            aria-label={`Go to slide ${i + 1}`}
            className={`h-1.5 rounded-full cursor-pointer transition-all duration-200 border-none
              ${i === idx ? "w-5 bg-accent" : "w-1.5 bg-white/25 hover:bg-white/50"}`}
          />
        ))}
      </div>
    </div>
  );
}

// ─── Individual Slide ─────────────────────────────────────────────────────────

function SlideItem({ slide }: { slide: HeroSlide }) {
  return (
    <div className="relative min-w-full h-[360px] flex items-end px-10 pb-9 shrink-0">
      {/* Gradient BG */}
      <div className="absolute inset-0" style={{ background: HERO_GRADIENTS[slide.bgKey] ?? HERO_GRADIENTS["football-pl"] }} />
      {/* Cinematic overlay — stronger on left for text legibility */}
      <div className="absolute inset-0 bg-hero-overlay" />
      {/* Subtle noise texture for depth */}
      <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" }} />

      <div className="relative z-10 max-w-[520px] animate-slide-up">
        <HeroBadge tag={slide.tag} className="mb-3" />

        <h1 className="font-display text-[52px] leading-none text-white tracking-tight mb-2 drop-shadow-lg">
          {slide.title}
        </h1>
        <p className="text-[13.5px] text-white/60 mb-4 font-body">{slide.league}</p>

        {slide.score ? (
          <div className="font-display text-[34px] text-white tracking-wide mb-5 drop-shadow">
            {slide.score}
            <span className="text-[18px] text-white/40 font-body font-normal ml-3">· {slide.time}</span>
          </div>
        ) : (
          <p className="text-[16px] text-white/50 mb-5 font-body">🕐 {slide.time}</p>
        )}

        <div className="flex gap-2.5">
          <button className="flex items-center gap-2 px-5 py-2.5 rounded-btn text-sm font-semibold bg-accent text-white border-none cursor-pointer font-heading tracking-wide transition-all duration-200 hover:bg-accent-light hover:shadow-accent-glow active:scale-[0.98]">
            ▶ Watch Live
          </button>
          <button className="px-4 py-2.5 rounded-btn text-sm font-semibold bg-white/[0.08] text-white border border-white/15 cursor-pointer font-heading tracking-wide transition-all duration-200 hover:bg-white/[0.15] active:scale-[0.98]">
            + Follow
          </button>
        </div>
      </div>
    </div>
  );
}
