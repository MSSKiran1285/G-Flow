/** App mark — the real logo asset (public/gflow-mark.png), black line art on a
 * transparent background. Inverted to white on dark theme via the .app-logo CSS rule
 * rather than keeping two raster files. public/favicon.png is the boxed (white
 * backdrop) variant used for the browser tab, which doesn't need theme-awareness. */
export function GFlowLogo({ size = 24 }: { size?: number }) {
  return (
    <img
      src="/gflow-mark.png"
      alt=""
      aria-hidden="true"
      className="app-logo"
      width={size}
      height={size}
      style={{ flexShrink: 0, objectFit: "contain" }}
    />
  );
}
