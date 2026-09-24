import React from "react";
import { Link, Navigate } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";
import { useAuth } from "../context/AuthContext";

const Landing: React.FC = () => {
  const { t } = useLanguage();
  const { user } = useAuth();

  // Landing is the guest marketing page — logged-in farmers land on the
  // Dashboard instead (their real "home" per the product's own design).
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const steps = [
    { title: t("landing_step1_title"), desc: t("landing_step1_desc") },
    { title: t("landing_step2_title"), desc: t("landing_step2_desc") },
    { title: t("landing_step3_title"), desc: t("landing_step3_desc") },
  ];

  return (
    <div>
      <section className="px-4 md:px-8 pt-12 pb-16 md:pt-20 md:pb-24">
        <div className="mx-auto max-w-6xl grid md:grid-cols-2 gap-12 md:gap-8 items-center">
          <div>
            <h1 className="text-3xl md:text-[2.75rem] leading-[1.1] font-semibold text-earth-900 mb-5">
              {t("landing_hero_title")}
            </h1>
            <p className="text-base md:text-lg text-earth-700 max-w-md mb-8 leading-relaxed">
              {t("landing_hero_subtitle")}
            </p>
            <div className="flex flex-wrap items-center gap-4 mb-6">
              <Link
                to="/register"
                className="bg-primary-600 text-white px-6 py-3 rounded-md font-semibold hover:bg-primary-700 transition-colors"
              >
                {t("landing_cta")}
              </Link>
              <Link to="/login" className="text-earth-700 font-medium hover:text-earth-900 text-sm">
                {t("landing_secondary_login")}
              </Link>
            </div>
            <p className="text-xs text-earth-500">{t("landing_languages_badge")}</p>
          </div>

          {/* Literal representation of the product mechanism — not stock
              imagery. A leaf, a scan sweep, and a labeled example result. */}
          <div className="relative mx-auto w-full max-w-sm aspect-square" aria-hidden="true">
            <div className="w-full h-full flex items-center justify-center">
  <div className="relative w-64 h-64 rounded-full bg-primary-50 border-2 border-primary-200">
    <div className="absolute inset-8 rounded-full border border-primary-300" />
    <div className="absolute inset-16 rounded-full bg-primary-100" />
    <div className="absolute inset-x-8 top-1/2 h-1 -translate-y-1/2 rounded-full bg-accent-500/80 shadow-[0_0_16px_4px_rgba(201,134,42,0.3)] animate-scan-sweep" />
  </div>
</div>
            <div className="absolute inset-x-8 top-1/2 h-1 -translate-y-1/2 rounded-full bg-accent-500/80 shadow-[0_0_16px_4px_rgba(201,134,42,0.3)] animate-scan-sweep" />
            <div className="absolute -bottom-5 right-0 sm:right-3 w-52 rounded-md border border-earth-200 bg-white shadow-soft p-3">
              <p className="text-[10px] font-medium text-earth-500 mb-1">{t("landing_example_badge")}</p>
              <p className="text-sm font-semibold text-earth-900">Tomato · Early Blight</p>
              <div className="mt-1.5 flex items-center gap-2">
                <div className="h-1.5 flex-1 rounded-full bg-earth-100 overflow-hidden">
                  <div className="h-full bg-accent-500" style={{ width: "92%" }} />
                </div>
                <span className="text-xs font-semibold text-accent-600">92%</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 md:px-8 pb-20">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-10 md:grid-cols-3 md:gap-8">
            {steps.map((step, i) => (
              <div key={step.title} className="relative pl-14 md:pl-0">
                <span className="absolute left-0 top-0 md:static md:block text-2xl font-semibold text-primary-300 md:mb-3">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="font-semibold text-earth-900 mb-1.5">{step.title}</h3>
                <p className="text-sm text-earth-600 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-earth-200 text-earth-500 text-center py-6 text-xs px-4">
        GreenMind — Built for sustainable agriculture. AI guidance is informational, not a substitute for expert advice.
      </footer>
    </div>
  );
};

export default Landing;
