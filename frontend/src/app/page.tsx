"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  ArrowRight,
  Link2,
  BarChart3,
  Search,
  FileText,
  Users,
} from "lucide-react";

export default function Home() {
  const router = useRouter();

  const [channelUrl, setChannelUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /* ============================================================= */
  /* URL VALIDATION                                                 */
  /* ============================================================= */

  const isValidYouTubeUrl = (value: string) => {
    try {
      const url = new URL(value);

      return (
        url.hostname === "youtube.com" ||
        url.hostname === "www.youtube.com" ||
        url.hostname === "m.youtube.com" ||
        url.hostname === "youtu.be" ||
        url.hostname === "www.youtu.be"
      );
    } catch {
      return false;
    }
  };


  /* ============================================================= */
  /* ANALYZE                                                        */
  /* ============================================================= */

  const handleAnalyze = (e?: FormEvent<HTMLFormElement>) => {
    e?.preventDefault();

    setError("");

    const trimmedUrl = channelUrl.trim();

    if (!trimmedUrl) {
      setError("Enter a YouTube channel URL.");
      return;
    }

    if (!isValidYouTubeUrl(trimmedUrl)) {
      setError("Please enter a valid YouTube channel URL.");
      return;
    }

    setLoading(true);

    /*
     * Keep the URL available to the analysis page as well.
     */
    localStorage.setItem("raise_channel_url", trimmedUrl);

    /*
     * Navigate to the existing analysis dashboard.
     *
     * Example:
     *
     * /analysis?url=https%3A%2F%2Fwww.youtube.com%2F%40markiplier
     */
    router.push(`/analysis?url=${encodeURIComponent(trimmedUrl)}`);
  };


  return (
    <main className="relative min-h-screen overflow-hidden bg-[#eee9dc] text-[#171b1b]">

      {/* ========================================================= */}
      {/* BACKGROUND                                                 */}
      {/* ========================================================= */}

      <div className="pointer-events-none fixed inset-0 -z-10">
        <Image
          src="/images/background.png"
          alt=""
          fill
          priority
          className="object-cover"
          sizes="100vw"
        />
      </div>


      {/* ========================================================= */}
      {/* HEADER                                                      */}
      {/* ========================================================= */}

      <header className="relative z-20 mx-auto flex h-[70px] w-full max-w-[1500px] items-center justify-between px-6 sm:px-10 lg:px-16">

        {/* Logo */}
        <a href="/" className="block shrink-0">
          <Image
            src="/images/rAIse_logo.png"
            alt="rAIse"
            width={190}
            height={90}
            priority
            className="h-auto w-[115px] sm:w-[135px] lg:w-[115px]"
          />
        </a>


        {/* Navigation */}
        <nav className="hidden items-center gap-10 text-[13px] font-medium tracking-wide text-[#202525] md:flex">

          <a
            href="#how-it-works"
            className="transition-opacity hover:opacity-50"
          >
            How it works
          </a>

          <a
            href="#features"
            className="transition-opacity hover:opacity-50"
          >
            Features
          </a>

          <a
            href="#examples"
            className="transition-opacity hover:opacity-50"
          >
            Examples
          </a>

          <a
            href="#about"
            className="transition-opacity hover:opacity-50"
          >
            About
          </a>

        </nav>


        {/* Get Started */}
        <button
          type="button"
          onClick={() => {
            document
              .getElementById("analyze")
              ?.scrollIntoView({ behavior: "smooth" });
          }}
          className="group flex items-center gap-3 bg-[#171b1b] px-5 py-2.5 text-sm font-medium text-[#f4f0e5] transition-all hover:bg-[#252b2b]"
        >
          Get Started

          <ArrowRight
            size={17}
            strokeWidth={1.8}
            className="transition-transform group-hover:translate-x-1"
          />
        </button>

      </header>


      {/* ========================================================= */}
      {/* HERO                                                        */}
      {/* ========================================================= */}

      <section className="relative mx-auto min-h-[calc(100vh-70px)] w-full max-w-[1500px] px-6 pb-10 sm:px-10 lg:px-16">


        {/* ======================================================= */}
        {/* VERTICAL LABEL                                            */}
        {/* ======================================================= */}

        <div className="absolute left-2 top-[145px] hidden xl:block">

          <div className="flex items-center gap-4">

            <div className="h-[120px] w-px bg-[#171b1b]/50" />

            <span
              className="text-[10px] font-medium tracking-[0.22em] text-[#252a29]"
              style={{
                writingMode: "vertical-rl",
                transform: "rotate(180deg)",
              }}
            >
              YOUTUBE GROWTH ANALYSIS
            </span>

          </div>

        </div>


        {/* ======================================================= */}
        {/* HERO GRID                                                 */}
        {/* ======================================================= */}

        <div className="relative grid min-h-[760px] grid-cols-1 lg:grid-cols-[0.95fr_1.05fr]">


          {/* ===================================================== */}
          {/* LEFT SIDE                                               */}
          {/* ===================================================== */}

          <div className="relative z-10 flex flex-col justify-center pt-14 lg:pt-0">


            {/* Eyebrow */}
            <div className="mb-5 flex items-center gap-3">

              <span className="h-[2px] w-8 bg-[#d8342f]" />

              <p className="text-[12px] font-semibold uppercase tracking-[0.18em] text-[#d8342f]">
                Turn creators into case studies
              </p>

            </div>


            {/* Main headline image */}
            <div className="relative w-full max-w-[650px]">

              <Image
                src="/images/MainText.png"
                alt="Understand what made a creator grow"
                width={1700}
                height={850}
                priority
                className="h-auto w-full object-contain object-left"
              />

            </div>


            {/* Description */}
            <p className="mt-7 max-w-[590px] text-[17px] leading-7 text-[#242928] sm:text-[18px]">
              Paste a YouTube channel URL and rAIse will find the
              biggest growth moments, then use AI to explain why
              they happened.
            </p>


            {/* =================================================== */}
            {/* URL INPUT                                              */}
            {/* =================================================== */}

            <form
              id="analyze"
              onSubmit={handleAnalyze}
              className="mt-9 w-full max-w-[650px]"
            >

              <div
                className={`flex min-h-[72px] flex-col border bg-[#f4f0e5]/95 shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition-all sm:flex-row ${
                  error
                    ? "border-[#d8342f]"
                    : "border-[#171b1b]/60 focus-within:border-[#171b1b]"
                }`}
              >

                {/* Input */}
                <div className="flex min-w-0 flex-1 items-center px-5">

                  <Link2
                    size={20}
                    strokeWidth={1.8}
                    className="mr-4 shrink-0 text-[#222827]"
                  />

                  <input
                    type="url"
                    value={channelUrl}
                    onChange={(e) => {
                      setChannelUrl(e.target.value);

                      if (error) {
                        setError("");
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();

                        if (!loading) {
                          handleAnalyze();
                        }
                      }
                    }}
                    placeholder="https://www.youtube.com/@channel"
                    disabled={loading}
                    className="w-full bg-transparent text-[15px] text-[#171b1b] outline-none placeholder:text-[#777b78] disabled:cursor-not-allowed disabled:opacity-60"
                  />

                </div>


                {/* Analyze button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="group flex min-h-[60px] items-center justify-center gap-3 bg-[#d8342f] px-7 text-[15px] font-semibold text-white transition-all hover:bg-[#bd2b27] disabled:cursor-not-allowed disabled:opacity-70 sm:min-h-0"
                >

                  {loading ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />

                      Analyzing
                    </>
                  ) : (
                    <>
                      Analyze Channel

                      <ArrowRight
                        size={19}
                        strokeWidth={1.8}
                        className="transition-transform group-hover:translate-x-1"
                      />
                    </>
                  )}

                </button>

              </div>


              {/* Input metadata */}
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-[#777b78]">

                <span>
                  No login required
                </span>

                <span className="h-3 w-px bg-[#777b78]/50" />

                <span>
                  Works with any public YouTube channel
                </span>

              </div>


              {/* Error */}
              {error && (
                <p className="mt-3 text-[12px] font-medium text-[#c52d29]">
                  {error}
                </p>
              )}

            </form>


            {/* =================================================== */}
            {/* REAL DATA ANNOTATION                                  */}
            {/* =================================================== */}

            <div className="relative mt-5 hidden w-fit translate-x-[390px] lg:block">

              <svg
                width="100"
                height="65"
                viewBox="0 0 100 65"
                fill="none"
                className="absolute -left-24 -top-16"
              >

                <path
                  d="M12 58C25 39 48 22 78 10"
                  stroke="#171b1b"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />

                <path
                  d="M69 8L78 10L73 18"
                  stroke="#171b1b"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

              </svg>


              <p
                className="rotate-[-5deg] text-[13px] font-semibold leading-5 text-[#171b1b]"
                style={{
                  fontFamily: "cursive",
                }}
              >
                REAL DATA.
                <br />
                REAL INSIGHTS.
              </p>

            </div>

          </div>


          {/* ===================================================== */}
          {/* RIGHT SIDE                                               */}
          {/* ===================================================== */}

          <div className="relative z-10 hidden min-h-[760px] lg:block">


            {/* Main poster */}
            <div className="absolute inset-0 flex items-center justify-center">

              <Image
                src="/images/MainPagePoster.png"
                alt=""
                width={1500}
                height={1500}
                priority
                className="h-auto w-[108%] max-w-none object-contain"
              />

            </div>


            {/* SAME CREATORS annotation */}
            <div className="absolute right-[8%] top-[12%] z-20">

              <div className="relative rotate-[-6deg]">

                <p
                  className="text-[18px] font-semibold leading-6 text-[#171b1b]"
                  style={{
                    fontFamily: "cursive",
                  }}
                >
                  SAME
                  <br />
                  CREATORS.
                  <br />
                  DEEPER
                  <br />
                  STORIES.
                </p>

                <div className="mt-1 ml-1 h-[2px] w-[75px] rotate-[-5deg] bg-[#d8342f]" />

              </div>

            </div>


            {/* DATA + AI annotation */}
            <div className="absolute right-[1%] top-[40%] z-20 hidden xl:block">

              <div className="border-l border-[#171b1b]/30 pl-5">

                <p className="text-[11px] font-medium uppercase leading-6 tracking-[0.16em] text-[#171b1b]">
                  DATA
                  <br />
                  +
                  <br />
                  AI
                  <br />
                  =
                  <br />
                  DEEPER
                  <br />
                  INSIGHTS
                </p>

              </div>

            </div>


            {/* MORE THAN VIEWS annotation */}
            <div className="absolute left-[18%] top-[60%] z-20 hidden xl:block">

              <p className="text-[11px] font-medium uppercase leading-5 tracking-[0.15em] text-[#171b1b]">
                MORE
                <br />
                THAN
                <br />
                VIEWS
              </p>

            </div>

          </div>

        </div>


        {/* ======================================================= */}
        {/* FEATURE STRIP                                             */}
        {/* ======================================================= */}

        <section
          id="features"
          className="relative z-20 border-t border-[#171b1b]/30"
        >

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">

            <Feature
              icon={
                <BarChart3
                  size={36}
                  strokeWidth={1.6}
                />
              }
              title="Detect growth events"
              description="Find the biggest spikes"
            />

            <Feature
              icon={
                <Search
                  size={36}
                  strokeWidth={1.6}
                />
              }
              title="AI research"
              description="Understand what drove them"
            />

            <Feature
              icon={
                <FileText
                  size={36}
                  strokeWidth={1.6}
                />
              }
              title="Actionable insights"
              description="Learn from real data"
            />

            <Feature
              icon={
                <Users
                  size={36}
                  strokeWidth={1.6}
                />
              }
              title="For any creator"
              description="Works with any public channel"
            />

          </div>

        </section>

      </section>


      {/* ========================================================= */}
      {/* HOW IT WORKS                                               */}
      {/* ========================================================= */}

      <section
        id="how-it-works"
        className="relative border-t border-[#171b1b]/15 px-6 py-24 sm:px-10 lg:px-16"
      >

        <div className="mx-auto max-w-[1200px]">


          <div className="mb-16 max-w-[650px]">

            <p className="mb-4 text-xs font-semibold uppercase tracking-[0.18em] text-[#d8342f]">
              How it works
            </p>

            <h2 className="text-4xl font-black uppercase tracking-[-0.04em] sm:text-5xl">
              From a channel
              <br />
              to a growth story.
            </h2>

          </div>


          <div className="grid gap-px border border-[#171b1b]/20 bg-[#171b1b]/20 md:grid-cols-3">

            <Step
              number="01"
              title="Analyze"
              text="Give rAIse a public YouTube channel and let the system build its historical dataset."
            />

            <Step
              number="02"
              title="Find the spikes"
              text="Growth events are detected by comparing videos against the channel's historical baseline."
            />

            <Step
              number="03"
              title="Understand why"
              text="AI research connects the growth event with audience activity, topics, context and evidence."
            />

          </div>

        </div>

      </section>


      {/* ========================================================= */}
      {/* ABOUT / CTA                                                */}
      {/* ========================================================= */}

      <section
        id="about"
        className="border-t border-[#171b1b]/15 px-6 py-24 sm:px-10 lg:px-16"
      >

        <div className="mx-auto max-w-[1200px]">

          <div className="relative overflow-hidden border border-[#171b1b]/30 bg-[#171b1b] px-8 py-16 text-[#f4f0e5] sm:px-14">


            {/* Decorative red block */}
            <div className="absolute right-0 top-0 h-24 w-24 bg-[#d8342f]" />


            {/* Decorative teal block */}
            <div className="absolute bottom-0 left-0 h-16 w-32 bg-[#168f8c]" />


            <div className="relative z-10 max-w-[700px]">

              <p className="mb-4 text-xs font-semibold uppercase tracking-[0.18em] text-[#ef4a43]">
                Start exploring
              </p>

              <h2 className="text-4xl font-black uppercase tracking-[-0.04em] sm:text-6xl">
                Find out what
                <br />
                made them grow.
              </h2>

              <p className="mt-6 max-w-[580px] text-base leading-7 text-[#f4f0e5]/70">
                Turn a creator&apos;s history into a structured growth
                case study — backed by data, research and evidence.
              </p>


              <button
                type="button"
                onClick={() => {
                  document
                    .getElementById("analyze")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
                className="group mt-8 flex items-center gap-3 bg-[#d8342f] px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-[#ef403a]"
              >

                Analyze a channel

                <ArrowRight
                  size={18}
                  className="transition-transform group-hover:translate-x-1"
                />

              </button>

            </div>

          </div>

        </div>

      </section>


      {/* ========================================================= */}
      {/* FOOTER                                                      */}
      {/* ========================================================= */}

      <footer className="border-t border-[#171b1b]/20 px-6 py-8 sm:px-10 lg:px-16">

        <div className="mx-auto flex max-w-[1500px] flex-col items-center justify-between gap-4 text-xs text-[#666b68] sm:flex-row">

          <div className="flex items-center gap-3">

            <Image
              src="/images/rAIse_logo.png"
              alt="rAIse"
              width={100}
              height={50}
              className="w-[75px]"
            />

            <span>
              Creator growth, explained.
            </span>

          </div>

          <span>
            © {new Date().getFullYear()} rAIse
          </span>

        </div>

      </footer>

    </main>
  );
}


/* =============================================================== */
/* FEATURE COMPONENT                                               */
/* =============================================================== */

function Feature({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="group flex min-h-[145px] flex-col justify-center border-b border-[#171b1b]/20 p-7 transition-colors hover:bg-[#171b1b]/[0.035] md:border-r md:last:border-r-0 lg:border-b-0">

      <div className="mb-5 text-[#171b1b] transition-transform duration-300 group-hover:-translate-y-1">
        {icon}
      </div>

      <h3 className="text-[15px] font-bold">
        {title}
      </h3>

      <p className="mt-1 text-[13px] text-[#6e7370]">
        {description}
      </p>

    </div>
  );
}


/* =============================================================== */
/* STEP COMPONENT                                                  */
/* =============================================================== */

function Step({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="bg-[#eee9dc] p-8 sm:p-10">

      <p className="font-mono text-xs text-[#d8342f]">
        {number}
      </p>

      <h3 className="mt-8 text-2xl font-black uppercase tracking-[-0.03em]">
        {title}
      </h3>

      <p className="mt-4 text-sm leading-6 text-[#666b68]">
        {text}
      </p>

    </div>
  );
}