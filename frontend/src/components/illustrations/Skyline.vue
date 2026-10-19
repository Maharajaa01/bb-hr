<!-- Original flat illustration: Chennai-style skyline (gopuram, Central-station clock tower, high-rises, Marina sea). -->
<template>
	<svg viewBox="0 0 480 180" preserveAspectRatio="xMidYMax slice" class="block h-full w-full" role="img" aria-label="Chennai city skyline">
		<defs>
			<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0" stop-color="#7CC4FF" />
				<stop offset="1" stop-color="#D9EEFF" />
			</linearGradient>
		</defs>
		<rect width="480" height="180" fill="url(#sky)" />
		<circle cx="392" cy="46" r="22" fill="#FFD27A" />
		<g fill="#fff" opacity=".85">
			<ellipse cx="90" cy="38" rx="26" ry="9" /><ellipse cx="112" cy="33" rx="18" ry="9" />
			<ellipse cx="300" cy="28" rx="22" ry="7" /><ellipse cx="318" cy="24" rx="14" ry="7" />
		</g>
		<!-- far high-rises -->
		<g fill="#A9D3FB">
			<rect x="20" y="78" width="26" height="80" /><rect x="50" y="64" width="20" height="94" />
			<rect x="250" y="70" width="24" height="88" /><rect x="420" y="74" width="30" height="84" />
			<rect x="452" y="90" width="24" height="68" />
		</g>
		<!-- gopuram -->
		<g>
			<polygon points="96,158 104,92 148,92 156,158" fill="#F2A23A" />
			<polygon points="104,92 110,72 142,72 148,92" fill="#F6B860" />
			<polygon points="110,72 115,58 137,58 142,72" fill="#F2A23A" />
			<rect x="114" y="50" width="24" height="8" rx="3" fill="#E08A1E" />
			<g fill="#E08A1E" opacity=".7"><rect x="112" y="100" width="6" height="8" /><rect x="123" y="100" width="6" height="8" /><rect x="134" y="100" width="6" height="8" /><rect x="116" y="78" width="5" height="7" /><rect x="131" y="78" width="5" height="7" /></g>
			<path d="M118 158v-22a8 8 0 0 1 16 0v22z" fill="#C46F12" />
		</g>
		<!-- central station with clock tower -->
		<g>
			<rect x="176" y="112" width="96" height="46" fill="#E25B4B" />
			<rect x="208" y="70" width="32" height="88" fill="#D94C3D" />
			<polygon points="204,70 224,48 244,70" fill="#B9151B" />
			<circle cx="224" cy="84" r="8" fill="#fff" /><path d="M224 79v5l3 2" stroke="#212121" stroke-width="1.5" fill="none" stroke-linecap="round" />
			<g fill="#fff" opacity=".8"><rect x="184" y="122" width="8" height="12" rx="4" /><rect x="198" y="122" width="8" height="12" rx="4" /><rect x="244" y="122" width="8" height="12" rx="4" /><rect x="258" y="122" width="8" height="12" rx="4" /></g>
		</g>
		<!-- near high-rises -->
		<g>
			<rect x="292" y="84" width="40" height="74" fill="#048EFF" />
			<rect x="336" y="100" width="34" height="58" fill="#36A2FF" />
			<rect x="374" y="88" width="30" height="70" fill="#0277D6" />
			<g fill="#D3EAFF" opacity=".9">
				<rect x="298" y="92" width="8" height="6" /><rect x="312" y="92" width="8" height="6" /><rect x="298" y="104" width="8" height="6" /><rect x="312" y="104" width="8" height="6" /><rect x="298" y="116" width="8" height="6" /><rect x="312" y="116" width="8" height="6" />
				<rect x="342" y="108" width="8" height="6" /><rect x="356" y="108" width="8" height="6" /><rect x="342" y="120" width="8" height="6" /><rect x="356" y="120" width="8" height="6" />
				<rect x="380" y="96" width="6" height="6" /><rect x="392" y="96" width="6" height="6" /><rect x="380" y="108" width="6" height="6" /><rect x="392" y="108" width="6" height="6" />
			</g>
		</g>
		<!-- palms -->
		<g stroke="#2E9E5B" stroke-width="3" stroke-linecap="round" fill="none">
			<path d="M64 158c2-18 4-28 8-38" stroke="#8A5A2B" /><path d="M72 120c-8-6-18-6-24 0M72 120c6-8 16-10 24-6M72 120c-2-8 2-16 8-20M72 120c-10 0-16 6-18 12" />
			<path d="M420 158c-2-16-4-26-8-34" stroke="#8A5A2B" /><path d="M412 124c8-6 18-6 24 0M412 124c-6-8-16-10-24-6M412 124c2-8-2-16-8-20" />
		</g>
		<!-- marina -->
		<rect y="156" width="480" height="24" fill="#048EFF" />
		<path d="M0 162c20 0 20 4 40 4s20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4" stroke="#A8D5FF" stroke-width="2" fill="none" />
		<path d="M0 172c20 0 20 4 40 4s20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4 20 4 40 4 20-4 40-4" stroke="#6DBAFF" stroke-width="2" fill="none" />
	</svg>
</template>
