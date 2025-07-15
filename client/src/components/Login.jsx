import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api/axios";

const Login = () => {
    const [form, setForm] = useState({ email: "", password: "" });
//  const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();


    const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
        const res = await API.post("/login", form);
        localStorage.setItem("token", res.data.access_token);
        navigate("/"); // go to homepage
        } catch (err) {
        setError(err.response?.data?.detail || "Login failed.");
        }
    };

    return (
        <form onSubmit={handleSubmit}>
        <h2>Log In</h2>
        <input name="email" type="email" placeholder="Email" onChange={handleChange} required />
        <input name="password" type="password" placeholder="Password" onChange={handleChange} required />
        <button type="submit">Login</button>
        {error && <p>{error}</p>}
        </form>
    );
};

export default Login;
