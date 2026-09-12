import React from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";

const Landing: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div>
      <section className="bg-gradient-to-b from-primary-100 to-primary-50 py-20 px-6 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-primary-700 mb-4">
          {t("landing_hero_title")}
        </h1>
        <p className="text-lg text-gray-700 max-w-2xl mx-auto mb-8">
          {t("landing_hero_subtitle")}
        </p>
        <Link
          to="/register"
          className="bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition"
        >
          {t("landing_cta")}
        </Link>
      </section>

      <section className="py-16 px-6 max-w-5xl mx-auto grid md:grid-cols-3 gap-8">
        {[
          { title: "AI Disease Detection", desc: "Upload a leaf photo for instant, transparently-labeled AI analysis." },
          { title: "Practical Recommendations", desc: "Treatment, fertilizer, and pesticide guidance tailored to the diagnosis." },
          { title: "Weather-Aware Advice", desc: "Live weather data informs crop management and timing decisions." },
          { title: "GreenMind Assistant", desc: "Ask follow-up questions about symptoms, care, and prevention." },
          { title: "Multilingual", desc: "Available in English, Telugu, and Hindi." },
          { title: "Full History & Reports", desc: "Track every diagnosis and download a shareable PDF report." },
        ].map((f) => (
          <div key={f.title} className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-primary-700 mb-2">{f.title}</h3>
            <p className="text-sm text-gray-600">{f.desc}</p>
          </div>
        ))}
      </section>

      <footer className="bg-primary-700 text-primary-100 text-center py-6 text-sm">
        GreenMind — Built for sustainable agriculture. AI guidance is informational, not a substitute for expert advice.
      </footer>
    </div>
  );
};

export default Landing;
