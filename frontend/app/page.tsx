"use client";
import { useState } from "react";
export default function Home() {
  const [status, setStatus] = useState("Ready");
  return <main style={{fontFamily:"Arial",maxWidth:800,margin:"80px auto",padding:24}}><h1>ParcelWalaa</h1><p>Multi-service delivery platform</p><button onClick={async()=>{const r=await fetch("http://localhost:8000/health");setStatus((await r.json()).status)}}>Check API</button><p>API status: {status}</p></main>;
}
