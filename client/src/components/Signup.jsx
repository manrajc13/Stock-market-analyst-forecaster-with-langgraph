import React, {useState} from "react";
import API from "../api/axios";

const Signup = () => {
    const [form, setForm] = useState({email: "", name: "", password: ""});
    const [message, setMessage] = useState("");

    const handleChnage = (e) => {
        setForm({...form, [e.target.name]: e.target.value});
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try{
            const res = await API.post("/register", form);
            setMessage("Signup successful! Please log in.");
        } catch(err){
            setMessage(err.response?.data?.detail || "Signup failed.")
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h2>Sign Up</h2>
            <input type="email" name="email" placeholder="email" onChange={handleChnage} required/>
            <input type="text" name="name" placeholder="name" onChange={handleChnage} required />
            <input type="password" name="password" placeholder="Password" onChange={handleSubmit} required/>
            <button type="submit">Register</button>
            <p>{message}</p>
        </form>
    );
};

export default Signup

