import { useState } from "react";

export function SignupPage() {
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
    });
    const [error, setError] = useState("");

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    }
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:5000/api/v1/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
        });
        const data = await response.json();
        setError(data.message||"Signup successful!");
        }
        catch (err) {
            setError("Signup failed. Please try again.");
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-base p-4">
            <form onSubmit={handleSubmit} className="w-full max-w-md bg-card rounded-lg p-6 shadow-md">
                <h2 className="text-2xl font-bold mb-6 text-center">Create an Account</h2>
                <input
                    type="text"
                    name="username"
                    placeholder="Username"
                    onChange={handleChange}
                    className= "w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <input
                    type = "email"
                    name = "email"
                    placeholder="Email"
                    onChange={handleChange}
                    className= "w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <input
                    type = "password"
                    name = "password"
                    placeholder="Password"
                    onChange={handleChange}
                    className= "w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <input
                    type = "password"
                    name = "confirmPassword"
                    placeholder="Confirm Password"
                    onChange={handleChange}
                    className= "w-full mb-4 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <button type="submit" className="w-full bg-accent text-white py-2 rounded-lg hover:bg-accent-dark transition-colors duration-200">Sign Up</button>
                {error && <p className="mt-4 text-center text-red-500">{error}</p>}
            </form>
        </div>
    );
}
