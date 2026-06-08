import React, { useState } from "react";
import Header from "../Header/Header";
import person from "../assets/person.png";
import emailIcon from "../assets/email.png";
import passwordIcon from "../assets/password.png";
import "./Register.css";

const Register = () => {
  const [userName, setUserName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const register = async (event) => {
    event.preventDefault();
    const res = await fetch(window.location.origin + "/djangoapp/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userName,
        firstName,
        lastName,
        email,
        password,
      }),
    });
    const json = await res.json();
    if (json.status === "Registered" || json.status === "Updated") {
      sessionStorage.setItem("username", userName);
      sessionStorage.setItem("firstname", firstName);
      sessionStorage.setItem("lastname", lastName);
      window.location.href = "/";
    } else {
      alert("The user could not be registered.");
    }
  };

  return (
    <div>
      <Header />
      <form className="register_container" onSubmit={register}>
        <div className="header">Sign-up</div>
        <div className="inputs">
          <div className="input">
            <img src={person} className="img_icon" alt="Username" />
            <input className="input_field" type="text" name="username" placeholder="Username" onChange={(e) => setUserName(e.target.value)} />
          </div>
          <div className="input">
            <img src={person} className="img_icon" alt="First Name" />
            <input className="input_field" type="text" name="first_name" placeholder="First Name" onChange={(e) => setFirstName(e.target.value)} />
          </div>
          <div className="input">
            <img src={person} className="img_icon" alt="Last Name" />
            <input className="input_field" type="text" name="last_name" placeholder="Last Name" onChange={(e) => setLastName(e.target.value)} />
          </div>
          <div className="input">
            <img src={emailIcon} className="img_icon" alt="Email" />
            <input className="input_field" type="email" name="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="input">
            <img src={passwordIcon} className="img_icon" alt="Password" />
            <input className="input_field" type="password" name="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
          </div>
        </div>
        <div className="submit_panel">
          <button className="submit" type="submit">Register</button>
        </div>
      </form>
    </div>
  );
};

export default Register;
