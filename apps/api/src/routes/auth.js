import { Router } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { User } from "../models/User.js";
import { env } from "../config/env.js";
import { requireAuth } from "../middleware/auth.js";

export const authRouter = Router();

// In production the frontend (Vercel) and API (Render) are on different domains, so the
// cookie must be sameSite=none + secure to survive a cross-site request at all; in local dev
// both run on http://localhost, where sameSite=none without secure is rejected by browsers,
// so dev stays on the lax/non-secure pair.
const isProd = process.env.NODE_ENV === "production";
const COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: isProd ? "none" : "lax",
  secure: isProd,
  maxAge: 7 * 24 * 60 * 60 * 1000,
};

function signToken(user) {
  return jwt.sign({ sub: user._id.toString(), email: user.email, name: user.name }, env.jwtSecret, {
    expiresIn: "7d",
  });
}

authRouter.post("/register", async (req, res, next) => {
  try {
    const { email, password, name } = req.body;
    if (!email || !password || !name) {
      return res.status(400).json({ error: "email, password, and name are required" });
    }
    const existing = await User.findOne({ email: email.toLowerCase() });
    if (existing) return res.status(409).json({ error: "An account with this email already exists" });

    const passwordHash = await bcrypt.hash(password, 10);
    const user = await User.create({ email, passwordHash, name });
    const token = signToken(user);
    res.cookie("token", token, COOKIE_OPTIONS);
    res.status(201).json({ user: { id: user._id, email: user.email, name: user.name } });
  } catch (err) {
    next(err);
  }
});

authRouter.post("/login", async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email: (email || "").toLowerCase() });
    if (!user) return res.status(401).json({ error: "Invalid email or password" });

    const valid = await bcrypt.compare(password || "", user.passwordHash);
    if (!valid) return res.status(401).json({ error: "Invalid email or password" });

    const token = signToken(user);
    res.cookie("token", token, COOKIE_OPTIONS);
    res.json({ user: { id: user._id, email: user.email, name: user.name } });
  } catch (err) {
    next(err);
  }
});

authRouter.post("/logout", (req, res) => {
  res.clearCookie("token", COOKIE_OPTIONS);
  res.json({ ok: true });
});

authRouter.get("/me", requireAuth, (req, res) => {
  res.json({ user: { id: req.user.sub, email: req.user.email, name: req.user.name } });
});
