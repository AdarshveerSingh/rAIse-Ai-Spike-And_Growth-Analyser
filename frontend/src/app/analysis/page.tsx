"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import type { MouseEvent } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";
/* ============================================================
   COLOR PALETTE
============================================================ */

const COLORS = {
  lightBlue: "#A2CCCE",
  mintLeaf: "#54C29D",
  linen: "#F5EEE4",
  vibrantCoral: "#F86158",
  ironGrey: "#354244",
  bananaCream: "#F7E141",
  darkTeal: "#1D4248",
} as const;

/* ============================================================
   TYPES
============================================================ */

type EventVideo = {
  video_id: string;
  title: string;
  published_at: string;
  views: number;
  vs_baseline: number;
};

type GrowthEvent = {
  video_id: string;
  title: string;
  published_at: string;

  spike_views: number;
  spike_ratio: number;
  robust_z?: number | null;
  thumbnail_url: string;
  before_baseline: number;
  short_term_baseline: number;
  long_term_baseline: number;

  short_term_change: number;
  long_term_change: number;

  short_term_retained: boolean;
  long_term_retained: boolean;

  event_type:
    | "ONE_OFF"
    | "TEMPORARY"
    | "SUSTAINED_THROUGHOUT"
    | "SUSTAINED_EVENTUAL"
    | "INSUFFICIENT_DATA";

  progressive_trajectory: boolean;

  before: EventVideo[];
  short_term: EventVideo[];
  long_term: EventVideo[];

  before_count: number;
  short_term_count: number;
  long_term_count: number;
};

type ChannelData = {
  channel: {
    id: string;
    name: string;
    description: string;
    published_at: string;
    subscribers: number;
    views: number;
    video_count: number;
      profile_picture?: string;
    banner_url?: string;
  };

  settings: {
    before_count: number;
    short_count: number;
    long_count: number;
    rolling_window?: number;
    spike_threshold: number;
    robust_z_threshold?: number;
    retention_threshold: number;
  };

  analysis: {
    total_videos: number;
    regular_videos: number;
    spike_candidates: number;
    events: number;
    content_types: Record<string, number>;
    classification_counts: Record<string, number>;
    progressive_count: number;
  };

  spikes?: any[];
  ranked_spikes?: any[];
  timeline: any[];
  events: GrowthEvent[];
};

type ResearchResult = {
  success?: boolean;
  creator?: string;

  research?: {
    event?: any;
    summary?: string;
    key_findings?: any[];
    audience_period?: any;
    audience_evidence?: any[];
    cross_year_analysis?: any;
    topic_demand?: any;
    hypotheses?: any[];
    alternative_explanations?: any[];
    what_changed?: any[];
    what_did_not_change?: any[];
    creator_context?: any;
    post_spike_effect?: any;
    evidence_gaps?: any[];
    recommendations?: any[];
    limitations?: any[];
    comment_signals?: any;
    sources?: any[];
  };

  error?: string;

  [key: string]: any;
};

/* ============================================================
   HELPERS
============================================================ */
// function PaletteThumbnail({
//   src,
//   alt,
// }: {
//   src: string;
//   alt: string;
// }) {
//   const canvasRef = React.useRef<HTMLCanvasElement | null>(null);

//   React.useEffect(() => {
//     const canvas = canvasRef.current;
//     if (!canvas || !src) return;

//     const ctx = canvas.getContext("2d");
//     if (!ctx) return;

//     const image = new Image();
//     image.crossOrigin = "anonymous";

//     image.onload = () => {
//       const width = 320;
//       const height = 180;

//       canvas.width = width;
//       canvas.height = height;

//       ctx.drawImage(image, 0, 0, width, height);

//       const imageData = ctx.getImageData(
//         0,
//         0,
//         width,
//         height
//       );

//       const pixels = imageData.data;

//       const palette = [
//         [29, 66, 72],    // #1D4248 dark teal
//         [53, 66, 68],    // #354244 iron grey
//         [84, 194, 157],  // #54C29D mint
//         [162, 204, 206], // #A2CCCE light blue
//         [245, 238, 228], // #F5EEE4 linen
//       ];

//       for (let i = 0; i < pixels.length; i += 4) {
//         const r = pixels[i];
//         const g = pixels[i + 1];
//         const b = pixels[i + 2];

//         // Perceived brightness
//         const luminance =
//           0.2126 * r +
//           0.7152 * g +
//           0.0722 * b;

//         let color;

//         if (luminance < 45) {
//           color = palette[0];
//         } else if (luminance < 90) {
//           color = palette[1];
//         } else if (luminance < 145) {
//           color = palette[2];
//         } else if (luminance < 205) {
//           color = palette[3];
//         } else {
//           color = palette[4];
//         }

//         pixels[i] = color[0];
//         pixels[i + 1] = color[1];
//         pixels[i + 2] = color[2];
//       }

//       ctx.putImageData(imageData, 0, 0);
//     };

//     image.onerror = () => {
//       console.warn("Failed to load thumbnail:", src);
//     };

//     image.src = src;
//   }, [src]);

//   return (
//     <canvas
//       ref={canvasRef}
//       aria-label={alt}
//       className="h-full w-full object-cover transition duration-200 group-hover:scale-105"
//     />
//   );
// }
function formatNumber(value: any): string {
  const n = Number(value);

  if (!Number.isFinite(n)) return "—";

  if (n >= 1_000_000_000) {
    return `${(n / 1_000_000_000).toFixed(1)}B`;
  }

  if (n >= 1_000_000) {
    return `${(n / 1_000_000).toFixed(1)}M`;
  }

  if (n >= 1_000) {
    return `${(n / 1_000).toFixed(1)}K`;
  }

  return Math.round(n).toLocaleString();
}

function formatExactNumber(value: any): string {
  const n = Number(value);

  if (!Number.isFinite(n)) return "—";

  return Math.round(n).toLocaleString();
}

