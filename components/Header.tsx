"use client";

export default function Header() {
  return (
    <header className="bg-meridian-600 text-white px-6 py-4 shadow-md flex items-center gap-3 shrink-0">
      <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center font-bold text-xl">
        M
      </div>
      <div>
        <h1 className="text-lg font-semibold leading-tight">
          Meridian Electronics
        </h1>
        <p className="text-sm text-meridian-200 leading-tight">
          Customer Support
        </p>
      </div>
    </header>
  );
}
