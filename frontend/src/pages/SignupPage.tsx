import { useState } from "react";

export function SignupPage() {
    const [formData, setFormData] = useState({
        display_name: "",
        email: "",
        password: "",
        confirmPassword: "",
    });
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");

        // Validate passwords match
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        // Validate password strength (min 8 chars, uppercase, digit)
        const passwordRegex = /^(?=.*[A-Z])(?=.*\d).{8,}$/;
        if (!passwordRegex.test(formData.password)) {
            setError("Password must be at least 8 characters with uppercase letter and digit");
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('http://localhost:5000/api/v1/auth/register', {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password,
                    display_name: formData.display_name || undefined
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess("✓ Account created successfully! Redirecting to login...");
                setFormData({ display_name: "", email: "", password: "", confirmPassword: "" });
                // Redirect to login after 2 seconds
                setTimeout(() => window.location.href = "/login", 2000);
            } else {
                setError(data.error || data.message || "Signup failed");
            }
        } catch (err) {
            setError("Network error. Please check your connection and try again.");
            console.error("Signup error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-base p-4">
            <form onSubmit={handleSubmit} className="w-full max-w-md bg-card rounded-lg p-6 shadow-md">
                <h2 className="text-2xl font-bold mb-6 text-center">Create an Account</h2>
                
                <input
                    type="text"
                    name="display_name"
                    placeholder="Display Name (optional)"
                    value={formData.display_name}
                    onChange={handleChange}
                    className="w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                
                <input
                    type="email"
                    name="email"
                    placeholder="Email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                
                <input
                    type="password"
                    name="password"
                    placeholder="Password (min 8 chars, uppercase, digit)"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className="w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                
                <input
                    type="password"
                    name="confirmPassword"
                    placeholder="Confirm Password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    className="w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                
                <button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-accent text-white py-2 rounded-lg hover:bg-accent-dark transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? "Creating account..." : "Sign Up"}
                </button>
                
                {error && <p className="mt-4 text-center text-red-500">{error}</p>}
                {success && <p className="mt-4 text-center text-green-500">{success}</p>}
            </form>
        </div>
    );
}