function formatDate(value: any): string {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatRatio(value: any): string {
  const n = Number(value);

  if (!Number.isFinite(n)) return "—";

  return `${n.toFixed(2)}×`;
}

function prettifyEventType(type: string): string {
  return type
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function textValue(value: any): string {
  if (typeof value === "string") {
    return value;
  }

  if (
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  if (
    value === null ||
    value === undefined
  ) {
    return "";
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => textValue(item))
      .filter(Boolean)
      .join(" ");
  }

  if (typeof value === "object") {
    const fields = [
      "finding",
      "observation",
      "change",
      "reason",
      "signal",
      "explanation",
      "hypothesis",
      "recommendation",
      "summary",
      "description",
      "claim",
      "text",
      "value",
    ];

    for (const field of fields) {
      if (
        value[field] !== undefined &&
        value[field] !== null
      ) {
        const result = textValue(value[field]);

        if (result) {
          return result;
        }
      }
    }
  }

  return "";
}

function getEarliestEvent(
  events: GrowthEvent[]
): GrowthEvent | null {
  if (!events.length) return null;

  return events.reduce(
    (earliest, event) =>
      new Date(event.published_at).getTime() <
      new Date(earliest.published_at).getTime()
        ? event
        : earliest
  );
}

function getStrongestEvent(
  events: GrowthEvent[]
): GrowthEvent | null {
  if (!events.length) return null;

  return events.reduce(
    (strongest, event) =>
      Number(event.spike_ratio) >
      Number(strongest.spike_ratio)
        ? event
        : strongest
  );
}

function getFirstEventOfType(
  events: GrowthEvent[],
  type: GrowthEvent["event_type"]
): GrowthEvent | null {
  return getEarliestEvent(
    events.filter(
      (event) => event.event_type === type
    )
  );
}

function getFirstProgressiveEvent(
  events: GrowthEvent[]
): GrowthEvent | null {
  return getEarliestEvent(
    events.filter(
      (event) => event.progressive_trajectory
    )
  );
}

/* ============================================================
   SMALL COMPONENTS
============================================================ */

function LoadingScreen({
  channelUrl,
}: {
  channelUrl: string;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F5EEE4] px-6 text-[#1D4248]">
      <div className="w-full max-w-md text-center">
        <div className="relative mx-auto mb-6 h-12 w-12">
          <div className="absolute inset-0 border-2 border-[#354244]" />
          <div className="absolute inset-[6px] border-2 border-[#54C29D]" />
          <div className="absolute inset-[12px] animate-spin border-2 border-[#F86158] border-t-transparent" />
        </div>

        <h2 className="text-lg font-bold tracking-tight text-[#1D4248]">
          Analyzing channel
        </h2>

        <p className="mt-2 text-sm leading-6 text-[#354244]/70">
          Fetching the creator&apos;s video history and
          detecting meaningful growth events.
        </p>

        {channelUrl && (
          <p className="mx-auto mt-4 max-w-full truncate border border-[#354244]/20 bg-[#F5EEE4] px-3 py-2 text-xs text-[#354244]/60">
            {channelUrl}
          </p>
        )}
      </div>
    </main>
  );
}

function ErrorScreen({
  error,
  onRetry,
}: {
  error: string;
  onRetry: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F5EEE4] px-6 text-[#1D4248]">
      <div className="w-full max-w-md border-2 border-[#F86158] bg-[#354244] p-6 text-[#F5EEE4]">
        <div className="flex h-10 w-10 items-center justify-center border-2 border-[#F86158] bg-[#F86158] text-lg font-bold text-[#1D4248]">
          !
        </div>

        <h1 className="mt-5 text-lg font-bold">
          Could not analyze channel
        </h1>

        <p className="mt-2 text-sm leading-6 text-[#F5EEE4]/70">
          {error}
        </p>

        <button
          type="button"
          onClick={onRetry}
          className="mt-5 border-2 border-[#F86158] bg-[#F86158] px-4 py-2 text-sm font-bold text-[#1D4248] transition hover:bg-[#F7E141] hover:border-[#F7E141]"
        >
          Try again
        </button>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  description,
  accent = COLORS.lightBlue,
}: {
  label: string;
  value: string;
  description?: string;
  accent?: string;
}) {
  return (
    <div className="relative overflow-hidden border-2 border-[#1D4248] bg-[#354244] p-4 shadow-[3px_3px_0px_#1D4248]">
      <div className="absolute left-0 top-0 h-full w-1" style={{ backgroundColor: accent }} />
      <p className="pl-2 text-[10px] font-bold uppercase tracking-[0.16em]" style={{ color: accent }}>
        {label}
      </p>
      <p className="mt-2 pl-2 text-2xl font-black tracking-tight text-[#F5EEE4] sm:text-3xl">
        {value}
      </p>
      {description && (
        <p className="mt-1 pl-2 text-[10px] font-medium text-[#A2CCCE]">
          {description}
        </p>
      )}
    </div>
  );
}

function EventBadge({
  event,
}: {
  event: GrowthEvent;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <span className="border border-[#A2CCCE] bg-[#A2CCCE] px-2.5 py-1 text-[10px] font-bold text-[#1D4248]">
        {prettifyEventType(event.event_type)}
      </span>

      {event.progressive_trajectory && (
        <span className="border border-[#54C29D] bg-[#54C29D] px-2.5 py-1 text-[10px] font-bold text-[#1D4248]">
          Progressive
        </span>
      )}
    </div>
  );
}

/* ============================================================
   VIDEO TABLE
============================================================ */

function WindowVideoTable({
  videos,
}: {
  videos: EventVideo[];
}) {
  if (!videos?.length) {
    return (
      <div className="border-2 border-[#A2CCCE] bg-[#354244] p-4 text-sm text-[#F5EEE4]/60">
        No videos available in this window.
      </div>
    );
  }

  return (
    <div className="overflow-hidden border-2 border-[#354244] bg-[#F5EEE4]">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[620px] text-left">
          <thead className="border-b-2 border-[#A2CCCE] bg-[#A2CCCE]">
            <tr>
              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-[#1D4248]">
                Video
              </th>

              <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-[#1D4248]">
                Date
              </th>

              <th className="px-4 py-3 text-right text-[10px] font-bold uppercase tracking-wider text-[#1D4248]">
                Views
              </th>

              <th className="px-4 py-3 text-right text-[10px] font-bold uppercase tracking-wider text-[#1D4248]">
                vs Baseline
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#354244]/15 bg-[#F5EEE4]">
            {videos.map((video) => (
              <tr
                key={video.video_id}
                className="transition hover:bg-[#A2CCCE]/30"
              >
                <td className="max-w-[420px] px-4 py-3">
  <button
    type="button"
    onClick={() => {
      if (!video.video_id) return;

      window.open(
        `https://www.youtube.com/watch?v=${video.video_id}`,
        "_blank",
        "noopener,noreferrer"
      );
    }}
    className="block max-w-full cursor-pointer truncate text-left text-sm font-semibold text-[#1D4248] transition-colors duration-150 hover:text-[#F86158] hover:underline"
  >
    {video.title}
  </button>
</td>

                <td className="whitespace-nowrap px-4 py-3 text-xs text-[#354244]">
                  {formatDate(video.published_at)}
                </td>

                <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-bold text-[#1D4248]">
                  {formatNumber(video.views)}
                </td>

                <td className="whitespace-nowrap px-4 py-3 text-right">
                  <span
                    className={
                      video.vs_baseline >= 1
                        ? "text-sm font-bold text-[#54C29D]"
                        : "text-sm text-[#F86158]"
                    }
                  >
                    {formatRatio(video.vs_baseline)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ============================================================
   EVENT DETAILS
============================================================ */

function EventDetails({
  event,
  onRunResearch,
  researchLoading,
}: {
  event: GrowthEvent;
  onRunResearch: () => void;
  researchLoading: boolean;
}) {
  return (
    <div className="border-t-2 border-[#F5EEE4]/10 bg-[#1D4248]">
      <div className="grid grid-cols-2 gap-0 border-b-2 border-[#354244] md:grid-cols-4">
        <div className="border-r-2 border-[#354244]">
          <StatCard
            label="Spike views"
            value={formatNumber(event.spike_views)}
          />
        </div>

        <div className="border-r-2 border-[#354244]">
          <StatCard
            label="Spike ratio"
            value={formatRatio(event.spike_ratio)}
          />
        </div>

        <div className="border-r-2 border-[#354244]">
          <StatCard
            label="Short-term change"
            value={formatRatio(event.short_term_change)}
          />
        </div>

        <StatCard
          label="Long-term change"
          value={formatRatio(event.long_term_change)}
        />
      </div>

      <div className="flex flex-wrap gap-x-8 gap-y-3 border-b-2 border-[#F5EEE4]/10 bg-[#354244] px-5 py-4">
        <span className="text-xs text-[#A2CCCE]">
          Short-term:
          <span className="ml-2 font-bold text-[#F5EEE4]">
            {event.short_term_retained
              ? "Retained"
              : "Not retained"}
          </span>
        </span>

        <span className="text-xs text-[#A2CCCE]">
          Long-term:
          <span className="ml-2 font-bold text-[#F5EEE4]">
            {event.long_term_retained
              ? "Retained"
              : "Not retained"}
          </span>
        </span>

        <span className="text-xs text-[#A2CCCE]">
          Before baseline:
          <span className="ml-2 font-bold text-[#F5EEE4]">
            {formatExactNumber(event.before_baseline)}
          </span>
        </span>
      </div>

      <div className="space-y-8 bg-[#F5EEE4] p-5">
        <div>
          <div className="mb-3 flex items-end justify-between border-b-2 border-[#354244] pb-2">
            <div>
              <p className="text-sm font-bold text-[#1D4248]">
                Before
              </p>

              <p className="mt-1 text-xs text-[#354244]/60">
                {event.before_count} videos before the spike
              </p>
            </div>

            <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#F86158]">
              Pre-event
            </span>
          </div>

          <WindowVideoTable videos={event.before} />
        </div>

        <div>
          <div className="mb-3 flex items-end justify-between border-b-2 border-[#354244] pb-2">
            <div>
              <p className="text-sm font-bold text-[#1D4248]">
                Short-term aftermath
              </p>

              <p className="mt-1 text-xs text-[#354244]/60">
                {event.short_term_count} videos after the spike
              </p>
            </div>

            <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#54C29D]">
              Short-term
            </span>
          </div>

          <WindowVideoTable videos={event.short_term} />
        </div>

        <div>
          <div className="mb-3 flex items-end justify-between border-b-2 border-[#354244] pb-2">
            <div>
              <p className="text-sm font-bold text-[#1D4248]">
                Long-term aftermath
              </p>

              <p className="mt-1 text-xs text-[#354244]/60">
                {event.long_term_count} subsequent videos
              </p>
            </div>

            <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#F7E141]">
              Long-term
            </span>
          </div>

          <WindowVideoTable videos={event.long_term} />
        </div>
      </div>

      <div className="border-t-2 border-[#354244] bg-[#354244] px-5 py-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-bold text-[#F5EEE4]">
              Investigate this event
            </p>

            <p className="mt-1 max-w-2xl text-xs leading-5 text-[#A2CCCE]/70">
              Research comments, audience timing,
              topic demand, related historical videos
              and external evidence.
            </p>
          </div>

          <button
            type="button"
            onClick={onRunResearch}
            disabled={researchLoading}
            className="border-2 border-[#F86158] bg-[#F86158] px-5 py-2.5 text-sm font-bold text-[#1D4248] transition hover:border-[#F7E141] hover:bg-[#F7E141] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {researchLoading
              ? "Researching..."
              : "Run Research"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   EVENT CARD
============================================================ */

function GrowthEventCard({
  label,
  event,
  selected,
  expanded,
  researchLoading,
  onToggle,
  onRunResearch,
}: {
  label: string;
  event: GrowthEvent;
  selected: boolean;
  expanded: boolean;
  researchLoading: boolean;
  onToggle: () => void;
  onRunResearch: () => void;
}) {
  return (
    <div
      className={`group relative overflow-hidden border-2 bg-[#354244] shadow-[3px_3px_0px_#1D4248] transition-all duration-200 ease-out hover:z-10 hover:scale-[1.045] hover:shadow-[15px_15px_0px_#F86158] hover:bg-[#1D4248] ${
        selected ? "border-[#F86158]" : "border-[#1D4248]"
      }`}
    >
      <button
        type="button"
        onClick={onToggle}
        className="w-full cursor-pointer text-left"
        aria-label={`Select ${event.title}`}
      >
        <div className="flex items-start justify-between gap-5 p-4">
          <div className="min-w-0 flex-1">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span
                className={`text-[10px] font-bold uppercase tracking-[0.18em] ${
                  selected ? "text-[#F86158]" : "text-[#A2CCCE]"
                }`}
              >
                {label}
              </span>
              <EventBadge event={event} />
            </div>
            <h3 className="truncate text-sm font-bold text-[#F5EEE4] sm:text-base">
              {event.title}
            </h3>
            <p className="mt-1 text-xs text-[#A2CCCE]">
              {formatDate(event.published_at)}
            </p>
          </div>

          <div className="shrink-0 text-right">
            <p className="text-lg font-black text-[#F86158]">
              {formatRatio(event.spike_ratio)}
            </p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#A2CCCE]">
              spike
            </p>
          </div>
        </div>
      </button>
    </div>
  );
}

/* ============================================================
   RESEARCH
============================================================ */

function ResearchList({
  items,
  empty = "No evidence available.",
}: {
  items?: any[];
  empty?: string;
}) {
  if (!items?.length) {
    return (
      <p className="text-sm text-[#354244]">
        {empty}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, index) => {
        const text = textValue(item);

        if (!text) return null;

        return (
          <div
            key={index}
            className="border-2 border-[#A2CCCE] bg-[#354244] p-4"
          >
            <div className="flex flex-wrap gap-2">
              <p className="flex-1 text-sm leading-6 text-[#F5EEE4]">
                {text}
              </p>

              {item?.evidence_level && (
                <span className="h-fit border border-[#54C29D] px-2 py-1 text-[10px] font-bold uppercase tracking-[0.08em] text-[#54C29D]">
                  {String(item.evidence_level)}
                </span>
              )}

              {item?.confidence && (
                <span className="h-fit border border-[#F7E141] px-2 py-1 text-[10px] font-bold uppercase tracking-[0.08em] text-[#F7E141]">
                  {String(item.confidence)}
                </span>
              )}
            </div>

            {Array.isArray(item?.sources) &&
              item.sources.length > 0 && (
                <div className="mt-3 space-y-1 border-t border-[#A2CCCE]/30 pt-3">
                  {item.sources.map(
                    (
                      source: any,
                      sourceIndex: number
                    ) => (
                      <a
                        key={sourceIndex}
                        href={source?.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block truncate text-[10px] text-[#A2CCCE] transition-colors hover:text-[#F86158]"
                      >
                        {source?.title ??
                          source?.name ??
                          source?.url}
                      </a>
                    )
                  )}
                </div>
              )}
          </div>
        );
      })}
    </div>
  );
}

function ResearchSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3 className="mb-3 text-sm font-black uppercase tracking-[0.12em] text-[#354244]">
        {title}
      </h3>

      {children}
    </section>
  );
}
/* ============================================================
   rAIse POSTER-STYLE RESEARCH RENDERERS
   Visual system:
   Linen       #F5EEE4
   Mint        #54C29D
   Coral       #F86158
   Light Blue  #A2CCCE
   Iron Grey   #354244
   Banana      #F7E141
   Dark Teal   #1D4248

   IMPORTANT:
   This section ONLY changes presentation.
   No research data structure or data flow is changed.
============================================================ */

/* ============================================================
   POSTER STYLE CONSTANTS
============================================================ */

const POSTER = {
  linen: "#F5EEE4",
  mint: "#54C29D",
  coral: "#F86158",
  lightBlue: "#A2CCCE",
  ironGrey: "#354244",
  banana: "#F7E141",
  darkTeal: "#1D4248",
} as const;


/* ============================================================
   SMALL HELPERS
============================================================ */

function posterAccent(index: number) {
  const colors = [
    POSTER.coral,
    POSTER.mint,
    POSTER.banana,
    POSTER.lightBlue,
  ];

  return colors[index % colors.length];
}


/* ============================================================
   STRUCTURED RESEARCH RENDERERS
============================================================ */

function ResearchObject({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No evidence available.
      </p>
    );
  }


  if (
    typeof data === "string" ||
    typeof data === "number" ||
    typeof data === "boolean"
  ) {
    return (
      <div
        className="
          border-2
          border-[#54C29D]
          bg-[#354244]
          p-4
          text-sm
          leading-6
          text-[#F5EEE4]
        "
      >
        {String(data)}
      </div>
    );
  }


  if (Array.isArray(data)) {
    return <ResearchList items={data} />;
  }


  const preferredFields = [
    "finding",
    "observation",
    "change",
    "reason",
    "signal",
    "explanation",
    "hypothesis",
    "recommendation",
    "summary",
    "description",
    "claim",
    "text",
    "value",
  ];


  const renderedFields = preferredFields.filter(
    (field) =>
      data[field] !== undefined &&
      data[field] !== null
  );


  if (renderedFields.length > 0) {
    return (
      <div className="space-y-3">

        {renderedFields.map((field, index) => (
          <div
            key={field}
            className="
              border-2
              bg-[#354244]
              p-4
            "
            style={{
              borderColor: posterAccent(index),
            }}
          >

            <p
              className="
                mb-2
                text-[10px]
                font-bold
                uppercase
                tracking-[0.18em]
                text-[#A2CCCE]
              "
            >
              {field.replaceAll("_", " ")}
            </p>


            <p className="text-sm leading-6 text-[#F5EEE4]">

              {typeof data[field] === "object"
                ? JSON.stringify(data[field], null, 2)
                : String(data[field])}

            </p>

          </div>
        ))}

      </div>
    );
  }


  const entries = Object.entries(data).filter(
    ([, value]) =>
      value !== undefined &&
      value !== null &&
      value !== ""
  );


  if (!entries.length) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No evidence available.
      </p>
    );
  }


  return (
    <div className="space-y-3">

      {entries.map(([key, value], index) => (

        <div
          key={key}
          className="
            border-2
            bg-[#354244]
            p-4
          "
          style={{
            borderColor: posterAccent(index),
          }}
        >

          <p
            className="
              mb-2
              text-[10px]
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#A2CCCE]
            "
          >
            {key.replaceAll("_", " ")}
          </p>


          {Array.isArray(value) ? (

            <ResearchList items={value} />

          ) : typeof value === "object" ? (

            <ResearchObject data={value} />

          ) : (

            <p className="text-sm leading-6 text-[#F5EEE4]">
              {String(value)}
            </p>

          )}

        </div>

      ))}

    </div>
  );
}


/* ============================================================
   AUDIENCE ACTIVITY
============================================================ */

function AudienceActivity({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No audience-activity evidence available.
      </p>
    );
  }


  return <ResearchObject data={data} />;
}


/* ============================================================
   TOPIC DEMAND
============================================================ */

function TopicDemand({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No topic-demand evidence available.
      </p>
    );
  }


  return <ResearchObject data={data} />;
}


/* ============================================================
   CROSS-YEAR SIGNALS
============================================================ */

function CrossYearSignals({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No cross-year analysis available.
      </p>
    );
  }


  return <ResearchObject data={data} />;
}


/* ============================================================
   CREATOR CONTEXT
============================================================ */

function CreatorContext({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No creator-context evidence available.
      </p>
    );
  }


  return <ResearchObject data={data} />;
}


/* ============================================================
   POST SPIKE EFFECT
============================================================ */

function PostSpikeEffect({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No post-spike interpretation available.
      </p>
    );
  }


  return <ResearchObject data={data} />;
}


/* ============================================================
   COMMENT SIGNALS
============================================================ */

function CommentSignals({ data }: { data: any }) {

  if (!data) {
    return (
      <p className="text-sm leading-6 text-[#354244]/60">
        No comment signals available.
      </p>
    );
  }


  const themeCounts = data.theme_counts ?? {};


  function renderCommentItem(item: any) {

    if (
      typeof item === "string" ||
      typeof item === "number" ||
      typeof item === "boolean"
    ) {
      return (
  <p className="text-sm leading-6 text-[#F5EEE4]">
    {String(item)}
  </p>
);
    }


    if (item === null || item === undefined) {
      return "";
    }


    if (typeof item === "object") {

      if (item.text !== undefined) {
        return (
          <div className="space-y-2">

            <p className="text-sm leading-6 text-[#F5EEE4]">
              {String(item.text)}
            </p>


            {item.likes !== undefined && (
              <p className="text-[10px] font-bold uppercase tracking-wider text-[#A2CCCE]">
                {formatExactNumber(item.likes)} likes
              </p>
            )}

          </div>
        );
      }


      const text = textValue(item);


      if (text) {
        return (
          <p className="text-sm leading-6 text-[#F5EEE4]">
            {text}
          </p>
        );
      }


      return (
        <pre
          className="
            overflow-x-auto
            whitespace-pre-wrap
            text-xs
            leading-5
            text-[#A2CCCE]
          "
        >
          {JSON.stringify(item, null, 2)}
        </pre>
      );
    }


    return String(item);
  }


  function renderList(
    items: any[] | undefined,
    emptyText: string
  ) {

    if (!items?.length) {
      return (
        <p className="text-sm leading-6 text-[#F5EEE4]/60">
          {emptyText}
        </p>
      );
    }


    return (
      <ul className="mt-3 space-y-2 text-[#F5EEE4]">

        {items.map(
          (item: any, index: number) => (

            <li
              key={index}
              className="
                border-2
                bg-[#354244]
                p-3
                text-[#F5EEE4]
              "
              style={{
                borderColor: posterAccent(index),
              }}
            >

              {renderCommentItem(item)}

            </li>

          )
        )}

      </ul>
    );
  }


  return (
    <div className="space-y-6">

      {/* COMMENTS ANALYZED */}

      {data.sample_size !== undefined && (
        <div>

          <h4
            className="
              text-xs
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#F86158]
            "
          >
            Comments analyzed
          </h4>


          <p className="mt-2 text-2xl font-black text-[#F5EEE4]">
            {formatExactNumber(data.sample_size)}
          </p>

        </div>
      )}


      {/* THEME COUNTS */}

      {Object.keys(themeCounts).length > 0 && (
        <div>

          <h4
            className="
              text-xs
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#54C29D]
            "
          >
            Comment themes
          </h4>


          <div className="mt-3 space-y-2">

            {Object.entries(themeCounts)
              .sort(
                ([, a]: any, [, b]: any) =>
                  Number(b) - Number(a)
              )
              .map(
                ([theme, count]: [string, any], index) => (

                  <div
                    key={theme}
                    className="
                      flex
                      items-center
                      justify-between
                      border-2
                      bg-[#354244]
                      p-3
                    "
                    style={{
                      borderColor: posterAccent(index),
                    }}
                  >

                    <span className="text-sm capitalize text-[#F5EEE4]">
                      {theme.replaceAll("_", " ")}
                    </span>


                    <span className="text-sm font-black text-[#F7E141]">
                      {formatExactNumber(count)}
                    </span>

                  </div>

                )
              )}

          </div>

        </div>
      )}


      {/* AUDIENCE SIGNALS */}

      {data.audience_signals?.length > 0 && (
        <div>

          <h4
            className="
              text-xs
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#54C29D]
            "
          >
            Audience signals
          </h4>


          {renderList(
            data.audience_signals,
            "No audience signals available."
          )}

        </div>
      )}


      {/* RECURRING REQUESTS */}

      {data.recurring_requests?.length > 0 && (
        <div>

          <h4
            className="
              text-xs
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#F86158]
            "
          >
            Recurring requests
          </h4>


          {renderList(
            data.recurring_requests,
            "No recurring requests available."
          )}

        </div>
      )}


      {/* COLLABORATOR MENTIONS */}

      {data.collaborator_mentions?.length > 0 && (
        <div>

          <h4
            className="
              text-xs
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#54C29D]
            "
          >
            Collaborator mentions
          </h4>


          {renderList(
            data.collaborator_mentions,
            "No collaborator mentions available."
          )}

        </div>
      )}


      {/* DISCOVERY SIGNALS */}

      {data.discovery_signals?.length > 0 && (
        <div>

          <h4
            className="
              text-xs
              font-bold
              uppercase
              tracking-[0.18em]
              text-[#F7E141]
            "
          >
            Discovery signals
          </h4>


          {renderList(
            data.discovery_signals,
            "No discovery signals available."
          )}

        </div>
      )}

    </div>
  );
}


/* ============================================================
   RESEARCH RESULT
============================================================ */

function ResearchResult({
  result,
  event,
}: {
  result: ResearchResult;
  event: GrowthEvent;
}) {

  const research = result.research;


  if (!research) {
    return (
      <div
        className="
          border-2
          border-[#F86158]
          bg-[#354244]
          p-5
        "
      >

        <p className="text-sm leading-6 text-[#F5EEE4]">
          Research completed, but no structured
          report was returned.
        </p>

      </div>
    );
  }


  return (
    <div className="space-y-8">

      {/* ======================================================
          RESEARCH HEADER
      ====================================================== */}

      <div
        className="
          border-2
          border-[#1D4248]
          bg-[#354244]
          p-6
        "
      >

        <div className="flex flex-wrap items-center gap-3">

          <span
            className="
              border-2
              border-[#F86158]
              bg-[#F86158]
              px-3
              py-1
              text-[10px]
              font-black
              uppercase
              tracking-[0.18em]
              text-[#1D4248]
            "
          >
            AI research
          </span>


          <span
            className="
              text-xs
              font-bold
              uppercase
              tracking-wider
              text-[#A2CCCE]
            "
          >
            {event.title}
          </span>

        </div>


        {research.summary && (
          <p
            className="
              mt-5
              max-w-4xl
              text-base
              leading-7
              text-[#F5EEE4]
            "
          >
            {research.summary}
          </p>
        )}

      </div>


      {/* ======================================================
          CORE FINDINGS
      ====================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        <ResearchSection title="Key findings">
          <ResearchList
            items={research.key_findings}
          />
        </ResearchSection>


        <ResearchSection title="What changed">
          <ResearchList
            items={research.what_changed}
          />
        </ResearchSection>


        <ResearchSection title="What did not change">
          <ResearchList
            items={research.what_did_not_change}
          />
        </ResearchSection>


        <ResearchSection title="Growth hypotheses">
          <ResearchList
            items={research.hypotheses}
          />
        </ResearchSection>


        <ResearchSection title="Alternative explanations">
          <ResearchList
            items={research.alternative_explanations}
          />
        </ResearchSection>


        <ResearchSection title="Recommendations">
          <ResearchList
            items={research.recommendations}
          />
        </ResearchSection>

      </div>


      {/* ======================================================
          AUDIENCE / CREATOR CONTEXT
      ====================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        <ResearchSection title="Audience activity">
          <AudienceActivity
            data={
              research.audience_period ??
              research.audience_evidence
            }
          />
        </ResearchSection>


        <ResearchSection title="Topic demand">
          <TopicDemand
            data={research.topic_demand}
          />
        </ResearchSection>


        <ResearchSection title="Cross-year signals">
          <CrossYearSignals
            data={research.cross_year_analysis}
          />
        </ResearchSection>


        <ResearchSection title="Creator context">
          <CreatorContext
            data={research.creator_context}
          />
        </ResearchSection>

      </div>


      {/* ======================================================
          POST-SPIKE / COMMENTS / LIMITATIONS
      ====================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        <ResearchSection title="Post-spike effect">
          <PostSpikeEffect
            data={research.post_spike_effect}
          />
        </ResearchSection>


        <ResearchSection title="Comment signals">
          <CommentSignals
            data={research.comment_signals}
          />
        </ResearchSection>


        <ResearchSection title="Evidence gaps">
          <ResearchList
            items={research.evidence_gaps}
          />
        </ResearchSection>


        <ResearchSection title="Limitations">
          <ResearchList
            items={research.limitations}
          />
        </ResearchSection>

      </div>


      {/* ======================================================
          SOURCES
      ====================================================== */}

      {research.sources &&
        research.sources.length > 0 && (

          <ResearchSection title="Sources">

            <div className="space-y-3">

              {research.sources.map(
                (
                  source: any,
                  index: number
                ) => (

                  <a
                    key={index}
                    href={source?.url}
                    target="_blank"
                    rel="noreferrer"
                    className="
                      block
                      border-2
                      bg-[#354244]
                      p-4
                      transition
                      hover:-translate-y-[1px]
                    "
                    style={{
                      borderColor: posterAccent(index),
                    }}
                  >

                    <p className="text-sm font-bold text-[#F5EEE4]">
                      {source?.title ??
                        source?.name ??
                        "Source"}
                    </p>


                    {source?.url && (
                      <p className="mt-1 truncate text-xs text-[#A2CCCE]">
                        {source.url}
                      </p>
                    )}

                  </a>

                )
              )}

            </div>

          </ResearchSection>

        )}

    </div>
  );
}
/* ============================================================
   SELECTED EVENT PANEL
============================================================ */

function SelectedEventPanel({
  event,
  researchLoading,
  researchResult,
  researchError,
  onRunResearch,
}: {
  event: GrowthEvent;
  researchLoading: boolean;
  researchResult: ResearchResult | null;
  researchError: string | null;
  onRunResearch: () => void;
}) {
  return (
    <section
      className="
        overflow-hidden
        rounded-none
        border-2
        border-[#354244]
        bg-[#F5EEE4]
        shadow-[5px_5px_0px_#1D4248]
      "
    >
      {/* ======================================================
          EVENT HEADER
      ====================================================== */}

      <div
        className="
          border-b-2
          border-[#354244]
          bg-[#354244]
          p-5
          md:p-6
        "
      >
        <p
          className="
            text-[10px]
            font-semibold
            uppercase
            tracking-[0.22em]
            text-[#F86158]
          "
        >
          Selected event
        </p>

        <div
          className="
            mt-3
            flex
            flex-col
            gap-5
            md:flex-row
            md:items-start
            md:justify-between
          "
        >
          {/* ==================================================
              EVENT INFORMATION
          ================================================== */}

          <div className="min-w-0">
<button
  type="button"
  onClick={() => {
    if (!event.video_id) return;

    window.open(
      `https://www.youtube.com/watch?v=${event.video_id}`,
      "_blank",
      "noopener,noreferrer"
    );
  }}
  className="
    mt-1
    block
    max-w-full
    cursor-pointer
    truncate
    text-left
    text-lg
    font-black
    text-[#F5EEE4]
    transition-colors
    duration-150
    hover:text-[#F86158]
    hover:underline
  "
>
  {event.title}
</button>

            <p
              className="
                mt-2
                text-sm
                font-medium
                text-[#A2CCCE]
              "
            >
              {formatDate(event.published_at)}
            </p>

            <div className="mt-4">
              <EventBadge event={event} />
            </div>
          </div>

          {/* ==================================================
              RESEARCH BUTTON
          ================================================== */}

          <button
            type="button"
            onClick={onRunResearch}
            disabled={researchLoading}
            className="
              shrink-0
              border-2
              border-[#1D4248]
              bg-[#F7E141]
              px-5
              py-2.5
              text-sm
              font-bold
              text-[#1D4248]
              shadow-[3px_3px_0px_#1D4248]
              transition
              duration-150
              hover:translate-x-[1px]
              hover:translate-y-[1px]
              hover:scale-[1.045]
              hover:shadow-[2px_2px_0px_#1D4248]
              hover:bg-[#F5EEE4]
              hover:text-[#354244]
              active:translate-x-[3px]
              active:translate-y-[3px]
              active:shadow-none
              disabled:cursor-not-allowed
              disabled:opacity-50
              disabled:shadow-[2px_2px_0px_#1D4248]
            "
          >
            {researchLoading
              ? "Researching..."
              : "Run Research"}
          </button>
        </div>
      </div>

      {/* ======================================================
          RESEARCH ERROR
      ====================================================== */}

      {researchError && (
        <div
          className="
            border-b-2
            border-[#354244]
            bg-[#F86158]
            p-5
            md:p-6
          "
        >
          <p
            className="
              text-sm
              font-bold
              uppercase
              tracking-[0.08em]
              text-[#1D4248]
            "
          >
            Research failed
          </p>

          <p
            className="
              mt-1
              text-xs
              font-medium
              leading-5
              text-[#1D4248]/80
            "
          >
            {researchError}
          </p>
        </div>
      )}

      {/* ======================================================
          RESEARCH LOADING
      ====================================================== */}

      {researchLoading && (
        <div
          className="
            border-b-2
            border-[#354244]
            bg-[#A2CCCE]
            p-5
            md:p-6
          "
        >
          <div className="flex items-center gap-4">
            {/* Poster-style loading indicator */}
            <div
              className="
                flex
                h-9
                w-9
                shrink-0
                items-center
                justify-center
                border-2
                border-[#1D4248]
                bg-[#F5EEE4]
              "
            >
              <div
                className="
                  h-4
                  w-4
                  animate-spin
                  rounded-full
                  border-2
                  border-[#354244]/20
                  border-t-[#F86158]
                "
              />
            </div>

            <div>
              <p
                className="
                  text-sm
                  font-bold
                  uppercase
                  tracking-[0.08em]
                  text-[#1D4248]
                "
              >
                Research agent running
              </p>

              <p
                className="
                  mt-1
                  text-xs
                  font-medium
                  leading-5
                  text-[#354244]/75
                "
              >
                Gathering evidence and analyzing the event.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================
          RESEARCH RESULT
      ====================================================== */}

      {researchResult &&
        !researchLoading && (
          <div
            className="
              bg-[#F5EEE4]
              p-4
              md:p-6
            "
          >
            <ResearchResult
              result={researchResult}
              event={event}
            />
          </div>
        )}
    </section>
  );
}

/* ============================================================
   DASHBOARD / POSTER HELPERS
============================================================ */

function DashboardIcon({
  name,
  size = 20,
}: {
  name:
    | "home"
    | "chart"
    | "search"
    | "research"
    | "settings"
    | "users"
    | "eye"
    | "video"
    | "trend"
    | "event"
    | "document";
  size?: number;
}) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  if (name === "home") return (
    <svg {...common}><path d="M3 10.5 12 3l9 7.5" /><path d="M5.5 9.5V21h13V9.5" /><path d="M9 21v-6h6v6" /></svg>
  );
  if (name === "search") return (
    <svg {...common}><circle cx="10.8" cy="10.8" r="6.6" /><path d="m16 16 5 5" /></svg>
  );
  if (name === "settings") return (
    <svg {...common}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5v.2h-2.5v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H6.4v-2.5h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5v-.2H15v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1h.2V15h-.2a1.7 1.7 0 0 0-1.5 0Z" /></svg>
  );
  if (name === "users") return (
    <svg {...common}><circle cx="9" cy="8" r="3" /><path d="M3.5 20a5.5 5.5 0 0 1 11 0" /><path d="M16 5.5a3 3 0 0 1 0 5.8M17 15a5 5 0 0 1 4 5" /></svg>
  );
  if (name === "eye") return (
    <svg {...common}><path d="M2.5 12s3.3-6 9.5-6 9.5 6 9.5 6-3.3 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></svg>
  );
  if (name === "video") return (
    <svg {...common}><rect x="3" y="5" width="13" height="14" rx="1.5" /><path d="m16 10 5-3v10l-5-3" /><path d="m9 10 3 2-3 2z" /></svg>
  );
  if (name === "research" || name === "document") return (
    <svg {...common}><path d="M6 3h9l3 3v15H6z" /><path d="M14 3v4h4" /><path d="M9 11h6M9 15h6M9 19h4" /></svg>
  );
  return (
    <svg {...common}><path d="M4 19V5" /><path d="M4 19h16" /><path d="m6 15 4-5 3 2 5-7" /><path d="m15 5 3-1v3" /></svg>
  );
}

function DashboardSidebar() {
  const items = [
    { label: "Overview", icon: "home" as const, active: true },
    { label: "Growth Events", icon: "chart" as const },
    { label: "Analysis", icon: "search" as const },
    { label: "Research", icon: "research" as const },
    { label: "Settings", icon: "settings" as const },
  ];

  return (
    <aside className="fixed left-0 top-0 z-30 hidden h-screen w-[200px] border-r-2 border-black bg-[#354244] text-[#F5EEE4] lg:flex lg:flex-col">

      {/* ───────────── LOGO ───────────── */}
      <div className="flex h-[155px] w-full flex-col items-center justify-start px-3 pt-[2px]">
<a
  href="/"
  className="flex h-[155px] w-full flex-col items-center justify-start px-3 pt-[2px]"
>
  <img
    src="/images/rAIse_logo_White.png"
    alt="rAIse"
    className="h-[92px] w-[150px] object-contain"
  />

  <p className="-mt-1 text-center text-[10px] font-black uppercase tracking-[0.13em] text-[#F5EEE4]">
    Growth &amp; Spike Analyzer
  </p>
</a>
      </div>

      {/* ───────────── NAVIGATION ───────────── */}
      <nav className="relative z-10 px-[15px]">
        <div>
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              className={`
                group flex h-[48px] w-full cursor-pointer items-center gap-[13px]
                border-b border-[#F5EEE4]/10 px-[10px]
                text-left transition-all duration-200
                ${
                  item.active
                    ? "border-b-transparent bg-[#F86158] text-[#1D4248]"
                    : "text-[#F5EEE4]/90 hover:bg-[#1D4248]/70 hover:text-[#F5EEE4]"
                }
              `}
            >
              <span
                className={
                  item.active
                    ? "text-[#1D4248]"
                    : "text-[#F5EEE4]"
                }
              >
                <DashboardIcon name={item.icon} size={22} />
              </span>

              <span className="text-[12px] font-medium tracking-wide">
                {item.label}
              </span>
            </button>
          ))}
        </div>
      </nav>

      {/* ───────────── TAGLINE ───────────── */}
      <div className="relative z-20 mt-auto px-[30px] pb-[170px]">
        <p className="text-[12px] font-black uppercase leading-[1.45] tracking-[0.22em] text-[#F5EEE4]">
          SAME
          <br />
          CREATORS.
          <br />
          DEEPER
          <br />
          STORIES.
        </p>
      </div>

      {/* ───────────── GEOMETRIC SHAPES ───────────── */}

      {/* Mint */}
      <div
        className="absolute bottom-0 right-0 h-[235px] w-[190px] bg-[#54C29D]"
        style={{
          clipPath: "polygon(100% 0%, 100% 100%, 0% 100%, 0% 55%)",
        }}
      />

      {/* Coral */}
      <div
        className="absolute bottom-0 left-0 h-[140px] w-[115px] bg-[#F86158]"
        style={{
          clipPath: "polygon(0 0, 100% 50%, 0 100%)",
        }}
      />

      {/* Yellow */}
      <div
        className="absolute bottom-0 right-0 h-[108px] w-[105px] bg-[#F7E141]"
        style={{
          clipPath: "polygon(100% 0, 100% 100%, 0 100%)",
        }}
      />

      {/* ───────────── FOOTER ───────────── */}
      <div className="relative z-30 mt-auto flex flex-col items-center pb-3">
        <p className="mb-3 text-center text-[11px] font-black uppercase leading-[1.5] tracking-[0.22em] text-[#1D4248]">
          REAL DATA.
          <br />
          REAL INSIGHTS.
        </p>

        <p className="text-[10px] font-medium tracking-wide text-[#1D4248]">
          © 2026 rAIse
        </p>
      </div>
    </aside>
  );
}
function ChannelPlaceholder({
  variant = "logo",
  src,
  alt,
}: {
  variant?: "logo" | "banner";
  src?: string;
  alt?: string;
}) {
  if (variant === "banner") {
    if (src) {
      return (
        <div className="relative h-full min-h-[96px] overflow-hidden border-2 border-[#1D4248] bg-[#354244]">
          <img
            src={src}
            alt={alt || "Channel banner"}
            className="h-full w-full object-cover"
          />

          <div className="absolute inset-0 bg-[#1D4248]/25" />
        </div>
      );
    }

    return (
      <div className="relative h-full min-h-[96px] overflow-hidden border-2 border-[#1D4248] bg-[#354244]">
        <div
          className="absolute inset-0 opacity-80"
          style={{
            backgroundImage:
              "repeating-radial-gradient(ellipse at 20% 30%, transparent 0 14px, #F86158 15px 19px, transparent 20px 34px), repeating-radial-gradient(ellipse at 80% 70%, transparent 0 16px, #54C29D 17px 20px, transparent 21px 38px)",
          }}
        />

        <div className="absolute inset-0 bg-[#1D4248]/45" />

        <div className="relative flex h-full items-center justify-center">
          <div className="border-2 border-[#F5EEE4] bg-[#1D4248]/85 px-5 py-3 text-center">
            <p className="text-[9px] font-bold uppercase tracking-[0.25em] text-[#A2CCCE]">
              Channel banner
            </p>

            <p className="mt-1 text-xs font-black uppercase tracking-[0.12em] text-[#F5EEE4]">
              Placeholder
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (src) {
    return (
      <div className="aspect-square w-full overflow-hidden border-2 border-[#1D4248] bg-[#354244]">
        <img
          src={src}
          alt={alt || "Channel profile picture"}
          className="h-full w-full object-cover"
        />
      </div>
    );
  }

  return (
    <div className="flex aspect-square w-full items-center justify-center border-2 border-[#1D4248] bg-[#354244]">
      <div className="flex h-[70%] w-[70%] items-center justify-center border-2 border-[#A2CCCE] bg-[#1D4248]">
        <div className="text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center border-2 border-[#54C29D] text-lg font-black text-[#F86158]">
            ?
          </div>

          <p className="mt-2 text-[8px] font-bold uppercase tracking-[0.16em] text-[#F5EEE4]">
            Logo
          </p>
        </div>
      </div>
    </div>
  );
}

function ViewsTimelineChart({ timeline }: { timeline: any[] }) {
  
  const [zoomed, setZoomed] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState<any | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({
    x: 0,
    y: 0,
  });

  const points = useMemo(() => {
    if (!timeline?.length) return [];

    const dated = timeline
      .map((video: any) => ({
        ...video,
        date: new Date(video.published_at).getTime(),
        views: Number(video.views) || 0,
      }))
      .filter((item: any) => Number.isFinite(item.date))
      .sort((a: any, b: any) => a.date - b.date);

    // Normal mode: compress to max 180 points
    if (!zoomed && dated.length > 180) {
      const bucketSize = Math.ceil(dated.length / 180);
      const buckets: any[] = [];

      for (let i = 0; i < dated.length; i += bucketSize) {
        const bucket = dated.slice(i, i + bucketSize);

        buckets.push(
          bucket.reduce(
            (max: any, item: any) =>
              item.views > max.views ? item : max,
            bucket[0]
          )
        );
      }

      return buckets;
    }

    // Zoom mode: show every video
    return dated;
  }, [timeline, zoomed]);

  if (!points.length) {
    return (
      <div className="flex h-[300px] items-center justify-center border-2 border-[#1D4248] bg-[#354244] text-sm text-[#A2CCCE]">
        No timeline data available.
      </div>
    );
  }

  /*
   * In normal mode we keep the original width.
   *
   * In zoom mode the width grows according to the number
   * of years, allowing the graph to be horizontally scrolled.
   */
  const minDate = points[0].date;
  const maxDate = points[points.length - 1].date || minDate + 1;

  const minYear = new Date(minDate).getFullYear();
  const maxYear = new Date(maxDate).getFullYear();
  const yearCount = Math.max(maxYear - minYear + 1, 1);

  const width = zoomed
    ? Math.max(1100, yearCount * 7000)
    : 900;

  const height = 300;
  const padX = 44;
  const padY = 25;

  const max = Math.max(
    ...points.map((p) => p.views),
    1
  );

  const coords = points.map((point) => ({
    ...point,

    x:
      padX +
      ((point.date - minDate) /
        Math.max(maxDate - minDate, 1)) *
        (width - padX * 2),

    y:
      height -
      padY -
      (point.views / max) *
        (height - padY * 2),
  }));

  const line = coords
    .map(
      (p, i) =>
        `${i === 0 ? "M" : "L"} ${p.x.toFixed(
          2
        )} ${p.y.toFixed(2)}`
    )
    .join(" ");

  const area = `
    ${line}
    L ${coords[coords.length - 1].x.toFixed(2)} ${
      height - padY
    }
    L ${coords[0].x.toFixed(2)} ${height - padY}
    Z
  `;

  const topPoint = coords.reduce(
    (maxPoint, point) =>
      point.views > maxPoint.views
        ? point
        : maxPoint,
    coords[0]
  );

  /*
   * Normal mode:
   * Show approximately 6 date ticks.
   *
   * Zoom mode:
   * Show one tick per year.
   */
  const ticks = zoomed
    ? Array.from({ length: yearCount }, (_, i) => {
        const year = minYear + i;

        const yearDate = new Date(
          year,
          0,
          1
        ).getTime();

        const ratio =
          (yearDate - minDate) /
          Math.max(maxDate - minDate, 1);

        return {
          x:
            padX +
            Math.max(0, Math.min(1, ratio)) *
              (width - padX * 2),
          label: year.toString(),
        };
      })
    : Array.from({ length: 6 }, (_, i) => {
        const ratio = i / 5;

        return {
          x:
            padX +
            (width - padX * 2) * ratio,

          label: new Date(
            minDate +
              (maxDate - minDate) * ratio
          )
            .getFullYear()
            .toString(),
        };
      });

  /*
   * Find the point closest to the cursor.
   */
 const handleMouseMove = (
  event: MouseEvent<SVGSVGElement>
) => {
    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();

    const mouseX =
      ((event.clientX - rect.left) /
        rect.width) *
      width;

    let closest = coords[0];
    let closestDistance = Math.abs(
      mouseX - closest.x
    );

    for (const point of coords) {
      const distance = Math.abs(
        mouseX - point.x
      );

      if (distance < closestDistance) {
        closest = point;
        closestDistance = distance;
      }
    }

    setHoveredPoint(closest);

    /*
     * Position tooltip relative to the chart container.
     */
    const containerRect =
      svg.parentElement?.getBoundingClientRect();

    if (containerRect) {
      const tooltipX =
        event.clientX -
        containerRect.left;

      const tooltipY =
        event.clientY -
        containerRect.top;

      setTooltipPosition({
        x: tooltipX,
        y: tooltipY,
      });
    }
  };

  const handleMouseLeave = () => {
    setHoveredPoint(null);
  };

  return (
    <div
  className={`
    border-2 border-[#1D4248] bg-[#354244] p-3 sm:p-4
    transition-all duration-300
    ${
      expanded
  ? "-ml-[650px] w-[calc(100%+650px)] border-5 border-[#54C29D]"
  : "ml-0 w-full"
    }
  `}
>
      
      {/* ───────────────── HEADER ───────────────── */}

      <div className="flex items-center justify-between pb-2">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#A2CCCE]">
            Channel history
          </p>

          <p className="mt-1 text-lg font-black uppercase text-[#F5EEE4]">
            Views over time
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom state */}
          <span className="hidden border border-[#A2CCCE]/40 px-2 py-1 text-[9px] font-bold uppercase tracking-[0.12em] text-[#A2CCCE] sm:inline-flex">
            {zoomed
              ? "Year-by-year"
              : "Full timeline"}
          </span>
          <button
  type="button"
  onClick={() => setExpanded((value) => !value)}
  title={expanded ? "Shrink graph" : "Expand graph"}
  aria-label={expanded ? "Shrink graph" : "Expand graph"}
  className={`
    flex h-8 w-8 cursor-pointer items-center
    justify-center border transition-all duration-200
    ${
      expanded
        ? "border-[#F86158] bg-[#F86158] text-[#1D4248]"
        : "border-[#A2CCCE]/40 text-[#A2CCCE] hover:border-[#54C29D] hover:bg-[#54C29D]/10 hover:text-[#54C29D]"
    }
  `}
>
  <svg
    viewBox="0 0 24 24"
    className="h-[17px] w-[17px]"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
  >
    {expanded ? (
      <>
        <polyline points="9 15 9 9 15 9" />
        <polyline points="15 9 9 15" />
        <polyline points="15 15 15 9 9 9" />
      </>
    ) : (
      <>
        <polyline points="8 3 3 3 3 8" />
        <polyline points="16 3 21 3 21 8" />
        <polyline points="3 16 3 21 8 21" />
        <polyline points="21 16 21 21 16 21" />
      </>
    )}
  </svg>
</button>
          {/* Magnifying glass */}
          <button
            type="button"
            onClick={() => {
              setZoomed((value) => !value);
              setHoveredPoint(null);
            }}
            title={
              zoomed
                ? "Return to full timeline"
                : "Zoom into timeline"
            }
            aria-label={
              zoomed
                ? "Return to full timeline"
                : "Zoom into timeline"
            }
            className={`
              flex h-8 w-8 cursor-pointer items-center
              justify-center border transition-all
              duration-200
              ${
                zoomed
                  ? "border-[#F86158] bg-[#F86158] text-[#1D4248]"
                  : "border-[#A2CCCE]/40 text-[#A2CCCE] hover:border-[#54C29D] hover:bg-[#54C29D]/10 hover:text-[#54C29D]"
              }
            `}
          >
            <svg
              viewBox="0 0 24 24"
              className="h-[17px] w-[17px]"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <circle cx="11" cy="11" r="6.5" />
              <line x1="16" y1="16" x2="21" y2="21" />
            </svg>
          </button>
        </div>
      </div>

      {/* ───────────────── GRAPH ───────────────── */}

      <div className="relative overflow-hidden">
  {/* Tooltip */}
  {hoveredPoint && (
    <div
      className="pointer-events-none absolute z-30 w-[250px] -translate-x-1/2 -translate-y-full overflow-hidden border-2 border-[#1D4248] bg-[#F5EEE4] shadow-lg"
      style={{
        left: tooltipPosition.x,
        top: tooltipPosition.y - 12,
      }}
    >
      {/* Thumbnail */}
      {hoveredPoint.thumbnail_url && (
        <div className="h-[125px] w-full overflow-hidden bg-[#1D4248]">
          <img
            src={hoveredPoint.thumbnail_url}
            alt={hoveredPoint.title || "Video thumbnail"}
            className="h-full w-full object-cover"
          />
        </div>
      )}

      <div className="p-3">
        <p className="text-[9px] font-black uppercase tracking-[0.15em] text-[#F86158]">
          {new Date(
            hoveredPoint.date
          ).toLocaleDateString(undefined, {
            day: "2-digit",
            month: "short",
            year: "numeric",
          })}
        </p>

        <p className="mt-1 text-[12px] font-black leading-4 text-[#1D4248]">
          {hoveredPoint.title || "Untitled video"}
        </p>

        <div className="mt-2 flex items-center justify-between border-t border-[#1D4248]/15 pt-2">
          <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#354244]/60">
            Views
          </span>

          <span className="text-sm font-black text-[#54C29D]">
            {formatNumber(hoveredPoint.views)}
          </span>
        </div>

        {hoveredPoint.video_id && (
          <p className="mt-2 text-[8px] font-bold uppercase tracking-[0.1em] text-[#354244]/50">
            YouTube video
          </p>
        )}
      </div>
    </div>
  )}

        {/* Horizontal scrolling only in zoom mode */}
        <div
          className={
            zoomed
              ? "overflow-x-auto overflow-y-hidden pb-2"
              : "overflow-hidden"
          }
        >
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className={
  zoomed
    ? expanded
      ? "h-[470px] min-w-full"
      : "h-[300px] min-w-full"
    : expanded
      ? "h-[470px] w-full"
      : "h-[270px] w-full"
}
            style={{
              minWidth: zoomed
                ? `${width}px`
                : undefined,
            }}
            role="img"
            aria-label="Channel video views over time"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            {/* ───────────── GRID ───────────── */}

            {[0.25, 0.5, 0.75, 1].map(
              (ratio) => {
                const y =
                  height -
                  padY -
                  ratio *
                    (height -
                      padY * 2);

                return (
                  <line
                    key={ratio}
                    x1={padX}
                    x2={width - padX}
                    y1={y}
                    y2={y}
                    stroke="#A2CCCE"
                    strokeOpacity="0.18"
                    strokeDasharray="3 5"
                  />
                );
              }
            )}

            {/* ───────────── YEAR TICKS ───────────── */}

            {ticks.map((tick) => (
              <g
                key={`${tick.label}-${tick.x}`}
              >
                <line
                  x1={tick.x}
                  x2={tick.x}
                  y1={padY}
                  y2={height - padY}
                  stroke="#A2CCCE"
                  strokeOpacity={
                    zoomed ? "0.13" : "0.08"
                  }
                />

                <text
                  x={tick.x}
                  y={height - 5}
                  fill="#A2CCCE"
                  fontSize={zoomed ? "11" : "10"}
                  fontWeight={
                    zoomed ? "700" : "400"
                  }
                  textAnchor="middle"
                >
                  {tick.label}
                </text>
              </g>
            ))}

            {/* ───────────── AREA ───────────── */}

            <path
              d={area}
              fill="#54C29D"
              fillOpacity="0.14"
            />

            {/* ───────────── LINE ───────────── */}

            <path
              d={line}
              fill="none"
              stroke="#54C29D"
              strokeWidth="2.5"
              vectorEffect="non-scaling-stroke"
            />

{/* ───────────── HOVER GUIDE ───────────── */}

{hoveredPoint && (
  <>
    <line
      x1={hoveredPoint.x}
      x2={hoveredPoint.x}
      y1={padY}
      y2={height - padY}
      stroke="#F5EEE4"
      strokeOpacity="0.45"
      strokeDasharray="4 4"
      vectorEffect="non-scaling-stroke"
    />

    <circle
      cx={hoveredPoint.x}
      cy={hoveredPoint.y}
      r="7"
      fill="#F86158"
      stroke="#F5EEE4"
      strokeWidth="2"
      vectorEffect="non-scaling-stroke"
      className={
        hoveredPoint.video_id
          ? "cursor-pointer"
          : "cursor-default"
      }
      onClick={(e) => {
        e.stopPropagation();

        if (!hoveredPoint.video_id) return;

        window.open(
          `https://www.youtube.com/watch?v=${hoveredPoint.video_id}`,
          "_blank",
          "noopener,noreferrer"
        );
      }}
    />
  </>
)}
            {/* ───────────── HIGHEST POINT ───────────── */}

            <circle
              cx={topPoint.x}
              cy={topPoint.y}
              r="5"
              fill="#F86158"
              stroke="#F5EEE4"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />

            <text
              x={Math.min(
                topPoint.x + 10,
                width - 130
              )}
              y={Math.max(
                topPoint.y - 12,
                20
              )}
              fill="#F86158"
              fontSize="11"
              fontWeight="800"
            >
              {formatNumber(topPoint.views)}
            </text>
          </svg>
        </div>

        {/* Zoom hint */}
        {zoomed && (
          <div className="mt-1 flex items-center justify-between text-[8px] font-bold uppercase tracking-[0.14em] text-[#A2CCCE]/60">
            <span>
              Scroll horizontally to explore
            </span>

            <span>
              {points.length} videos
            </span>
          </div>
        )}
      </div>
    </div>
  );
} 

function TopGrowthEvents({
  events,
  onSelect,
}: {
  events: GrowthEvent[];
  onSelect: (event: GrowthEvent) => void;
}) {
  return (
    <div className="overflow-hidden border-2 border-[#1D4248] bg-[#354244]">
      <div className="flex items-center justify-between border-b-2 border-[#1D4248] bg-[#1D4248] px-4 py-3">
        <div>
          <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#F86158]">
            Event detection
          </p>

          <h2 className="mt-1 text-lg font-black uppercase text-[#F5EEE4]">
            Top growth events
          </h2>
        </div>

        <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-[#A2CCCE]">
          Top 5
        </span>
      </div>

      <div className="divide-y divide-[#A2CCCE]/15">
        {events.length === 0 ? (
          <div className="p-6 text-sm text-[#A2CCCE]">
            No growth events were detected.
          </div>
        ) : (
          events.map((event, index) => (
            <button
              key={event.video_id}
              type="button"
              onClick={() => onSelect(event)}
              className="
                group flex w-full cursor-pointer items-center gap-3
                px-3 py-3 text-left
                transition-all duration-200 ease-out
                hover:bg-[#1D4248]
                hover:px-4
              "
            >
              {/* Rank */}
              <span className="w-5 shrink-0 text-center text-sm font-black text-[#F86158]">
                {index + 1}
              </span>

              {/* Thumbnail */}
              <div className="h-12 w-20 shrink-0 overflow-hidden border border-[#A2CCCE]/30 bg-[#1D4248]">
                {event.thumbnail_url ? (
                  <img
                    src={event.thumbnail_url}
                    alt={event.title}
                    className="
                      h-full w-full object-cover
                      transition-transform duration-200
                      group-hover:scale-105
                    "
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center">
                    <span className="text-[8px] font-bold uppercase tracking-[0.08em] text-[#A2CCCE]">
                      Video
                    </span>
                  </div>
                )}
              </div>

              {/* Event information */}
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-bold text-[#F5EEE4] transition-colors duration-200 group-hover:text-[#54C29D]">
                  {event.title}
                </p>

                <p className="mt-1 text-[10px] text-[#A2CCCE]">
                  {formatDate(event.published_at)}
                </p>
              </div>

              {/* Views */}
              <div className="hidden shrink-0 text-right sm:block">
                <p className="text-sm font-black text-[#F5EEE4]">
                  {formatNumber(event.spike_views)}
                </p>

                <p className="mt-0.5 text-[9px] uppercase tracking-[0.08em] text-[#A2CCCE]">
                  views
                </p>
              </div>

              {/* Spike ratio */}
              <div className="w-[68px] shrink-0 border-2 border-[#F86158] bg-[#F86158] px-2 py-2 text-center transition-transform duration-200 group-hover:scale-105">
                <p className="text-base font-black leading-none text-[#1D4248]">
                  {formatRatio(event.spike_ratio)}
                </p>

                <p className="mt-0.5 text-[7px] font-black uppercase tracking-[0.1em] text-[#1D4248]/70">
                  spike
                </p>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

function ClassificationPanel({ counts }: { counts: Record<string, number> }) {
  const entries = [
    ["ONE_OFF", "One Off", POSTER.coral],
    ["TEMPORARY", "Temporary", POSTER.mint],
    ["SUSTAINED_THROUGHOUT", "Sustained Throughout", POSTER.banana],
    ["SUSTAINED_EVENTUAL", "Sustained Eventual", POSTER.lightBlue],
    ["INSUFFICIENT_DATA", "Insufficient Data", "#B8BCBD"],
  ] as const;
  const max = Math.max(...entries.map(([key]) => Number(counts[key] ?? 0)), 1);

  return (
    <div className="border-2 border-[#1D4248] bg-[#354244] p-4">
      <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#F86158]">Classification</p>
      <h2 className="mt-1 text-lg font-black uppercase text-[#F5EEE4]">Event classifications</h2>
      <div className="mt-4 space-y-3">
        {entries.map(([key, label, accent]) => {
          const value = Number(counts[key] ?? 0);
          return (
            <div key={key} className="grid grid-cols-[minmax(0,1fr)_42px] items-center gap-3">
              <div>
                <div className="mb-1 text-[10px] font-semibold text-[#F5EEE4]">{label}</div>
                <div className="h-2 bg-[#1D4248]">
                  <div className="h-full" style={{ width: `${Math.max(2, (value / max) * 100)}%`, backgroundColor: accent }} />
                </div>
              </div>
              <span className="text-right text-sm font-black text-[#F5EEE4]">{formatExactNumber(value)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function KeyInsightsPanel({ analysis }: { analysis: ChannelData["analysis"] }) {
  const contentTypes = Object.entries(analysis.content_types ?? {}).sort(([, a], [, b]) => Number(b) - Number(a));
  const classifications = Object.entries(analysis.classification_counts ?? {}).sort(([, a], [, b]) => Number(b) - Number(a));
  const topContent = contentTypes[0];
  const topClass = classifications[0];

  const insights = [
    {
      icon: "chart" as const,
      accent: POSTER.coral,
      title: `${formatExactNumber(analysis.events)} growth events detected`,
      description: "Events returned by the channel analysis.",
    },
    {
      icon: "trend" as const,
      accent: POSTER.mint,
      title: `${formatExactNumber(analysis.progressive_count)} progressive events`,
      description: "Events marked with a progressive trajectory.",
    },
    {
      icon: "document" as const,
      accent: POSTER.banana,
      title: topContent ? `${topContent[0]} is the largest format` : "Content formats",
      description: topContent ? `${formatExactNumber(Number(topContent[1]))} videos in this category.` : "Formats returned by the analysis.",
    },
    {
      icon: "event" as const,
      accent: POSTER.lightBlue,
      title: topClass ? `Most common: ${prettifyEventType(topClass[0])}` : "Event classifications",
      description: topClass ? `${formatExactNumber(Number(topClass[1]))} events in this class.` : "Classification counts returned by the analysis.",
    },
  ];

  return (
    <div className="border-2 border-[#1D4248] bg-[#354244] p-4">
      <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#54C29D]">Channel signals</p>
      <h2 className="mt-1 text-lg font-black uppercase text-[#F5EEE4]">Key insights</h2>
      <div className="divide-y divide-[#A2CCCE]/15">
        {insights.map((insight) => (
          <div key={insight.title} className="flex gap-3 py-3">
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center border-2" style={{ borderColor: insight.accent, color: insight.accent }}>
              <DashboardIcon name={insight.icon} size={17} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-[#F5EEE4]">{insight.title}</p>
              <p className="mt-0.5 text-[10px] leading-4 text-[#A2CCCE]">{insight.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EventWindowPreview({ event }: { event: GrowthEvent | null }) {
  if (!event) {
    return (
      <div className="border-2 border-[#1D4248] bg-[#354244] p-5 text-sm text-[#A2CCCE]">
        No event windows are available yet.
      </div>
    );
  }

  return (
    <div
      key={event.video_id}
      className="overflow-hidden border-2 border-[#1D4248] bg-[#F5EEE4] shadow-[4px_4px_0px_#1D4248]"
      style={{ animation: "eventWindowFade 260ms ease-out" }}
    >
      <div className="grid border-b-2 border-[#1D4248] bg-[#1D4248] md:grid-cols-[minmax(0,1fr)_220px_220px]">
        <div className="border-b-2 border-[#354244] px-4 py-3 md:border-b-0 md:border-r-2">
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#A2CCCE]">Selected event</p>
          <p className="mt-1 truncate text-sm font-black text-[#F5EEE4]">{event.title}</p>
          <p className="mt-1 text-[9px] uppercase tracking-[0.12em] text-[#A2CCCE]/70">{formatDate(event.published_at)}</p>
        </div>
        <div className="border-b-2 border-[#354244] px-4 py-3 md:border-b-0 md:border-r-2">
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#F86158]">Spike</p>
          <p className="mt-1 text-sm font-black text-[#F5EEE4]">{formatNumber(event.spike_views)} views</p>
        </div>
        <div className="px-4 py-3">
          <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#54C29D]">Spike ratio</p>
          <p className="mt-1 text-sm font-black text-[#F5EEE4]">{formatRatio(event.spike_ratio)}</p>
        </div>
      </div>

      <div className="space-y-7 p-3 sm:p-4">
        <div>
          <div className="mb-2 flex items-end justify-between border-b-2 border-[#354244] pb-2">
            <div>
              <p className="text-sm font-black uppercase text-[#1D4248]">Before</p>
              <p className="mt-0.5 text-[9px] uppercase tracking-[0.12em] text-[#354244]/60">{event.before_count} videos before the spike</p>
            </div>
<span className="inline-flex items-center rounded-md border border-[#F86158]/40 bg-[#F86158] px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em] text-[#354244]">
  Pre-event
</span>
          </div>
          <WindowVideoTable videos={event.before} />
        </div>

        <div>
          <div className="mb-2 flex items-end justify-between border-b-2 border-[#354244] pb-2">
            <div>
              <p className="text-sm font-black uppercase text-[#1D4248]">Short-term aftermath</p>
              <p className="mt-0.5 text-[9px] uppercase tracking-[0.12em] text-[#354244]/60">{event.short_term_count} videos after the spike</p>
            </div>
            <span className="inline-flex items-center rounded-md border border-[#54C29D]/40 bg-[#54C29D] px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em] text-[#354244]">
  Short-term
</span>
          </div>
          <WindowVideoTable videos={event.short_term} />
        </div>

        <div>
          <div className="mb-2 flex items-end justify-between border-b-2 border-[#354244] pb-2">
            <div>
              <p className="text-sm font-black uppercase text-[#1D4248]">Long-term aftermath</p>
              <p className="mt-0.5 text-[9px] uppercase tracking-[0.12em] text-[#354244]/60">{event.long_term_count} subsequent videos</p>
            </div>
            <span className="inline-flex items-center rounded-md border border-[#F7E141]/40 bg-[#F7E141] px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em] text-[#354244]">
  Long-term
</span>
          </div>
          <WindowVideoTable videos={event.long_term} />
        </div>
      </div>

      <div className="border-t-2 border-[#354244] bg-[#354244] px-4 py-3">
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-[10px]">
          <span className="text-[#A2CCCE]">Short-term:<strong className="ml-1 text-[#F5EEE4]">{event.short_term_retained ? "Retained" : "Not retained"}</strong></span>
          <span className="text-[#A2CCCE]">Long-term:<strong className="ml-1 text-[#F5EEE4]">{event.long_term_retained ? "Retained" : "Not retained"}</strong></span>
          <span className="text-[#A2CCCE]">Before baseline:<strong className="ml-1 text-[#F5EEE4]">{formatExactNumber(event.before_baseline)}</strong></span>
          <span className="text-[#A2CCCE]">Short-term change:<strong className="ml-1 text-[#F5EEE4]">{formatRatio(event.short_term_change)}</strong></span>
          <span className="text-[#A2CCCE]">Long-term change:<strong className="ml-1 text-[#F5EEE4]">{formatRatio(event.long_term_change)}</strong></span>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   MAIN PAGE
============================================================ */

function AnalysisContent() {
  const searchParams = useSearchParams();
  const channelUrl = searchParams.get("url")?.trim() || "";

  const [data, setData] = useState<ChannelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<GrowthEvent | null>(null);
  const [researchLoading, setResearchLoading] = useState(false);
  const [researchResult, setResearchResult] = useState<ResearchResult | null>(null);
  const [researchError, setResearchError] = useState<string | null>(null);

  async function fetchAnalysis() {
    if (!channelUrl) {
      setData(null);
      setError("No YouTube channel URL was provided.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedEvent(null);
    setExpandedEvent(null);
    setResearchResult(null);
    setResearchError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/analyze?channel_url=${encodeURIComponent(channelUrl)}`,
        { cache: "no-store" }
      );

      if (!response.ok) {
        let message = `Request failed with status ${response.status}`;
        try {
          const body = await response.json();
          if (body?.detail) message = body.detail;
        } catch {
          // Ignore JSON parse failure.
        }
        throw new Error(message);
      }

      const result: ChannelData = await response.json();
      setData(result);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Failed to load channel analysis.");
    } finally {
      setLoading(false);
    }
  }

  async function runResearch(event: GrowthEvent) {
    setSelectedEvent(event);
    setExpandedEvent(event.video_id);
    setResearchLoading(true);
    setResearchResult(null);
    setResearchError(null);

    if (!channelUrl) {
      setResearchError("No YouTube channel URL was provided.");
      setResearchLoading(false);
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/research?channel_url=${encodeURIComponent(channelUrl)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ event }),
        }
      );

      if (!response.ok) {
        let message = `Research request failed (${response.status})`;
        try {
          const body = await response.json();
          if (body?.detail) message = body.detail;
        } catch {
          // Ignore JSON parse failure.
        }
        throw new Error(message);
      }

      const result: ResearchResult = await response.json();

      if (!result?.success) {
        throw new Error(result?.error || "Research failed.");
      }

      if (!result?.research) {
        throw new Error("Research completed but no report was returned.");
      }

      setResearchResult(result);
    } catch (err) {
      setResearchError(err instanceof Error ? err.message : "Research failed.");
    } finally {
      setResearchLoading(false);
    }
  }

  useEffect(() => {
    fetchAnalysis();
  }, [channelUrl]);

  const keyEvents = useMemo(() => {
    if (!data) return [];

    const events = data.events;
    const result: { label: string; event: GrowthEvent }[] = [];

    const add = (label: string, event: GrowthEvent | null) => {
      if (event) result.push({ label, event });
    };

    add("Strongest Spike", getStrongestEvent(events));
    add("Earliest Spike", getEarliestEvent(events));
    add("One-off", getFirstEventOfType(events, "ONE_OFF"));
    add("Temporary", getFirstEventOfType(events, "TEMPORARY"));
    add("Sustained — Throughout", getFirstEventOfType(events, "SUSTAINED_THROUGHOUT"));
    add("Sustained — Eventual", getFirstEventOfType(events, "SUSTAINED_EVENTUAL"));
    add("Progressive", getFirstProgressiveEvent(events));

    const seen = new Set<string>();
    return result.filter(({ event }) => {
      if (seen.has(event.video_id)) return false;
      seen.add(event.video_id);
      return true;
    });
  }, [data]);

  const topGrowthEvents = useMemo(() => {
    if (!data?.events?.length) return [];
    return [...data.events]
      .sort((a, b) => Number(b.spike_ratio) - Number(a.spike_ratio))
      .slice(0, 5);
  }, [data]);

  const strongestEvent = useMemo(
    () => (data ? getStrongestEvent(data.events) : null),
    [data]
  );

  const activeEvent = selectedEvent ?? strongestEvent;

  function selectGrowthEvent(event: GrowthEvent) {
    setSelectedEvent(event);
    setExpandedEvent(null);
    setResearchResult(null);
    setResearchError(null);

    requestAnimationFrame(() => {
      document.getElementById("event-aftermath")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  if (loading) return <LoadingScreen channelUrl={channelUrl} />;
  if (error) return <ErrorScreen error={error} onRetry={fetchAnalysis} />;
  if (!data) return null;

  return (
    <main
      className="min-h-screen bg-[#F5EEE4] text-[#1D4248]"
      style={{
        backgroundImage:
          "radial-gradient(rgba(29,66,72,0.055) 0.65px, transparent 0.65px), radial-gradient(rgba(248,97,88,0.035) 0.6px, transparent 0.6px)",
        backgroundPosition: "0 0, 7px 11px",
        backgroundSize: "13px 13px, 17px 17px",
      }}
    >
      <style jsx global>{`
        @keyframes eventWindowFade {
          from {
            opacity: 0.15;
            transform: translateY(6px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      <DashboardSidebar />

      <div className="min-h-screen lg:pl-[218px]">
        <header className="border-b-2 border-[#1D4248] bg-[#F5EEE4]/95 backdrop-blur-sm">
          <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-5 px-4 py-3 sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-9 w- shrink-0 items-center justify-center border-2 border-[#1D4248] bg-[#F86158] text-lg font-black text-[#1D4248]">rAIse</div>
              <div className="min-w-0">
                <p className="text-[9px] font-bold uppercase tracking-[0.24em] text-[#354244]">YouTube growth intelligence</p>
                <p className="mt-0.5 truncate text-[10px] font-medium text-[#354244]/65">Same creators. Deeper stories.</p>
              </div>
            </div>
            <div className="hidden items-center gap-4 sm:flex">
              <div className="text-right">
                <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#F86158]">Channel analysis</p>
                <p className="mt-1 max-w-[260px] truncate text-sm font-black text-[#1D4248]">{data.channel.name}</p>
              </div>
              <div className="h-10 w-px bg-[#1D4248]/20" />
              <div className="border-2 border-[#1D4248] bg-[#354244] px-3 py-2 text-[9px] font-bold uppercase tracking-[0.14em] text-[#F5EEE4]">Live report</div>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-[1500px] px-4 pb-12 pt-4 sm:px-6 lg:px-8">
          <section className="border-b-2 border-[#1D4248]">
            <div className="grid min-h-[190px] border-2 border-[#1D4248] bg-[#F5EEE4] lg:grid-cols-[150px_minmax(0,1fr)_430px]">
              <div className="hidden border-r-2 border-[#1D4248] p-3 lg:block">
                {data.channel.profile_picture ? (
  <div className="aspect-square w-full overflow-hidden border-2 border-[#1D4248] bg-[#354244]">
    <img
      src={data.channel.profile_picture}
      alt={data.channel.name}
      className="h-full w-full object-cover"
    />
  </div>
) : (
  <ChannelPlaceholder variant="logo" />
)}
              </div>

              <div className="flex min-w-0 flex-col justify-center px-5 py-6 sm:px-7">
                <p className="text-xs font-black uppercase tracking-[0.2em] text-[#F86158]">Channel analysis</p>
                <div className="mt-1 flex min-w-0 items-center gap-3">
                  <h1 className="truncate text-4xl font-black uppercase leading-none tracking-[-0.055em] text-[#1D4248] sm:text-5xl xl:text-6xl">{data.channel.name}</h1>
                  <span className="hidden h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#54C29D] text-sm font-black text-[#1D4248] sm:flex">✓</span>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <p className="truncate font-mono text-[9px] text-[#354244]/65">{data.channel.id}</p>
                  <span className="h-1 w-1 rounded-full bg-[#F86158]" />
                  <p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#354244]/60">{formatExactNumber(data.channel.video_count)} videos</p>
                </div>
                <p className="mt-4 max-w-2xl text-xs leading-5 text-[#354244]/75">
                  {data.channel.description || "Creator channel growth analysis and evidence-backed event detection."}
                </p>
              </div>

              <div className="hidden h-full lg:block">
  {data.channel.banner_url ? (
    <img
      src={data.channel.banner_url}
      alt={`${data.channel.name} banner`}
      className="h-full min-h-[140px] w-full object-contain"
    />
  ) : (
    <ChannelPlaceholder variant="banner" />
  )}
</div>
            </div>
          </section>

          <section className="mt-2 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
            <StatCard label="Subscribers" value={formatNumber(data.channel.subscribers)} accent={COLORS.mintLeaf} />
            <StatCard label="Total views" value={formatNumber(data.channel.views)} accent={COLORS.lightBlue} />
            <StatCard label="Total videos" value={formatNumber(data.analysis.total_videos)} accent={COLORS.bananaCream} />
            <StatCard label="Detected events" value={formatNumber(data.analysis.events)} accent={COLORS.vibrantCoral} />
            <StatCard label="Progressive events" value={formatNumber(data.analysis.progressive_count)} accent={COLORS.mintLeaf} />
          </section>
                    <section className="mt-8">
            <div className="mb-3 flex flex-col gap-2 border-b-2 border-[#1D4248] pb-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#F86158]">Event detection</p>
                <h2 className="mt-1 text-xl font-black uppercase text-[#1D4248]">Key growth events</h2>
                <p className="mt-1 text-xs text-[#354244]/65">Select an event to update the before & aftermath analysis below.</p>
              </div>
              <div className="border-2 border-[#1D4248] bg-[#354244] px-3 py-2 text-[9px] font-bold uppercase tracking-[0.14em] text-[#F5EEE4]">{data.events.length.toLocaleString()} events</div>
            </div>

            {keyEvents.length === 0 ? (
              <div className="border-2 border-[#1D4248] bg-[#354244] p-8 text-center">
                <p className="text-sm text-[#A2CCCE]">No key growth events were detected.</p>
              </div>
            ) : (
              <div className="grid gap-3 lg:grid-cols-2">
                {keyEvents.map(({ label, event }) => (
                  <GrowthEventCard
                    key={`${label}-${event.video_id}`}
                    label={label}
                    event={event}
                    selected={
                      selectedEvent?.video_id === event.video_id ||
                      (!selectedEvent && strongestEvent?.video_id === event.video_id)
                    }
                    expanded={false}
                    researchLoading={researchLoading && selectedEvent?.video_id === event.video_id}
                    onToggle={() => selectGrowthEvent(event)}
                    onRunResearch={() => runResearch(event)}
                  />
                ))}
              </div>
            )}
          </section>
            {selectedEvent && (
            <section className="mt-5">
              <SelectedEventPanel
                event={selectedEvent}
                researchLoading={researchLoading}
                researchResult={researchResult}
                researchError={researchError}
                onRunResearch={() => runResearch(selectedEvent)}
              />
            </section>
            
          )}
          
          <section id="event-aftermath" className="scroll-mt-6 mt-3">
            <div className="mb-2 flex flex-col gap-2 border-b-2 border-[#1D4248] pb-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#F86158]">Event context</p>
                <h2 className="mt-1 text-xl font-black uppercase text-[#1D4248]">Before & aftermath</h2>
                <p className="mt-1 text-xs text-[#354244]/65">
                  {activeEvent ? `Showing the full video windows for “${activeEvent.title}”.` : "Select a growth event above to inspect its video windows."}
                </p>
              </div>
              <p className="hidden text-[9px] font-bold uppercase tracking-[0.14em] text-[#354244]/55 sm:block">
                {selectedEvent ? "Selected event" : "Strongest detected spike"}
              </p>
            </div>
            <EventWindowPreview event={activeEvent} />
          </section>

          

          <section className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,1.04fr)_minmax(430px,0.96fr)]">
            <TopGrowthEvents
              events={topGrowthEvents}
              onSelect={(event) => {
                selectGrowthEvent(event);
              }}
            />
            <ViewsTimelineChart timeline={data.timeline} />
          </section>

          <section className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
            <ClassificationPanel counts={data.analysis.classification_counts} />
            <KeyInsightsPanel analysis={data.analysis} />
          </section>

          


          <section className="mt-8 grid gap-3 lg:grid-cols-2">
            <div className="border-2 border-[#1D4248] bg-[#354244] p-4">
              <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#54C29D]">Distribution</p>
              <h2 className="mt-1 text-lg font-black uppercase text-[#F5EEE4]">Progressive growth</h2>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <StatCard label="Progressive events" value={formatNumber(data.analysis.progressive_count)} accent={COLORS.mintLeaf} />
                <StatCard label="Other events" value={formatNumber(Math.max(0, data.analysis.events - data.analysis.progressive_count))} accent={COLORS.lightBlue} />
              </div>
            </div>

            <div className="border-2 border-[#1D4248] bg-[#354244] p-4">
              <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#F7E141]">Configuration</p>
              <h2 className="mt-1 text-lg font-black uppercase text-[#F5EEE4]">Detection settings</h2>
              <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
                <StatCard label="Before window" value={formatExactNumber(data.settings.before_count)} accent={COLORS.lightBlue} />
                <StatCard label="Short window" value={formatExactNumber(data.settings.short_count)} accent={COLORS.mintLeaf} />
                <StatCard label="Long window" value={formatExactNumber(data.settings.long_count)} accent={COLORS.bananaCream} />
                <StatCard label="Spike threshold" value={`${data.settings.spike_threshold.toFixed(1)}×`} accent={COLORS.vibrantCoral} />
                <StatCard label="Retention threshold" value={`${data.settings.retention_threshold.toFixed(1)}×`} accent={COLORS.lightBlue} />
              </div>
            </div>
          </section>

          <section className="mt-8">
  <div className="mb-3 flex items-end justify-between border-b-2 border-[#1D4248] pb-2">
    <div>
      <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#54C29D]">
        Channel history
      </p>
      <h2 className="mt-1 text-xl font-black uppercase text-[#1D4248]">
        Full video timeline
      </h2>
    </div>

    <p className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#354244]/55">
      {data.timeline.length.toLocaleString()} videos
    </p>
  </div>

  <div className="overflow-hidden border-2 border-[#1D4248] bg-[#354244]">
    <div className="max-h-[560px] overflow-auto">
      <table className="w-full min-w-[700px] text-left">
        <thead className="sticky top-0 z-10 border-b-2 border-[#1D4248] bg-[#A2CCCE]">
          <tr>
            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-[0.12em] text-[#1D4248]">
              Video
            </th>

            <th className="px-4 py-3 text-[9px] font-black uppercase tracking-[0.12em] text-[#1D4248]">
              Date
            </th>

            <th className="px-4 py-3 text-right text-[9px] font-black uppercase tracking-[0.12em] text-[#1D4248]">
              Views
            </th>

            <th className="px-4 py-3 text-right text-[9px] font-black uppercase tracking-[0.12em] text-[#1D4248]">
              Engagement
            </th>

            <th className="px-4 py-3 text-right text-[9px] font-black uppercase tracking-[0.12em] text-[#1D4248]">
              State
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-[#A2CCCE]/15">
          {data.timeline.map((video: any, index: number) => {
            const isSpike = video.is_spike === true;

            return (
<tr
  key={video.video_id ?? index}
  onClick={() => {
    if (!isSpike || !video.video_id) return;

    const matchingEvent = data.events.find(
      (event) => event.video_id === video.video_id
    );

    if (!matchingEvent) return;

    selectGrowthEvent(matchingEvent);
  }}
  className={`transition ${
    isSpike
      ? "cursor-pointer hover:bg-[#1D4248]"
      : "hover:bg-[#1D4248]"
  }`}
>
  <td className="max-w-[520px] px-4 py-3">
    <button
      type="button"
      onClick={() => {
  if (!video.video_id) return;

  if (isSpike) {
    const matchingEvent = data.events.find(
      (event) => event.video_id === video.video_id
    );

    if (matchingEvent) {
      setSelectedEvent(matchingEvent);

      requestAnimationFrame(() => {
        document
          .getElementById("before-aftermath")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      });
    }
  }

  window.open(
    `https://www.youtube.com/watch?v=${video.video_id}`,
    "_blank",
    "noopener,noreferrer"
  );
}}
      className="block max-w-full cursor-pointer truncate text-left text-sm font-medium text-[#F5EEE4] transition-colors duration-150 hover:text-[#F86158] hover:underline"
    >
      {video.title ?? "Untitled video"}
    </button>
  </td>

  <td className="whitespace-nowrap px-4 py-3 text-xs text-[#A2CCCE]">
    {formatDate(video.published_at)}
  </td>

  <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-bold text-[#F5EEE4]">
    {formatNumber(video.views)}
  </td>

  <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-[#A2CCCE]">
    {video.engagement_rate !== undefined
      ? `${Number(video.engagement_rate).toFixed(2)}%`
      : "—"}
  </td>

  <td className="whitespace-nowrap px-4 py-3 text-right">
    <span
      className={`inline-flex items-center rounded-md border px-2 py-1 text-[9px] font-black uppercase tracking-[0.12em] ${
        isSpike
          ? "border-[#F86158]/40 bg-[#F86158]/15 text-[#F86158]"
          : "border-[#A2CCCE]/30 bg-[#A2CCCE]/10 text-[#A2CCCE]"
      }`}
    >
      {isSpike ? "Spike" : "Normal"}
    </span>
  </td>
</tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
</section>

          <footer className="mt-10 border-t-2 border-[#1D4248] py-6">
            <div className="flex flex-col gap-2 text-[9px] font-bold uppercase tracking-[0.14em] text-[#354244]/55 sm:flex-row sm:items-center sm:justify-between">
              <span>rAIse — Growth & Spike Analyzer</span>
              <span>Quantitative analysis · Research follows event selection</span>
            </div>
          </footer>
        </div>
      </div>
    </main>
  );
}
export default function Home() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-[#F5EEE4] text-[#1D4248]">
          <p className="text-sm font-bold">
            Loading analysis...
          </p>
        </main>
      }
    >
      <AnalysisContent />
    </Suspense>
  );
}