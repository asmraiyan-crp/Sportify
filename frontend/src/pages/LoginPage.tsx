import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../utils/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(formData);
      // Reload page to trigger auth check in App
      window.location.href = "/home";
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-9">
          <h1 className="font-display text-[48px] tracking-widest text-gradient-logo mb-2">
            ⚡ SPORTIFY
          </h1>
          <p className="text-t3 text-[13px] font-body">Sign in to your account</p>
        </div>

        {/* Card */}
        <div className="bg-card border border-border rounded-card p-8">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {/* Email */}
            <div>
              <label className="text-[12px] font-semibold text-t2 uppercase tracking-wide font-heading mb-2 block">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
                required
                className="w-full px-4 py-2.5 bg-base border border-border rounded-lg text-[13px] font-body text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            {/* Password */}
            <div>
              <label className="text-[12px] font-semibold text-t2 uppercase tracking-wide font-heading mb-2 block">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                required
                className="w-full px-4 py-2.5 bg-base border border-border rounded-lg text-[13px] font-body text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="px-4 py-3 rounded-lg bg-live/10 border border-live/30 text-live text-[13px] font-body">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-btn text-[13px] font-semibold bg-accent text-white border-none cursor-pointer font-heading tracking-wide transition-all duration-200 hover:bg-accent-light active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {/* Links */}
          <div className="flex items-center justify-between mt-6 pt-6 border-t border-border">
            <a href="#" className="text-[12px] text-t3 hover:text-accent-light transition-colors">
              Forgot password?
            </a>
            <button
              onClick={() => navigate("/signup")}
              className="text-[12px] text-accent-light hover:text-accent transition-colors bg-transparent border-none cursor-pointer"
            >
              Create account →
            </button>
          </div>
        </div>

        {/* Footer text */}
        <p className="text-center text-t3 text-[11px] mt-8">
          Football • Cricket • Real-time Stats • Live Community
        </p>
      </div>
    </div>
  );
}
