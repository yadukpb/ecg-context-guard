/**
 * AES-GCM decrypt for the simulated secure transmission channel from services/detector.
 *
 * Must stay byte-compatible with services/detector/app/crypto_channel.py:
 *   blob = base64(nonce) + "." + base64(ciphertext || 16-byte tag)
 *   key  = SHA-256(TRANSPORT_SECRET)  (32 bytes -> AES-256-GCM)
 *
 * Node's GCM implementation accepts a nonce of any length (not just the common 12 bytes),
 * same as pycryptodome's default — so no nonce-length negotiation is needed between the two
 * languages.
 */
import crypto from "node:crypto";
import { env } from "../config/env.js";

const KEY = crypto.createHash("sha256").update(env.transportSecret).digest();

export function decryptBlob(blob) {
  const [nonceB64, bodyB64] = blob.split(".");
  const nonce = Buffer.from(nonceB64, "base64");
  const body = Buffer.from(bodyB64, "base64");
  const tag = body.subarray(body.length - 16);
  const ciphertext = body.subarray(0, body.length - 16);

  const decipher = crypto.createDecipheriv("aes-256-gcm", KEY, nonce);
  decipher.setAuthTag(tag);
  const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  return JSON.parse(plaintext.toString("utf8"));
}
