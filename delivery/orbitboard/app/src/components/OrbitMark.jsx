function OrbitMark() {
  return (
    <svg
      aria-hidden="true"
      className="orbit-mark"
      fill="none"
      viewBox="0 0 40 40"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="1" y="1" width="38" height="38" rx="12" fill="currentColor" />
      <ellipse
        cx="20"
        cy="20"
        rx="12.5"
        ry="6.5"
        stroke="#e28a76"
        strokeWidth="1.7"
        transform="rotate(-36 20 20)"
      />
      <ellipse
        cx="20"
        cy="20"
        rx="7"
        ry="13"
        stroke="#f3e7d4"
        strokeOpacity=".8"
        strokeWidth="1.2"
        transform="rotate(42 20 20)"
      />
      <circle cx="20" cy="20" r="3" fill="#e28a76" />
      <circle cx="30.5" cy="10.5" r="2.4" fill="#d17160" />
    </svg>
  );
}

export default OrbitMark;
