"use client";

import Image from "next/image";
import { useState } from "react";

const FALLBACK = "/images/placeholder.svg";

type Props = {
  src: string;
  alt: string;
  size: number;
  className?: string;
  sizes?: string;
  eager?: boolean;
};

/** Product photo with a local fallback when the file is missing or fails to load. */
export default function ProductImage({ src, alt, size, className, sizes, eager }: Props) {
  const [failed, setFailed] = useState(!src);
  return (
    <Image
      src={failed ? FALLBACK : src}
      alt={alt}
      width={size}
      height={size}
      sizes={sizes ?? `${size}px`}
      className={className}
      unoptimized={failed} // the SVG fallback is served as-is
      loading={eager ? "eager" : "lazy"}
      fetchPriority={eager ? "high" : "auto"}
      onError={() => setFailed(true)}
    />
  );
}
