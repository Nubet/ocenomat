import Image from "next/image";

export function Brand() {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span className="relative size-10 shrink-0">
        <Image className="brand-logo-light" src="/logo-light.svg" alt="" fill sizes="40px" />
        <Image className="brand-logo-dark" src="/logo-dark.svg" alt="" fill sizes="40px" />
      </span>
      <span className="text-xl font-bold tracking-tight">
        Oceno<span className="text-primary">Mat</span>
      </span>
    </span>
  );
}
