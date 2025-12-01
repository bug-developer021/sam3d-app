"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  Compass,
  LayoutGrid,
  ShieldCheck,
  Sparkles,
  Timer,
  Zap,
  Box,
  Layers
} from "lucide-react";
import UploadZone from "../components/UploadZone";
import Gallery from "../components/Gallery";

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadComplete = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <main className="relative min-h-screen bg-ink text-slate-200 selection:bg-violet-500/30">
      {/* Navigation / Header */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-ink/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500" />
            <span className="text-lg font-medium tracking-tight text-white">Forma3D</span>
          </div>
          <div className="flex items-center gap-6 text-sm font-medium text-slate-400">
            <a href="#upload" className="hover:text-white transition-colors">Create</a>
            <a href="#gallery" className="hover:text-white transition-colors">Gallery</a>
            <a href="https://github.com/facebookresearch/sam-3d-objects" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">GitHub</a>
          </div>
        </div>
      </nav>

      <div className="relative mx-auto max-w-7xl px-6 pt-32 pb-20 lg:px-8">
        {/* Hero Section */}
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-200">
            <Sparkles className="h-3 w-3" />
            <span>v1.0 Now Available</span>
          </div>
          <h1 className="text-5xl font-medium tracking-tight text-white sm:text-7xl">
            Turn photos into <br />
            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-white bg-clip-text text-transparent">
              production assets.
            </span>
          </h1>
          <p className="mt-8 text-lg leading-8 text-slate-400 font-light">
            Forma3D transforms your multi-view photos into clean, watertight 3D meshes. 
            Ready for rendering, gaming, or printing. No manual cleanup required.
          </p>
          
          <div className="mt-10 flex items-center justify-center gap-4">
            <a
              href="#upload"
              className="group flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition hover:bg-slate-200"
            >
              Start Creating
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </a>
            <a
              href="#gallery"
              className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              View Gallery
            </a>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid gap-8 sm:grid-cols-3">
          {[
            {
              icon: Layers,
              title: "Multi-view Fusion",
              desc: "Intelligently blends up to 20 angles for complete coverage.",
            },
            {
              icon: Box,
              title: "Clean Topology",
              desc: "Watertight meshes ready for physics and collision.",
            },
            {
              icon: Zap,
              title: "GPU Accelerated",
              desc: "Fast processing pipeline optimized for high throughput.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="group relative overflow-hidden rounded-3xl border border-white/5 bg-white/[0.02] p-8 transition hover:border-white/10 hover:bg-white/[0.04]"
            >
              <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400 group-hover:text-violet-300 transition-colors">
                <item.icon className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-medium text-white">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                {item.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Upload Section */}
        <section id="upload" className="mt-32 scroll-mt-24">
          <div className="mb-10 flex items-end justify-between">
            <div>
              <h2 className="text-3xl font-medium text-white">Create New Asset</h2>
              <p className="mt-2 text-slate-400">Upload your reference images to begin.</p>
            </div>
          </div>
          
          <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
            <UploadZone onUploadComplete={handleUploadComplete} />
            
            <div className="space-y-6">
              <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-6">
                <h3 className="flex items-center gap-2 text-sm font-medium text-white">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  Best Practices
                </h3>
                <ul className="mt-4 space-y-3 text-sm text-slate-400">
                  <li className="flex gap-2">
                    <span className="text-violet-400">•</span>
                    Use 3-8 angles around the object
                  </li>
                  <li className="flex gap-2">
                    <span className="text-violet-400">•</span>
                    Ensure consistent lighting
                  </li>
                  <li className="flex gap-2">
                    <span className="text-violet-400">•</span>
                    Avoid blurry or out-of-focus shots
                  </li>
                  <li className="flex gap-2">
                    <span className="text-violet-400">•</span>
                    Neutral background works best
                  </li>
                </ul>
              </div>

              <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-6">
                <h3 className="flex items-center gap-2 text-sm font-medium text-white">
                  <LayoutGrid className="h-4 w-4 text-violet-400" />
                  Output Formats
                </h3>
                <div className="mt-4 flex flex-wrap gap-2">
                  {['OBJ', 'STL', 'GLB', 'GLTF'].map(fmt => (
                    <span key={fmt} className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-medium text-slate-300">
                      {fmt}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Gallery Section */}
        <section id="gallery" className="mt-32 scroll-mt-24">
          <div className="mb-10">
            <h2 className="text-3xl font-medium text-white">Recent Generations</h2>
            <p className="mt-2 text-slate-400">Browse the latest assets created by the community.</p>
          </div>
          <Gallery refreshTrigger={refreshTrigger} />
        </section>
      </div>
      
      <footer className="border-t border-white/5 bg-black/20 py-12">
        <div className="mx-auto max-w-7xl px-6 text-center text-sm text-slate-500">
          <p>&copy; 2025 Forma3D. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
}
